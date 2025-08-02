# Jodie Jacobs Photography Portfolio

A minimalistic photography portfolio featuring faces, street, and nature photography, hosted with GitHub Releases for reliable image delivery.

## Features
- **GitHub Releases image hosting** - Fast, reliable, and free
- **Interactive photo location map** using Leaflet
- **Category filtering** (faces, street, nature)
- **Mobile responsive design**
- **Lightbox gallery** with keyboard navigation
- **1000+ photo support** with lazy loading
- **Automated workflow** for adding new photos

## Live Site
Visit: [jodiejacobs.com](https://jodiejacobs.com)

## Quick Start

### Prerequisites
- [GitHub CLI](https://cli.github.com) installed
- `jq` for JSON manipulation
- Git repository connected to GitHub

### Installation
```bash
# Clone the repository
git clone https://github.com/jodiejacobs/jodiejacobs-photography.git
cd jodiejacobs-photography

# Make the update script executable
chmod +x update_portfolio.sh

# Install GitHub CLI (if not already installed)
# Mac:
brew install gh jq

# Linux:
sudo apt install gh jq

# Authenticate with GitHub
gh auth login
```

### Initial Setup
```bash
# Create GitHub release and generate photos.json
./update_portfolio.sh setup

# Deploy to your website
./update_portfolio.sh deploy
```

## Managing Your Portfolio

### Adding New Photos

1. **Add photos to the portfolio directory:**
   ```bash
   # Copy your photos to the portfolio folder
   cp ~/Pictures/new_photo.jpg portfolio/street_002_sunset.jpg
   ```

2. **Add to GitHub Releases:**
   ```bash
   ./update_portfolio.sh add portfolio/street_002_sunset.jpg
   ```

3. **Deploy changes:**
   ```bash
   ./update_portfolio.sh deploy
   ```

### Photo Naming Convention

For automatic categorization, name your photos using this pattern:
```
[category]_[number]_[title].[ext]
```

**Examples:**
- `street_001_dscf2561.jpg` → Street photography
- `faces_012_portrait.jpg` → Portrait photography  
- `nature_005_sunset.jpg` → Nature photography

**Categories:**
- `street` - Street photography, urban scenes
- `faces` - Portraits, people photos
- `nature` - Landscapes, natural scenes

### Updating Photo Metadata

```bash
# Update photo title
./update_portfolio.sh update street_001_dscf2561.jpg title "Golden Gate Bridge"

# Update location
./update_portfolio.sh update street_001_dscf2561.jpg location "San Francisco, CA"

# Update category
./update_portfolio.sh update street_001_dscf2561.jpg category faces

# Add GPS coordinates for map markers
./update_portfolio.sh update street_001_dscf2561.jpg lat 37.8199
./update_portfolio.sh update street_001_dscf2561.jpg lng -122.4783

# Deploy all changes
./update_portfolio.sh deploy
```

### Available Commands

```bash
# Show current status
./update_portfolio.sh status

# Initial setup (create release and photos.json)
./update_portfolio.sh setup

# Force recreate everything
./update_portfolio.sh setup --force

# Add new photo
./update_portfolio.sh add <image_path>

# Update photo metadata
./update_portfolio.sh update <filename> <field> <value>

# Deploy changes to GitHub
./update_portfolio.sh deploy

# Show help
./update_portfolio.sh help
```

## How It Works

### Image Hosting
- Photos are stored in **GitHub Releases** (not Git LFS)
- Each photo gets a permanent URL like:
  ```
  https://github.com/jodiejacobs/jodiejacobs-photography/releases/download/v1.0.0/photo.jpg
  ```
- **Completely free** with no bandwidth limits
- **Fast global CDN** through GitHub's infrastructure

### Photo Data
All photo metadata is stored in `photos.json`:
```json
[
  {
    "id": 1,
    "title": "DSCF2561",
    "category": "street",
    "thumbnail": "https://github.com/.../street_001_dscf2561.jpg",
    "full": "https://github.com/.../street_001_dscf2561.jpg",
    "lat": 37.8199,
    "lng": -122.4783,
    "location": "San Francisco, CA",
    "date": "2025-01-15",
    "filename": "street_001_dscf2561.jpg"
  }
]
```

### Map Integration
- Photos with GPS coordinates (`lat`/`lng`) appear as markers on the map
- Click markers to see photo title and location
- Uses OpenStreetMap tiles (free alternative to Google Maps)

## Development

### Local Development
```bash
# Run local server to test changes
python -m http.server 8000
# Visit http://localhost:8000
```

### File Structure
```
jodiejacobs-photography/
├── index.html              # Main website
├── photos.json             # Photo metadata
├── update_portfolio.sh     # Portfolio management script
├── portfolio/              # Local photo storage
│   ├── street_001_*.jpg
│   ├── faces_001_*.jpg
│   └── nature_001_*.jpg
├── README.md
└── CNAME                   # Custom domain config
```

### Customization

**Update configuration in `update_portfolio.sh`:**
```bash
# Edit these variables at the top of the script
GITHUB_USER="your-username"
REPO_NAME="your-repo-name"
RELEASE_TAG="v1.0.0"
```

**Modify website styling:**
- Edit `index.html` for layout changes
- Uses Tailwind CSS classes for styling
- Responsive design works on mobile and desktop

## Deployment

The site deploys automatically when you push changes to GitHub:

1. **GitHub Pages** serves the website from your repository
2. **GitHub Releases** hosts the image files
3. **Custom domain** configured through CNAME file

### Custom Domain Setup
1. Add your domain to the `CNAME` file
2. Configure DNS with your domain provider:
   ```
   CNAME jodiejacobs.com → jodiejacobs.github.io
   ```

## Troubleshooting

### Common Issues

**"GitHub CLI not found":**
```bash
# Install GitHub CLI
brew install gh        # Mac
sudo apt install gh    # Linux
```

**"Not authenticated":**
```bash
gh auth login
# Follow the prompts to authenticate
```

**"jq not found":**
```bash
brew install jq        # Mac
sudo apt install jq    # Linux
```

**Photos not loading:**
1. Check that the GitHub release exists
2. Verify URLs in `photos.json` are correct
3. Ensure photos were uploaded to the release

**Map not showing:**
1. Check browser console for JavaScript errors
2. Verify photos have `lat`/`lng` coordinates
3. Ensure Leaflet library is loading

### Getting Help

- Check the [Issues](https://github.com/jodiejacobs/jodiejacobs-photography/issues) page
- Run `./update_portfolio.sh status` to diagnose problems
- View browser developer tools for JavaScript errors

## License

© 2025 Jodie Jacobs. All rights reserved.

---

## Technical Details

- **Frontend**: Pure HTML/CSS/JavaScript with Tailwind CSS
- **Maps**: Leaflet.js with OpenStreetMap tiles
- **Image Hosting**: GitHub Releases API
- **Deployment**: GitHub Pages
- **Management**: Bash scripts with GitHub CLI