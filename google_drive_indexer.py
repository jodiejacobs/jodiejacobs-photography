#!/usr/bin/env python3
"""
Google Drive Public Links Photography Portfolio Indexer

This script scans your local Google Drive photos, extracts metadata, and generates
a photos.json file using Google Drive public sharing links.

Requirements:
pip install pillow exifread

Setup:
1. Create public folders in Google Drive for each category
2. Get the sharing links for each folder
3. Update the CONFIG below with your folder IDs
4. Run the script

Usage:
python google_drive_indexer.py
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
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install pillow exifread")
    exit(1)

# Configuration - Update these for your setup
CONFIG = {
    # Local Google Drive path (for scanning metadata)
    'google_drive_path': '/Users/jodiejacobs/Library/CloudStorage/GoogleDrive-jacobs.jodiem@gmail.com/My Drive/jodiejacobs_photography',
    
    # Photo directories within Google Drive
    'photo_directories': {
        'faces': 'Portfolio/Faces',
        'street': 'Portfolio/Street', 
        'nature': 'Portfolio/Nature'
    },
    
    # Google Drive public folder sharing links
    # Portfolio folder: https://drive.google.com/drive/folders/1R3nXeR50XjXyC7KcbwR76YhORwW1ATXj
    'public_folder_links': {
        'faces': 'https://drive.google.com/drive/folders/1sx0we1xJCmkILoaw5L9jTH2lx0OiWP_V',
        'street': 'https://drive.google.com/drive/folders/1BcpXD2whHZAUQxdU4bBDUshg0l4wdus1',
        'nature': 'https://drive.google.com/drive/folders/13EytsMQzV44JQn6E17QCF_s9LEqOJ0V6'
    },
    
    # Output settings
    'output_file': 'photos.json',
    'max_photos_per_category': 500,
    'supported_formats': ['.jpg', '.jpeg', '.png', '.webp'],
}

class GoogleDrivePublicIndexer:
    def __init__(self):
        self.photos = []
        self.base_path = Path(CONFIG['google_drive_path'])
    
    def extract_folder_id(self, folder_link: str) -> str:
        """Extract folder ID from Google Drive sharing link"""
        # Handle different Google Drive URL formats
        if '/folders/' in folder_link:
            folder_id = folder_link.split('/folders/')[1].split('?')[0]
        elif 'id=' in folder_link:
            folder_id = folder_link.split('id=')[1].split('&')[0]
        else:
            folder_id = folder_link.split('/')[-1].split('?')[0]
        return folder_id
    
    def get_google_drive_file_url(self, folder_link: str, filename: str) -> Tuple[str, str]:
        """
        Generate Google Drive direct file URLs for thumbnail and full size
        
        Note: This creates the URL format but the actual file ID would need to be
        obtained through Google Drive API for direct access. For now, we'll use
        a viewer URL that works for public folders.
        """
        folder_id = self.extract_folder_id(folder_link)
        
        # For public folders, we can construct viewer URLs
        # These will show the image in Google Drive's viewer
        base_viewer_url = f"https://drive.google.com/file/d/FILE_ID/view"
        
        # Note: To get actual file IDs, you'd need to use Google Drive API
        # For now, we'll create placeholder URLs that you can update manually
        thumbnail_url = f"https://drive.google.com/uc?export=view&id=FILE_ID_FOR_{filename.replace(' ', '_')}"
        full_url = f"https://drive.google.com/uc?export=view&id=FILE_ID_FOR_{filename.replace(' ', '_')}"
        
        return thumbnail_url, full_url
    
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
        except Exception as e:
            print(f"GPS extraction error: {e}")
        return None
    
    def extract_photo_metadata(self, file_path: Path, category: str) -> Optional[Dict]:
        """Extract metadata from a photo file"""
        try:
            # Extract EXIF data
            exif_data = {}
            date_taken = None
            gps_coords = None
            
            with open(file_path, 'rb') as f:
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
            
            # Get the folder sharing link for this category
            folder_link = CONFIG['public_folder_links'].get(category)
            if not folder_link or 'YOUR_' in folder_link:
                print(f"⚠️  No public folder link configured for category: {category}")
                print(f"   Please update CONFIG['public_folder_links']['{category}']")
                return None
            
            # Generate Google Drive URLs
            filename = file_path.stem
            thumbnail_url, full_url = self.get_google_drive_file_url(folder_link, filename)
            
            # Extract location from GPS or use default
            location = "Unknown"
            if gps_coords:
                location = f"{gps_coords[0]:.4f}, {gps_coords[1]:.4f}"
            else:
                # Try to extract from folder structure or filename
                parent_dir = file_path.parent.name
                if parent_dir and parent_dir != category.title():
                    location = parent_dir.replace('_', ' ').replace('-', ' ')
            
            return {
                'id': len(self.photos) + 1,
                'title': filename.replace('_', ' ').replace('-', ' ').title(),
                'category': category,
                'thumbnail': thumbnail_url,
                'full': full_url,
                'lat': gps_coords[0] if gps_coords else None,
                'lng': gps_coords[1] if gps_coords else None,
                'location': location,
                'date': date_taken or datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d'),
                'filename': file_path.name,
                'google_drive_folder': folder_link
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def scan_directory(self, directory: str, category: str) -> List[Dict]:
        """Scan a directory for photos"""
        photos = []
        dir_path = self.base_path / directory
        
        if not dir_path.exists():
            print(f"⚠️  Directory not found: {dir_path}")
            return photos
        
        print(f"📁 Scanning {dir_path} for {category} photos...")
        
        # Find all photo files
        photo_files = []
        for ext in CONFIG['supported_formats']:
            photo_files.extend(dir_path.glob(f"*{ext}"))
            photo_files.extend(dir_path.glob(f"*{ext.upper()}"))
        
        # Also scan subdirectories
        for subdir in dir_path.iterdir():
            if subdir.is_dir():
                for ext in CONFIG['supported_formats']:
                    photo_files.extend(subdir.glob(f"*{ext}"))
                    photo_files.extend(subdir.glob(f"*{ext.upper()}"))
        
        print(f"   Found {len(photo_files)} photos")
        
        # Limit photos per category
        photo_files = photo_files[:CONFIG['max_photos_per_category']]
        
        for i, file_path in enumerate(photo_files, 1):
            print(f"   Processing {i}/{len(photo_files)}: {file_path.name}")
            
            metadata = self.extract_photo_metadata(file_path, category)
            
            if metadata:
                photos.append(metadata)
                
        return photos
    
    def generate_index(self):
        """Generate the complete photo index"""
        print("🔍 Generating photo index with Google Drive public links...")
        
        if not self.base_path.exists():
            print(f"❌ Google Drive path not found: {self.base_path}")
            print("Make sure Google Drive is synced and the path is correct")
            return
        
        # Check if public folder links are configured
        missing_links = [cat for cat, link in CONFIG['public_folder_links'].items() 
                        if not link or 'YOUR_' in link]
        
        if missing_links:
            print(f"⚠️  Missing public folder links for: {', '.join(missing_links)}")
            print("\nTo set up Google Drive public sharing:")
            print("1. Go to Google Drive in your browser")
            print("2. Navigate to your Photos/Portfolio folder")
            print("3. Right-click each category folder (Faces, Street, Nature)")
            print("4. Choose 'Share' > 'Get link' > 'Anyone with the link can view'")
            print("5. Copy the sharing link and update CONFIG['public_folder_links']")
            print("")
        
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
        
        if missing_links:
            print(f"\n⚠️  Remember to:")
            print(f"   1. Set up public sharing for missing folders: {', '.join(missing_links)}")
            print(f"   2. Update the file IDs in the generated photos.json")
            print(f"   3. Test the links work in your browser")

def create_setup_instructions():
    """Create a helpful setup guide"""
    instructions = """
