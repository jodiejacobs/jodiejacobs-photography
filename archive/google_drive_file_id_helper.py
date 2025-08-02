#!/usr/bin/env python3
"""
Google Drive File ID Helper

This script helps you get the actual file IDs from Google Drive for direct image access.
It updates your photos.json with working Google Drive direct image URLs.

Usage:
1. First run google_drive_indexer.py to generate initial photos.json
2. Set up public sharing for your folders
3. Run this script to update with actual file IDs
"""

import json
import os
from pathlib import Path

def extract_file_id_from_url(url):
    """Extract file ID from various Google Drive URL formats"""
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in url:
        return url.split('id=')[1].split('&')[0]
    return None

def create_direct_image_url(file_id):
    """Create direct image URL from Google Drive file ID"""
    return f"https://drive.google.com/uc?export=view&id={file_id}"

def update_photos_with_file_ids():
    """
    Interactive script to help update photos.json with actual Google Drive file IDs
    """
    photos_file = 'photos.json'
    
    if not Path(photos_file).exists():
        print(f"❌ {photos_file} not found. Run google_drive_indexer.py first.")
        return
    
    # Load existing photos
    with open(photos_file, 'r') as f:
        photos = json.load(f)
    
    print("🔗 Google Drive File ID Updater")
    print("=" * 40)
    print(f"Found {len(photos)} photos to update")
    print("\nFor each photo, you can:")
    print("1. Enter the Google Drive sharing link for that file")
    print("2. Enter the file ID directly")
    print("3. Skip (keep placeholder URL)")
    print("4. Type 'done' to finish\n")
    
    updated_count = 0
    
    for i, photo in enumerate(photos, 1):
        print(f"\n📸 Photo {i}/{len(photos)}: {photo['title']}")
        print(f"   Category: {photo['category']}")
        print(f"   Current thumbnail: {photo['thumbnail']}")
        print(f"   Current full: {photo['full']}")
        
        # Check if already has real file ID
        if 'FILE_ID_FOR_' not in photo['thumbnail']:
            print("   ✅ Already has real file ID, skipping...")
            continue
        
        response = input("   Enter Google Drive link, file ID, or 'skip'/'done': ").strip()
        
        if response.lower() == 'done':
            break
        elif response.lower() == 'skip' or not response:
            continue
        
        # Extract file ID
        file_id = None
        if response.startswith('http'):
            file_id = extract_file_id_from_url(response)
        else:
            # Assume it's a direct file ID
            file_id = response
        
        if file_id:
            # Update URLs
            direct_url = create_direct_image_url(file_id)
            photo['thumbnail'] = direct_url
            photo['full'] = direct_url
            photo['file_id'] = file_id
            
            print(f"   ✅ Updated with file ID: {file_id}")
            updated_count += 1
        else:
            print("   ❌ Could not extract file ID from that input")
    
    # Save updated photos
    with open(photos_file, 'w') as f:
        json.dump(photos, f, indent=2)
    
    print(f"\n🎉 Updated {updated_count} photos")
    print(f"💾 Saved to {photos_file}")

def create_batch_update_template():
    """Create a template for batch updating file IDs"""
    photos_file = 'photos.json'
    
    if not Path(photos_file).exists():
        print(f"❌ {photos_file} not found. Run google_drive_indexer.py first.")
        return
    
    with open(photos_file, 'r') as f:
        photos = json.load(f)
    
    template = "# Google Drive File ID Mapping\n"
    template += "# Format: filename = file_id\n"
    template += "# Get file IDs by right-clicking photos in Google Drive > Get link\n\n"
    
    for photo in photos:
        if 'FILE_ID_FOR_' in photo['thumbnail']:
            template += f"{photo['filename']} = YOUR_FILE_ID_HERE\n"
    
    with open('file_id_mapping.txt', 'w') as f:
        f.write(template)
    
    print("📝 Created file_id_mapping.txt template")
    print("   Fill in the file IDs and run update_from_mapping() to batch update")

def update_from_mapping():
    """Update photos.json from a file ID mapping file"""
    mapping_file = 'file_id_mapping.txt'
    photos_file = 'photos.json'
    
    if not Path(mapping_file).exists():
        print(f"❌ {mapping_file} not found. Run create_batch_update_template() first.")
        return
    
    if not Path(photos_file).exists():
        print(f"❌ {photos_file} not found.")
        return
    
    # Parse mapping file
    file_id_map = {}
    with open(mapping_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                filename, file_id = line.split('=', 1)
                file_id_map[filename.strip()] = file_id.strip()
    
    # Load and update photos
    with open(photos_file, 'r') as f:
        photos = json.load(f)
    
    updated_count = 0
    for photo in photos:
        filename = photo['filename']
        if filename in file_id_map and file_id_map[filename] != 'YOUR_FILE_ID_HERE':
            file_id = file_id_map[filename]
            direct_url = create_direct_image_url(file_id)
            photo['thumbnail'] = direct_url
            photo['full'] = direct_url
            photo['file_id'] = file_id
            updated_count += 1
    
    # Save updated photos
    with open(photos_file, 'w') as f:
        json.dump(photos, f, indent=2)
    
    print(f"🎉 Updated {updated_count} photos from mapping file")
    print(f"💾 Saved to {photos_file}")

def main():
    print("🔗 Google Drive File ID Helper")
    print("=" * 30)
    print("Choose an option:")
    print("1. Interactive update (one by one)")
    print("2. Create batch update template")
    print("3. Update from mapping file")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        update_photos_with_file_ids()
    elif choice == '2':
        create_batch_update_template()
    elif choice == '3':
        update_from_mapping()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()