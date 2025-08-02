#!/bin/bash
# GitHub Releases Portfolio Update Script
# Similar to update_portfolio.sh but uses GitHub Releases for image hosting

set -e  # Exit on any error

# Configuration
GITHUB_USER="jodiejacobs"
REPO_NAME="jodiejacobs-photography"
RELEASE_TAG="v1.0.0"
PORTFOLIO_DIR="photos"
PHOTOS_JSON="photos.json"
BASE_URL="https://github.com/$GITHUB_USER/$REPO_NAME/releases/download/$RELEASE_TAG"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI not found. Please install it:"
        echo "  Mac: brew install gh"
        echo "  Linux: sudo apt install gh"
        echo "  Or visit: https://cli.github.com"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub CLI"
        echo "Run: gh auth login"
        exit 1
    fi
    
    # Check if jq is installed (for JSON manipulation)
    if ! command -v jq &> /dev/null; then
        log_warning "jq not found. Installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install jq
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt install jq -y
        fi
    fi
    
    log_success "Dependencies OK"
}

# Extract photo info from filename
extract_photo_info() {
    local filename="$1"
    local basename=$(basename "$filename" | sed 's/\.[^.]*$//')  # Remove extension
    local category="street"  # default
    local title=""
    
    # Detect category from filename
    if [[ "$basename" =~ (street|urban|city) ]]; then
        category="street"
    elif [[ "$basename" =~ (face|portrait|person|people) ]]; then
        category="faces"
    elif [[ "$basename" =~ (nature|landscape|forest|mountain|ocean|tree) ]]; then
        category="nature"
    fi
    
    # Extract title (usually the last part after underscores)
    if [[ "$basename" =~ _([^_]+)$ ]]; then
        title=$(echo "${BASH_REMATCH[1]}" | tr '[:lower:]' '[:upper:]')
    else
        title=$(echo "$basename" | tr '[:lower:]' '[:upper:]')
    fi
    
    echo "$category|$title"
}

