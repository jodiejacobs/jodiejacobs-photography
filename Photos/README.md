# Photos Directory

This directory contains the source photos for your portfolio website.

## Directory Structure

- **Faces/** - Portrait and people photography
- **Street/** - Street photography and urban scenes  
- **Nature/** - Landscape and nature photography

## Adding Photos

1. Add your photos to the appropriate category folder
2. Supported formats: .jpg, .jpeg, .png, .webp, .heic
3. Run the portfolio update script: `./update_portfolio.sh`

## How It Works

The indexer script will:
- Scan these directories for photos
- Extract EXIF data (GPS coordinates, dates, etc.)
- Create web-optimized versions in the `photos/` directory
- Generate `photos.json` with metadata
- Upload everything to GitHub with LFS

Your original photos stay in this directory, while optimized versions are created for the web.
