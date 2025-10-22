# kAIcad Wiki Content

This directory contains the source files for the kAIcad GitHub Wiki.

## Setting Up the Wiki

To publish these pages to the GitHub wiki:

1. **Initialize the wiki** (first time only):
   - Go to https://github.com/hunes3d/kAIcad/wiki
   - Click "Create the first page"
   - Add any content and save

2. **Clone the wiki repository**:
   ```bash
   cd ..
   git clone https://github.com/hunes3d/kAIcad.wiki.git
   ```

3. **Copy wiki content**:
   ```bash
   cp kAIcad/docs/wiki/*.md kAIcad.wiki/
   cd kAIcad.wiki
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add wiki documentation"
   git push
   ```

## Wiki Pages

- **Home.md** - Main landing page with overview
- **Getting-Started.md** - Quick start guide
- **Installation.md** - Detailed installation instructions
- **Features.md** - Complete feature documentation
- **Configuration.md** - Settings and customization (TODO)
- **User-Guide.md** - Detailed usage guide (TODO)
- **Troubleshooting.md** - Common issues and solutions (TODO)

## Maintenance

To update the wiki:

1. Edit the `.md` files in this directory
2. Copy updated files to the wiki repository
3. Commit and push changes

## TODO

Additional wiki pages to create:

- [ ] Configuration.md - Detailed configuration guide
- [ ] User-Guide.md - Step-by-step usage instructions
- [ ] Troubleshooting.md - FAQ and common issues
- [ ] Contributing.md - How to contribute
- [ ] API-Reference.md - Developer documentation
- [ ] Examples.md - Real-world usage examples