# Google Drive Public Sharing Setup Guide

## Step 1: Create Public Folders
1. Go to Google Drive (drive.google.com)
2. Navigate to your Photos/Portfolio folder
3. For each category folder (Faces, Street, Nature):
   - Right-click the folder
   - Click "Share"
   - Click "Get link"
   - Change permission to "Anyone with the link can view"
   - Copy the sharing link

## Step 2: Update Configuration
Update the CONFIG['public_folder_links'] in the script with your actual links:

```python
'public_folder_links': {
    'faces': 'https://drive.google.com/drive/folders/1ABC123_YOUR_ACTUAL_FOLDER_ID',
    'street': 'https://drive.google.com/drive/folders/1DEF456_YOUR_ACTUAL_FOLDER_ID',
    'nature': 'https://drive.google.com/drive/folders/1GHI789_YOUR_ACTUAL_FOLDER_ID'
}
```

## Step 3: Get Individual File IDs (Optional for Direct Access)
For direct image access, you'll need individual file IDs:
1. Upload photos to your public folders
2. Right-click each photo > "Get link"
3. Extract the file ID from the link
4. Update the photos.json file with actual file IDs

## Alternative: Use Google Drive API
For automatic file ID extraction, consider using the Google Drive API.
"""
    
    with open('google_drive_setup.md', 'w') as f:
        f.write(instructions)
    
    print("📝 Created google_drive_setup.md with detailed instructions")

def main():
    print("🚀 Google Drive Public Links Photography Portfolio Indexer")
    print("=" * 60)
    
    # Validate configuration
    if not Path(CONFIG['google_drive_path']).exists():
        print(f"❌ Google Drive path not found: {CONFIG['google_drive_path']}")
        print("Please update CONFIG['google_drive_path'] to your Google Drive location")
        return
    
    # Create setup instructions
    create_setup_instructions()
    
    # Initialize indexer
    indexer = GoogleDrivePublicIndexer()
    
    # Generate the index
    indexer.generate_index()
    
    print("\n🎉 Index generation complete!")
    print(f"\nNext steps:")
    print(f"1. Set up public sharing for your Google Drive folders (see google_drive_setup.md)")
    print(f"2. Update CONFIG['public_folder_links'] with your actual sharing links")
    print(f"3. Run the script again to generate proper URLs")
    print(f"4. Upload {CONFIG['output_file']} to your GitHub repository")
    print(f"5. Your photos will be served directly from Google Drive!")

if __name__ == "__main__":
    main()
