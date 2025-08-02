#!/usr/bin/env python3
"""
Simple Photos Indexer (No Thumbnails)

This script processes photos from your local Photos directory and creates
web-optimized versions without separate thumbnails. The website will use
CSS to resize the same image for both thumbnail and full view.

Directory structure expected:
/Users/jodiejacobs/Nextcloud/jodiejacobs-photography/Photos/
├── Faces/
├── Street/
└── Nature/

Requirements:
pip install pillow exifread
"""

import json
import os
import shutil
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

# Configuration
CONFIG = {
    # Local photos directory (in your Nextcloud folder)
    'photos_source_dir': '/Users/jodiejacobs/Nextcloud/jodiejacobs-photography/Photos',
    
    # Photo directories within the Photos folder
    'photo_directories': {
        'faces': 'Faces',
        'street': 'Street', 
        'nature': 'Nature'
    },
    
    # Output settings
    'output_file': 'photos.json',
    'web_photos_dir': 'portfolio',  # Changed from 'photos' to avoid conflict with 'Photos'
    'max_photos_per_category': 500,
    'supported_formats': ['.jpg', '.jpeg', '.png', '.webp', '.heic'],
    
    # Single image optimization settings (no thumbnails)
    'max_size': (1200, 1200),  # Max dimensions for web
    'quality': 85,  # JPEG quality
}

class SimplePhotosIndexer:
    def __init__(self):
        self.photos = []
        self.source_path = Path(CONFIG['photos_source_dir'])
        
        # Create output directory for web-optimized photos (no thumbnails folder)
        self.web_photos_dir = Path(CONFIG['web_photos_dir'])
        self.web_photos_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def optimize_image(self, input_path: Path, output_path: Path) -> bool:
        """Optimize image for web (single size, no thumbnails)"""
        try:
            with Image.open(input_path) as img:
                # Handle HEIC files
                if input_path.suffix.lower() == '.heic':
                    pass
                
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Auto-rotate based on EXIF orientation
                try:
                    exif = img._getexif()
                    if exif is not None:
                        orientation = exif.get(274)
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                except:
                    pass
                
                # Resize if larger than max_size
                if img.size[0] > CONFIG['max_size'][0] or img.size[1] > CONFIG['max_size'][1]:
                    img.thumbnail(CONFIG['max_size'], Image.Resampling.LANCZOS)
                
                # Save optimized image as JPEG
                output_path = output_path.with_suffix('.jpg')
                img.save(output_path, 'JPEG', quality=CONFIG['quality'], optimize=True)
                return True
        except Exception as e:
            print(f"Image optimization error for {input_path}: {e}")
            return False
    
    def process_photo(self, file_path: Path, category: str) -> Optional[Dict]:
        """Process a single photo"""
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
                elif 'DateTime' in tags:
                    date_str = str(tags['DateTime'])
                    try:
                        date_taken = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Extract GPS
                gps_coords = self.extract_gps_from_exif(tags)
            
            # Generate web-friendly filename
            photo_id = len(self.photos) + 1
            original_name = file_path.stem
            safe_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            
            # Single optimized file (no separate thumbnail)
            filename = f"{category}_{photo_id:03d}_{safe_name}.jpg"
            
            # Create optimized image
            output_path = self.web_photos_dir / filename
            
            optimize_success = self.optimize_image(file_path, output_path)
            
            if not optimize_success:
                print(f"Failed to process {file_path.name}")
                return None
            
            # Generate URLs (same URL for both thumbnail and full)
            image_url = f"portfolio/{filename}"
            
            # Extract location
            location = "Unknown"
            if gps_coords:
                location = f"{gps_coords[0]:.4f}, {gps_coords[1]:.4f}"
            else:
                # Try to extract from folder structure
                parent_dir = file_path.parent.name
                if parent_dir and parent_dir.lower() != category.lower():
                    location = parent_dir.replace('_', ' ').replace('-', ' ')
            
            return {
                'id': photo_id,
                'title': original_name.replace('_', ' ').replace('-', ' ').title(),
                'category': category,
                'thumbnail': image_url,  # Same as full
                'full': image_url,       # Same as thumbnail
                'lat': gps_coords[0] if gps_coords else None,
                'lng': gps_coords[1] if gps_coords else None,
                'location': location,
                'date': date_taken or datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d'),
                'filename': filename,
                'original_file': file_path.name
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def scan_directory(self, directory: str, category: str) -> List[Dict]:
        """Scan directory and process photos"""
        photos = []
        dir_path = self.source_path / directory
        
        if not dir_path.exists():
            print(f"⚠️  Directory not found: {dir_path}")
            return photos
        
        print(f"📁 Processing {category} photos from {dir_path}")
        
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
        
        # Sort by modification time (newest first)
        photo_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Limit photos per category
        photo_files = photo_files[:CONFIG['max_photos_per_category']]
        print(f"   Found {len(photo_files)} photos to process")
        
        for i, file_path in enumerate(photo_files, 1):
            print(f"   Processing {i}/{len(photo_files)}: {file_path.name}")
            
            metadata = self.process_photo(file_path, category)
            if metadata:
                photos.append(metadata)
        
        return photos
    
    def generate_index(self):
        """Generate complete photo index"""
        print("🔍 Processing local photos (single size, no thumbnails)...")
        
        if not self.source_path.exists():
            print(f"❌ Photos directory not found: {self.source_path}")
            return
        
        # Clean existing web photos directory
        if self.web_photos_dir.exists():
            print("🧹 Cleaning existing web photos...")
            for file in self.web_photos_dir.glob("*.jpg"):
                file.unlink()
        else:
            print("📁 Creating web photos directory...")
        
        self.web_photos_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each category
        for category, directory in CONFIG['photo_directories'].items():
            category_photos = self.scan_directory(directory, category)
            self.photos.extend(category_photos)
            print(f"✅ Processed {len(category_photos)} {category} photos")
        
        # Sort by date (newest first)
        self.photos.sort(key=lambda x: x['date'], reverse=True)
        
        print(f"📊 Total photos processed: {len(self.photos)}")
        
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
        print(f"   Web photos directory: {self.web_photos_dir}")
        
        # Show file sizes
        total_size = sum(
            f.stat().st_size 
            for f in self.web_photos_dir.glob("*.jpg")
        )
        print(f"   Total optimized size: {total_size / (1024*1024):.1f} MB")

def main():
    print("🚀 Simple Photos Indexer (No Thumbnails)")
    print("=" * 45)
    
    # Initialize indexer
    indexer = SimplePhotosIndexer()
    
    # Generate the index
    indexer.generate_index()
    
    print("\n🎉 Photo processing complete!")
    print("\nNext steps:")
    print("1. Commit photos and index:")
    print("   git add photos/ photos.json")
    print("   git commit -m 'Add simplified photos (no thumbnails)'")
    print("   git push")
    print("\n2. Your photos use CSS sizing instead of separate thumbnails")
    print("3. This should be much more reliable!")

if __name__ == "__main__":
    main()