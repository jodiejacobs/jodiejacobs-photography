#!/bin/bash

# Photography Portfolio Update Script
# This script automates the entire process of updating your photography portfolio
# with new photos from Google Drive

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/Users/jodiejacobs/Nextcloud/jodiejacobs-photography"
PHOTOS_SOURCE_DIR="/Users/jodiejacobs/Nextcloud/jodiejacobs-photography/Photos"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed or not in PATH"
        exit 1
    fi
}

# Main function
main() {
    echo -e "${BLUE}🚀 Photography Portfolio Update Script${NC}"
    echo "=================================================="
    
    # Check if we're in the right directory
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    print_success "Changed to project directory: $PROJECT_DIR"
    
    # Check if Photos directory exists
    if [ ! -d "$PHOTOS_SOURCE_DIR" ]; then
        print_error "Photos directory not found: $PHOTOS_SOURCE_DIR"
        print_warning "Please create the directory and add your photos:"
        print_warning "  mkdir -p $PHOTOS_SOURCE_DIR/{Faces,Street,Nature}"
        exit 1
    fi
    
    print_success "Photos directory found and accessible"
    
    # Check required commands
    print_status "Checking dependencies..."
    check_command "python3"
    check_command "git"
    print_success "All dependencies found"
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        print_error "Not in a git repository. Run 'git init' first."
        exit 1
    fi
    
    # Install Python dependencies if needed
    print_status "Installing/updating Python dependencies..."
    python3 -m pip install pillow exifread --quiet
    print_success "Python dependencies ready"
    
    # Set up Git LFS for photos if not already configured
    print_status "Ensuring Git LFS is configured..."
    git lfs install >/dev/null 2>&1 || true
    git lfs track "portfolio/**/*.jpg" >/dev/null 2>&1 || true
    git lfs track "portfolio/**/*.jpeg" >/dev/null 2>&1 || true  
    git lfs track "portfolio/**/*.png" >/dev/null 2>&1 || true
    
    # Add .gitattributes if it exists
    if [ -f ".gitattributes" ]; then
        git add .gitattributes
        print_success "Git LFS tracking configured"
    fi
    
    # Check if indexer script exists
    if [ ! -f "simple_photos_indexer.py" ]; then
        print_error "simple_photos_indexer.py not found in current directory"
        print_warning "Please save the Simple Photos Indexer script first"
        exit 1
    fi
    
    # Run the photo indexer
    print_status "Processing local photos (simplified, no thumbnails)..."
    python3 simple_photos_indexer.py
    
    if [ $? -eq 0 ]; then
        print_success "Photo indexing completed successfully"
    else
        print_error "Photo indexing failed"
        exit 1
    fi
    
    # Check if photos.json was created
    if [ ! -f "photos.json" ]; then
        print_error "photos.json was not created"
        exit 1
    fi
    
    # Show summary of photos.json
    photo_count=$(python3 -c "import json; data = json.load(open('photos.json')); print(len(data))")
    print_success "Generated photos.json with $photo_count photos"
    
    # Git operations
    print_status "Checking git status..."
    
    # Check if there are changes to commit
    if git diff --quiet && git diff --cached --quiet; then
        print_warning "No changes detected in photos.json"
        echo "Your portfolio is already up to date!"
        exit 0
    fi
    
    # Show what's changed
    print_status "Changes detected:"
    git status --porcelain
    
    # Add files to git
    print_status "Adding files to git..."
    git add photos.json
    
    # Add optimized photos directory
    if [ -d "portfolio" ]; then
        git add portfolio/
        print_success "Added optimized portfolio directory"
    fi
    
    # Add any other changed files (optional)
    if [ -f "index.html" ] && git diff --name-only | grep -q "index.html"; then
        git add index.html
        print_success "Added updated index.html"
    fi
    
    if [ -f "robots.txt" ] && git diff --name-only | grep -q "robots.txt"; then
        git add robots.txt
        print_success "Added updated robots.txt"
    fi
    
    # Commit changes
    commit_message="Update portfolio with local photos from $(date '+%Y-%m-%d %H:%M')"
    print_status "Committing changes with message: '$commit_message'"
    git commit -m "$commit_message"
    print_success "Changes committed successfully"
    
    # Push to GitHub
    print_status "Pushing to GitHub..."
    
    # Check if we have a remote
    if ! git remote | grep -q "origin"; then
        print_error "No 'origin' remote found. Add your GitHub repository first:"
        echo "git remote add origin https://github.com/yourusername/jodiejacobs-photography.git"
        exit 1
    fi
    
    # Push to main/master branch
    current_branch=$(git branch --show-current)
    git push origin "$current_branch"
    
    if [ $? -eq 0 ]; then
        print_success "Successfully pushed to GitHub!"
    else
        print_error "Failed to push to GitHub"
        print_warning "You may need to resolve conflicts or check your credentials"
        exit 1
    fi
    
    # Final success message
    echo ""
    echo -e "${GREEN}🎉 Portfolio update complete!${NC}"
    echo "=================================================="
    echo "📊 Updated with $photo_count photos"
    echo "🌐 Your website should update shortly at: https://jodiejacobs.com"
    echo "📸 Photos are optimized and hosted via GitHub LFS"
    echo ""
    echo "Next steps:"
    echo "• Check your website to make sure photos load correctly"
    echo "• Add new photos to: $PHOTOS_SOURCE_DIR"
    echo "• Run this script again to update your portfolio"
    echo ""
}

# Function to show help
show_help() {
    echo "Photography Portfolio Update Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -n, --dry-run  Show what would be done without making changes"
    echo ""
    echo "This script will:"
    echo "1. Scan your Google Drive for photos"
    echo "2. Extract metadata (GPS, dates, etc.)"
    echo "3. Generate photos.json"
    echo "4. Commit and push changes to GitHub"
    echo ""
}

# Function for dry run
dry_run() {
    echo -e "${YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
    echo "=================================================="
    echo "Would scan: $PHOTOS_SOURCE_DIR"
    echo "Would update: $PROJECT_DIR/photos.json"
    echo "Would optimize photos to: $PROJECT_DIR/portfolio/"
    echo "Would commit and push to GitHub with LFS"
    echo ""
    echo "To actually run the update, use: $0"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -n|--dry-run)
        dry_run
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac