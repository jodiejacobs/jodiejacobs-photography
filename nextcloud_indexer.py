#!/usr/bin/env python3
"""
NextCloud Photography Portfolio Indexer

This script scans your NextCloud photos, extracts metadata, and generates
a photos.json file for your photography portfolio website.

Requirements:
pip install pillow exifread requests webdav4

Usage:
1. Configure the settings below
2. Run: python nextcloud_indexer.py
3. Upload the generated photos.json to your GitHub repo
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    import exifread
    from webdav4.client import Client
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install pillow exifread webdav4")
    exit(1)

# Configuration - Update these for your setup
CONFIG = {
    # NextCloud WebDAV settings
    'nextcloud_url': 'https://your-nextcloud-domain.com/remote.php/dav/files/username/',
    'username': 'your-username',
    'password': 'your-app-password',  # Use app password, not main password
    
    # Photo directories in NextCloud
    'photo_directories': {
        'faces': 'Photos/Portfolio/Faces',
        'street': 'Photos/Portfolio/Street', 
        'nature': 'Photos/Portfolio/Nature'
    },
    
    # Public share URLs for each category (create these in NextCloud)
    'public_shares': {
        'faces': 'https://your-nextcloud-domain.com/s/SHARE_TOKEN_FACES',
        'street': 'https://your-nextcloud-domain.com/s/SHARE_TOKEN_STREET',
        'nature': 'https://your-nextcloud-domain.com/s/SHARE_TOKEN_NATURE'
    },
    
    # Output settings
    'output_file': 'photos.json',
    'max_photos_per_category': 500,  # Limit to prevent huge JSON files
    'supported_formats': ['.jpg', '.jpeg', '.png', '.webp'],
    
    # Thumbnail settings (if generating locally)
    'create_thumbnails': False,  # Set to True if you want local thumbnails
    'thumbnail_size': (400, 300),
    'thumbnail_dir': 'thumbnails'
}

class NextCloudPhotoIndexer:
    def __init__(self):
        self.client = None
        self.photos = []
        
    def connect_to_nextcloud(self) -> bool:
        """Connect to NextCloud via WebDAV"""
        try:
            self.client = Client(
                CONFIG['nextcloud_url'],
                auth=(CONFIG['username'], CONFIG['password'])
            )
            # Test connection
            self.client.ls('/')
            print("✅ Connected to NextCloud")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to NextCloud: {e}")
            print("Make sure to use an app password, not your main password")
            return False
    
    def extract_gps_from_exif(self, exif_data) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from EXIF data"""
        try:
            if 'GPS GPSLatitude' in exif_data and 'GPS GPSLongitude' in exif_data:
                lat_ref = str(exif_data.get('GPS GPSLatitudeRef', 'N'))
                lat_vals = exif_data['GPS GPSLatitude'].values
                
                lng_ref = str(exif_data.get('GPS GPSLongitudeRef', 'E'))
                lng_vals = exif_data['GPS GPSLongitude'].values
                
                # Convert to decimal degrees
                lat = float(lat_vals[0]) + float(lat_vals[1])/60 + float(lat_vals[2])/3600
                lng = float(lng_vals[0]) + float(lng_vals[1])/60 + float(lng_vals[2])/3600
                
                if lat_ref == 'S':
                    lat = -lat
                if lng_ref == 'W':
                    lng = -lng
                    
                return lat, lng
        except:
            pass
        return None
    
    def extract_photo_metadata(self, file_path: str, category: str) -> Optional[Dict]:
        """Extract metadata from a photo file"""
        try:
            # Download file temporarily to read EXIF
            temp_file = f"/tmp/{os.path.basename(file_path)}"
            self.client.download_file(file_path, temp_file)
            
            # Extract EXIF data
            exif_data = {}
            date_taken = None
            gps_coords = None
            
            with open(temp_file, 'rb') as f:
                tags = exifread.process_file(f)
                exif_data = {str(k): str(v) for k, v in tags.items()}
                
                # Extract date
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    try:
                        date_taken = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Extract GPS
                gps_coords = self.extract_gps_from_exif(tags)
            
            # Clean up temp file
            os.remove(temp_file)
            
            # Generate URLs
            filename = os.path.basename(file_path)
            base_share_url = CONFIG['public_shares'].get(category, '')
            
            if not base_share_url:
                print(f"⚠️  No public share URL configured for category: {category}")
                return None
            
            # Construct public URLs
            thumbnail_url = f"{base_share_url}/download/{filename}"
            full_url = f"{base_share_url}/download/{filename}"
            
            # Extract location from GPS or use default
            location = "Unknown"
            if gps_coords:
                # You could use reverse geocoding here with a service like Nominatim
                location = f"{gps_coords[0]:.4f}, {gps_coords[1]:.4f}"
            
            return {
                'id': len(self.photos) + 1,
                'title': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
                'category': category,
                'thumbnail': thumbnail_url,
                'full': full_url,
                'lat': gps_coords[0] if gps_coords else None,
                'lng': gps_coords[1] if gps_coords else None,
                'location': location,
                'date': date_taken or 'Unknown',
                'filename': filename
            }
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return None
    
    def scan_directory(self, directory: str, category: str) -> List[Dict]:
        """Scan a directory for photos"""
        photos = []
        try:
            print(f"📁 Scanning {directory} for {category} photos...")
            
            files = self.client.ls(directory)
            photo_files = [
                f for f in files 
                if any(f.lower().endswith(ext) for ext in CONFIG['supported_formats'])
            ]
            
            print(f"   Found {len(photo_files)} photos")
            
            # Limit photos per category
            photo_files = photo_files[:CONFIG['max_photos_per_category']]
            
            for i, file_path in enumerate(photo_files, 1):
                print(f"   Processing {i}/{len(photo_files)}: {os.path.basename(file_path)}")
                
                full_path = f"{directory}/{file_path}" if not directory.endswith('/') else f"{directory}{file_path}"
                metadata = self.extract_photo_metadata(full_path, category)
                
                if metadata:
                    photos.append(metadata)
                    
        except Exception as e:
            print(f"❌ Error scanning directory {directory}: {e}")
            
        return photos
    
    def generate_index(self):
        """Generate the complete photo index"""
        print("🔍 Generating photo index...")
        
        for category, directory in CONFIG['photo_directories'].items():
            category_photos = self.scan_directory(directory, category)
            self.photos.extend(category_photos)
            print(f"✅ Added {len(category_photos)} {category} photos")
        
        # Sort photos by date (newest first)
        self.photos.sort(key=lambda x: x['date'], reverse=True)
        
        print(f"📊 Total photos indexed: {len(self.photos)}")
        
        # Save to JSON
        with open(CONFIG['output_file'], 'w') as f:
            json.dump(self.photos, f, indent=2)
        
        print(f"💾 Saved index to {CONFIG['output_file']}")
        
        # Print summary
        categories = {}
        locations = set()
        for photo in self.photos:
            categories[photo['category']] = categories.get(photo['category'], 0) + 1
            if photo['location'] != 'Unknown':
                locations.add(photo['location'])
        
        print("\n📈 Summary:")
        for cat, count in categories.items():
            print(f"   {cat}: {count} photos")
        print(f"   Locations with GPS: {len(locations)}")

def main():
    print("🚀 NextCloud Photography Portfolio Indexer")
    print("=" * 50)
    
    # Validate configuration
    if not all([
        CONFIG['nextcloud_url'],
        CONFIG['username'], 
        CONFIG['password']
    ]):
        print("❌ Please configure your NextCloud credentials in CONFIG")
        return
    
    if not any(CONFIG['public_shares'].values()):
        print("⚠️  Warning: No public share URLs configured")
        print("   Create public shares in NextCloud for each photo category")
        print("   and update the 'public_shares' in CONFIG")
    
    # Initialize indexer
    indexer = NextCloudPhotoIndexer()
    
    # Connect to NextCloud
    if not indexer.connect_to_nextcloud():
        return
    
    # Generate the index
    indexer.generate_index()
    
    print("\n🎉 Index generation complete!")
    print(f"\nNext steps:")
    print(f"1. Upload {CONFIG['output_file']} to your GitHub repository")
    print(f"2. Update CONFIG.photosJsonUrl in your website to point to the JSON file")
    print(f"3. Add your Mapbox token to CONFIG.mapboxToken")
    print(f"4. Your photos will load from NextCloud public shares")

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "nextcloud_url": "https://your-nextcloud.com/remote.php/dav/files/username/",
        "username": "your-username",
        "password": "your-app-password",
        "photo_directories": {
            "faces": "Photos/Portfolio/Faces",
            "street": "Photos/Portfolio/Street",
            "nature": "Photos/Portfolio/Nature"
        },
        "public_shares": {
            "faces": "https://your-nextcloud.com/s/FACES_SHARE_TOKEN",
            "street": "https://your-nextcloud.com/s/STREET_SHARE_TOKEN", 
            "nature": "https://your-nextcloud.com/s/NATURE_SHARE_TOKEN"
        }
    }
    
    with open('nextcloud_config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("📝 Created nextcloud_config.json - update with your settings")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-config':
        create_sample_config()
    else:
        main()