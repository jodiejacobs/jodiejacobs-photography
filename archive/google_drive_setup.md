
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
