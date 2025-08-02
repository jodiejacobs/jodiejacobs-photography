#!/usr/bin/env python3
"""
Local Photos Indexer for GitHub LFS

This script processes photos from your local Nextcloud Photos directory
and prepares them for GitHub LFS hosting with automatic optimization.

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
    'web_photos_dir': 'photos',  # Directory for web-optimized photos
    'max_photos_per_category': 500,
    'supported_formats': ['.jpg', '.jpeg', '.png', '.webp', '.heic'],
    
    # Image optimization settings
    'create_thumbnails': True,
    'thumbnail_size': (400, 533),  # 3:4 aspect ratio for portfolio
    'thumbnail_quality': 85,
    'full_size_max': (2000, 2000),  # Max dimensions for web
    'full_size_quality': 90,
    
    # GitHub Pages base URL
    'base_url': '.'  # Relative URLs for GitHub Pages
}

class LocalPhotosIndexer:
    def __init__(self):
        self.photos = []
        self.source_path = Path(CONFIG['photos_source_dir'])
        
        # Create output directories for web-optimized photos
        self.web_photos_dir = Path(CONFIG['web_photos_dir'])
        self.thumbnails_dir = self.web_photos_dir / 'thumbnails'
        self.full_dir = self.web_photos_dir / 'full'
        
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.full_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def optimize_image(self, input_path: Path, output_path: Path, max_size: tuple, quality: int) -> bool:
        """Optimize image for web"""
        try:
            with Image.open(input_path) as img:
                # Handle HEIC files
                if input_path.suffix.lower() == '.heic':
                    # HEIC files are automatically converted to JPEG
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
                        orientation = exif.get(274)  # 274 is the orientation tag
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                except:
                    pass
                
                # Resize if larger than max_size
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image as JPEG
                output_path = output_path.with_suffix('.jpg')
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
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
            
            # Always use .jpg for web versions
            thumbnail_filename = f"{category}_{photo_id:03d}_{safe_name}_thumb.jpg"
            full_filename = f"{category}_{photo_id:03d}_{safe_name}.jpg"
            
            # Create optimized images
            thumbnail_path = self.thumbnails_dir / thumbnail_filename
            full_path = self.full_dir / full_filename
            
            # Create thumbnail
            thumbnail_success = self.optimize_image(
                file_path, thumbnail_path, 
                CONFIG['thumbnail_size'], CONFIG['thumbnail_quality']
            )
            
            # Create web-optimized full size
            full_success = self.optimize_image(
                file_path, full_path,
                CONFIG['full_size_max'], CONFIG['full_size_quality']
            )
            
            if not (thumbnail_success and full_success):
                print(f"Failed to process {file_path.name}")
                return None
            
            # Generate URLs (relative to website root)
            thumbnail_url = f"./photos/thumbnails/{thumbnail_filename}"
            full_url = f"./photos/full/{full_filename}"
            
            # Extract location
            location = "Unknown"
            if gps_coords:
                # Simple coordinate display - you could add reverse geocoding here
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
                'thumbnail': thumbnail_url,
                'full': full_url,
                'lat': gps_coords[0] if gps_coords else None,
                'lng': gps_coords[1] if gps_coords else None,
                'location': location,
                'date': date_taken or datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d'),
                'filename': full_filename,
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
            print(f"   Please create: {dir_path}")
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
        
        # Debug: Show what files were found
        print(f"   Debug: Found these files:")
        for file in photo_files:
            print(f"     - {file}")
        
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
        print("🔍 Processing local photos for GitHub LFS...")
        
        if not self.source_path.exists():
            print(f"❌ Photos directory not found: {self.source_path}")
            print("Please create the directory and add your photos:")
            for category, directory in CONFIG['photo_directories'].items():
                print(f"   {self.source_path / directory}")
            return
        
        # Clean existing thumbnails and full directories to avoid stale files
        # but preserve any other folders in photos/ directory
        if self.thumbnails_dir.exists():
            print("🧹 Cleaning existing thumbnails...")
            shutil.rmtree(self.thumbnails_dir)
        
        if self.full_dir.exists():
            print("🧹 Cleaning existing full-size photos...")
            shutil.rmtree(self.full_dir)
        
        # Recreate the directories
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.full_dir.mkdir(parents=True, exist_ok=True)
        
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
            for f in self.web_photos_dir.rglob('*') 
            if f.is_file()
        )
        print(f"   Total web-optimized size: {total_size / (1024*1024):.1f} MB")

def main():
    print("🚀 Local Photos Indexer for GitHub LFS")
    print("=" * 45)
    
    # Check if we're in the right directory
    expected_dir = Path('/Users/jodiejacobs/Nextcloud/jodiejacobs-photography')
    current_dir = Path.cwd()
    
    if current_dir != expected_dir:
        print(f"⚠️  Expected to run from: {expected_dir}")
        print(f"   Currently in: {current_dir}")
        print("   Please cd to the correct directory first")
        return
    
    # Initialize indexer
    indexer = LocalPhotosIndexer()
    
    # Generate the index
    indexer.generate_index()
    
    print("\n🎉 Photo processing complete!")
    print("\nNext steps:")
    print("1. Set up Git LFS (if not already done):")
    print("   git lfs install")
    print("   git lfs track 'photos/**/*.jpg'")
    print("   git add .gitattributes")
    print("\n2. Commit photos and index:")
    print("   git add photos/ photos.json")
    print("   git commit -m 'Add optimized photos with LFS'")
    print("   git push")
    print("\n3. Your photos will be hosted on GitHub Pages with LFS")

if __name__ == "__main__":
    main()