# Scan portfolio directory and generate photo data
scan_portfolio() {
    log_info "Scanning portfolio directory..."
    
    if [[ ! -d "$PORTFOLIO_DIR" ]]; then
        log_error "Portfolio directory '$PORTFOLIO_DIR' not found!"
        exit 1
    fi
    
    local photo_id=1
    local photos_array="[]"
    
    # Find all image files
    shopt -s nullglob  # Handle case where no files match
    for img in "$PORTFOLIO_DIR"/*.jpg "$PORTFOLIO_DIR"/*.jpeg "$PORTFOLIO_DIR"/*.png "$PORTFOLIO_DIR"/*.JPG "$PORTFOLIO_DIR"/*.JPEG "$PORTFOLIO_DIR"/*.PNG; do
        # Skip if no files match
        [[ ! -f "$img" ]] && continue
        
        local filename=$(basename "$img")
        local info=$(extract_photo_info "$filename")
        local category=$(echo "$info" | cut -d'|' -f1)
        local title=$(echo "$info" | cut -d'|' -f2)
        local date=$(date +%Y-%m-%d)
        
        # Create photo object
        local photo_obj=$(jq -n \
            --argjson id "$photo_id" \
            --arg title "$title" \
            --arg category "$category" \
            --arg thumbnail "$BASE_URL/$filename" \
            --arg full "$BASE_URL/$filename" \
            --arg location "Unknown" \
            --arg date "$date" \
            --arg filename "$filename" \
            --arg original_file "$filename" \
            '{
                id: $id,
                title: $title,
                category: $category,
                thumbnail: $thumbnail,
                full: $full,
                lat: null,
                lng: null,
                location: $location,
                date: $date,
                filename: $filename,
                original_file: $original_file
            }')
        
        # Add to photos array
        photos_array=$(echo "$photos_array" | jq ". += [$photo_obj]")
        
        log_success "Found: $filename → $category → $title"
        ((photo_id++))
    done
    
    # Write photos.json
    echo "$photos_array" | jq '.' > "$PHOTOS_JSON"
    
    local photo_count=$(echo "$photos_array" | jq length)
    log_success "Generated $PHOTOS_JSON with $photo_count photos"
}

# Create or update GitHub release
manage_release() {
    local force_recreate="$1"
    
    log_info "Managing GitHub release..."
    
    # Check if release exists
    if gh release view "$RELEASE_TAG" &> /dev/null; then
        if [[ "$force_recreate" == "true" ]]; then
            log_warning "Deleting existing release $RELEASE_TAG"
            gh release delete "$RELEASE_TAG" --yes
        else
            log_info "Release $RELEASE_TAG already exists"
            return 0
        fi
    fi
    
    # Find all image files
    local image_files=()
    shopt -s nullglob  # Handle case where no files match
    for img in "$PORTFOLIO_DIR"/*.jpg "$PORTFOLIO_DIR"/*.jpeg "$PORTFOLIO_DIR"/*.png "$PORTFOLIO_DIR"/*.JPG "$PORTFOLIO_DIR"/*.JPEG "$PORTFOLIO_DIR"/*.PNG; do
        [[ -f "$img" ]] && image_files+=("$img")
    done
    
    if [[ ${#image_files[@]} -eq 0 ]]; then
        log_error "No image files found in $PORTFOLIO_DIR"
        exit 1
    fi
    
    log_info "Creating release $RELEASE_TAG with ${#image_files[@]} images..."
    
    # Create release with all images
    gh release create "$RELEASE_TAG" \
        --title "Portfolio Images" \
        --notes "Photography portfolio images for $GITHUB_USER.com" \
        "${image_files[@]}"
    
    log_success "Release created successfully!"
    log_info "View at: https://github.com/$GITHUB_USER/$REPO_NAME/releases/tag/$RELEASE_TAG"
}

# Add new photo to existing release
add_photo() {
    local image_path="$1"
    
    if [[ ! -f "$image_path" ]]; then
        log_error "Image file not found: $image_path"
        exit 1
    fi
    
    log_info "Adding $(basename "$image_path") to release..."
    
    # Upload to release
    gh release upload "$RELEASE_TAG" "$image_path"
    
    log_success "Added $(basename "$image_path") to release"
    
    # Regenerate photos.json
    scan_portfolio
}

# Update photo metadata
update_photo() {
    local filename="$1"
    local field="$2"
    local value="$3"
    
    if [[ ! -f "$PHOTOS_JSON" ]]; then
        log_error "$PHOTOS_JSON not found"
        exit 1
    fi
    
    # Update the specific field
    local updated_json=$(jq --arg filename "$filename" --arg field "$field" --arg value "$value" \
        'map(if .filename == $filename then .[$field] = $value else . end)' "$PHOTOS_JSON")
    
    echo "$updated_json" > "$PHOTOS_JSON"
    
    log_success "Updated $field for $filename: $value"
}

# Deploy changes to GitHub
deploy() {
    log_info "Deploying changes to GitHub..."
    
    # Add photos.json
    git add "$PHOTOS_JSON"
    
    # Commit if there are changes
    if git diff --cached --quiet; then
        log_info "No changes to commit"
    else
        git commit -m "Update $PHOTOS_JSON for GitHub Releases"
        log_success "Committed changes"
    fi
    
    # Push changes
    git push
    
    log_success "Changes deployed to GitHub!"
    log_info "Your site will update at: https://$GITHUB_USER.github.io/$REPO_NAME"
}

# Show current status
show_status() {
    log_info "Portfolio Status:"
    
    # Count files in portfolio
    local file_count=0
    shopt -s nullglob  # Handle case where no files match
    for img in "$PORTFOLIO_DIR"/*.jpg "$PORTFOLIO_DIR"/*.jpeg "$PORTFOLIO_DIR"/*.png "$PORTFOLIO_DIR"/*.JPG "$PORTFOLIO_DIR"/*.JPEG "$PORTFOLIO_DIR"/*.PNG; do
        [[ -f "$img" ]] && ((file_count++))
    done
    
    echo "📁 Portfolio directory: $file_count images"
    
    # Check photos.json
    if [[ -f "$PHOTOS_JSON" ]]; then
        local json_count=$(jq length "$PHOTOS_JSON" 2>/dev/null || echo "0")
        echo "📄 $PHOTOS_JSON: $json_count photos"
    else
        echo "📄 $PHOTOS_JSON: not found"
    fi
    
    # Check release
    if gh release view "$RELEASE_TAG" &> /dev/null; then
        echo "📦 GitHub Release: $RELEASE_TAG exists"
    else
        echo "📦 GitHub Release: $RELEASE_TAG not found"
    fi
    
    # Check git status
    if git diff --quiet && git diff --cached --quiet; then
        echo "📝 Git status: clean"
    else
        echo "📝 Git status: changes pending"
    fi
}

# Show help
show_help() {
    echo "GitHub Releases Portfolio Manager"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup [--force]           Initial setup - create release and photos.json"
    echo "  add <image_path>          Add new photo to release"
    echo "  update <filename> <field> <value>  Update photo metadata"
    echo "  deploy                    Deploy changes to GitHub"
    echo "  status                    Show current status"
    echo "  help                      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 setup                                    # Initial setup"
    echo "  $0 setup --force                           # Recreate release"
    echo "  $0 add portfolio/new_photo.jpg             # Add new photo"
    echo "  $0 update street_001.jpg title 'Golden Gate'  # Update title"
    echo "  $0 update street_001.jpg location 'SF, CA'    # Update location"
    echo "  $0 deploy                                   # Deploy all changes"
    echo ""
}

# Main script logic
main() {
    local command="${1:-help}"
    
    case "$command" in
        "setup")
            check_dependencies
            local force_flag="false"
            [[ "$2" == "--force" ]] && force_flag="true"
            manage_release "$force_flag"
            scan_portfolio
            log_success "Setup complete! Run '$0 deploy' to push changes."
            ;;
        "add")
            if [[ -z "$2" ]]; then
                log_error "Image path required"
                echo "Usage: $0 add <image_path>"
                exit 1
            fi
            check_dependencies
            add_photo "$2"
            log_success "Photo added! Run '$0 deploy' to push changes."
            ;;
        "update")
            if [[ -z "$2" || -z "$3" || -z "$4" ]]; then
                log_error "Missing arguments"
                echo "Usage: $0 update <filename> <field> <value>"
                exit 1
            fi
            update_photo "$2" "$3" "$4"
            log_success "Photo updated! Run '$0 deploy' to push changes."
            ;;
        "deploy")
            check_dependencies
            deploy
            ;;
        "status")
            show_status
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"