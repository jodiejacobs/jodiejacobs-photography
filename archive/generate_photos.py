#!/usr/bin/env python3
"""
Generate photos.json with GitHub Releases URLs
Run this after uploading images to GitHub Releases
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Configuration - Update these with your GitHub details
GITHUB_CONFIG = {
    'username': 'jodiejacobs',           # Your GitHub username
    'repo': 'jodiejacobs-photography',   # Your repo name
    'release_tag': 'v1.0.0'             # The release tag you created
}

def generate_github_url(filename):
    """Generate GitHub Releases download URL"""
    base_url = f"https://github.com/{GITHUB_CONFIG['username']}/{GITHUB_CONFIG['repo']}/releases/download/{GITHUB_CONFIG['release_tag']}"
    return f"{base_url}/{filename}"

def extract_category_from_filename(filename):
    """Extract category from filename pattern like 'street_001_dscf2561.jpg'"""
    name_lower = filename.lower()
    if 'street' in name_lower:
        return 'street'
    elif 'face' in name_lower or 'portrait' in name_lower:
        return 'faces'
    elif 'nature' in name_lower or 'landscape' in name_lower:
        return 'nature'
    else:
        return 'street'  # default

def extract_info_from_filename(filename):
    """Extract title and other info from filename"""
    # Remove extension
    name_without_ext = Path(filename).stem
    
    # Try to extract parts like 'street_001_dscf2561'
    parts = name_without_ext.split('_')
    
    if len(parts) >= 3:
        category = parts[0]
        title = parts[-1].upper()  # Last part is usually the camera file name
    else:
        category = 'street'
        title = name_without_ext
    
    return {
        'title': title,
        'category': extract_category_from_filename(filename)
    }

def scan_portfolio_directory():
    """Scan portfolio directory for images and generate photo data"""
    portfolio_dir = Path('portfolio')
    
    if not portfolio_dir.exists():
        print("❌ Portfolio directory not found!")
        print("Please ensure your photos are in a 'portfolio' directory")
        return []
    
    photos = []
    photo_id = 1
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    
    # Find all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(portfolio_dir.glob(f'*{ext}'))
    
    # Sort files for consistent ordering
    image_files.sort()
    
    for image_file in image_files:
        filename = image_file.name
        info = extract_info_from_filename(filename)
        
        photo_data = {
            'id': photo_id,
            'title': info['title'],
            'category': info['category'],
            'thumbnail': generate_github_url(filename),
            'full': generate_github_url(filename),
            'lat': None,
            'lng': None,
            'location': 'Unknown',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'filename': filename,
            'original_file': filename
        }
        
        photos.append(photo_data)
        photo_id += 1
        
        print(f"✅ Added: {filename} → {info['category']}")
    
    return photos

def generate_photos_json():
    """Generate the photos.json file"""
    print("🔍 Scanning portfolio directory...")
    photos = scan_portfolio_directory()
    
    if not photos:
        print("❌ No images found in portfolio directory")
        return
    
    # Write to photos.json
    with open('photos.json', 'w') as f:
        json.dump(photos, f, indent=2)
    
    print(f"\n✅ Generated photos.json with {len(photos)} photos")
    print(f"📍 URLs point to: https://github.com/{GITHUB_CONFIG['username']}/{GITHUB_CONFIG['repo']}/releases/download/{GITHUB_CONFIG['release_tag']}/")
    
    # Show sample URLs
    if photos:
        print(f"\n📝 Sample URL: {photos[0]['thumbnail']}")

def main():
    print("🚀 GitHub Releases Photos.json Generator")
    print("=" * 50)
    
    # Check if GitHub config is updated
    if GITHUB_CONFIG['username'] == 'your-github-username':
        print("❌ Please update GITHUB_CONFIG with your actual GitHub username!")
        print("Edit this script and replace 'your-github-username' with your real username")
        return
    
    generate_photos_json()
    
    print("\n🎉 Done! Your photos.json is ready for GitHub Releases")
    print("\nNext steps:")
    print("1. Commit and push the updated photos.json")
    print("2. Your website should now load images from GitHub Releases")

if __name__ == "__main__":
    main()