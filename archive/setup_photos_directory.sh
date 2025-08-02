#!/bin/bash

# Setup Photos Directory for Local Portfolio
# This script creates the directory structure for your local photos

set -e

# Configuration
PROJECT_DIR="/Users/jodiejacobs/Nextcloud/jodiejacobs-photography"
PHOTOS_DIR="$PROJECT_DIR/Photos"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📁 Setting up Photos Directory${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Create Photos directory structure
echo -e "${BLUE}Creating directory structure...${NC}"

mkdir -p "$PHOTOS_DIR/Faces"
mkdir -p "$PHOTOS_DIR/Street" 
mkdir -p "$PHOTOS_DIR/Nature"

echo -e "${GREEN}✅ Created Photos directory structure:${NC}"
echo "   $PHOTOS_DIR/Faces/"
echo "   $PHOTOS_DIR/Street/"
echo "   $PHOTOS_DIR/Nature/"

# Create .gitkeep files so empty directories are tracked
touch "$PHOTOS_DIR/Faces/.gitkeep"
touch "$PHOTOS_DIR/Street/.gitkeep"
touch "$PHOTOS_DIR/Nature/.gitkeep"

echo -e "${GREEN}✅ Added .gitkeep files${NC}"

# Set up Git LFS if not already configured
echo -e "${BLUE}Setting up Git LFS...${NC}"

if command -v git &> /dev/null; then
    # Initialize Git LFS
    git lfs install 2>/dev/null || echo "Git LFS already initialized"
    
    # Track photo files
    git lfs track "photos/**/*.jpg" 2>/dev/null || true
    git lfs track "photos/**/*.jpeg" 2>/dev/null || true
    git lfs track "photos/**/*.png" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Git LFS configured for photos${NC}"
    
    # Add .gitattributes if it was created
    if [ -f ".gitattributes" ]; then
        git add .gitattributes
        echo -e "${GREEN}✅ Added .gitattributes${NC}"
    fi
    
    # Add the Photos directory structure
    git add Photos/
    echo -e "${GREEN}✅ Added Photos directory to git${NC}"
    
else
    echo -e "${YELLOW}⚠️  Git not found, skipping LFS setup${NC}"
fi

# Create a README for the Photos directory
cat > "$PHOTOS_DIR/README.md" << 'EOF'
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
EOF

git add "$PHOTOS_DIR/README.md" 2>/dev/null || true

echo ""
echo -e "${GREEN}🎉 Photos directory setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Add your photos to the appropriate directories:"
echo "   - Portraits → $PHOTOS_DIR/Faces/"
echo "   - Street photography → $PHOTOS_DIR/Street/"
echo "   - Nature photos → $PHOTOS_DIR/Nature/"
echo ""
echo "2. Run the portfolio update script:"
echo "   ./update_portfolio.sh"
echo ""
echo "3. Your photos will be optimized and deployed automatically!"
echo ""
echo -e "${BLUE}Directory structure created:${NC}"
tree "$PHOTOS_DIR" 2>/dev/null || ls -la "$PHOTOS_DIR"