# Quick Wiki Setup Guide

The wiki documentation is ready in `docs/wiki/`. To publish it:

## Option 1: Automated Script (Easiest)

```powershell
.\docs\setup-wiki.ps1
```

The script will guide you through:
1. Initializing the wiki on GitHub (one-time)
2. Cloning the wiki repository
3. Copying documentation
4. Pushing to GitHub

## Option 2: Manual Setup

### Step 1: Initialize Wiki (First Time Only)

1. Go to https://github.com/hunes3d/kAIcad/wiki
2. Click **"Create the first page"**
3. Type anything (e.g., "# Welcome")
4. Click **"Save Page"**

### Step 2: Clone and Publish

```bash
# Go to parent directory
cd ..

# Clone the wiki
git clone https://github.com/hunes3d/kAIcad.wiki.git

# Copy documentation
cp kAIcad/docs/wiki/*.md kAIcad.wiki/

# Commit and push
cd kAIcad.wiki
git add .
git commit -m "Add comprehensive wiki documentation"
git push
```

### Step 3: View Your Wiki

Visit https://github.com/hunes3d/kAIcad/wiki

## Wiki Pages Included

- ✅ **Home** - Overview with quick links
- ✅ **Getting Started** - Quick start guide
- ✅ **Installation** - Platform-specific installation
- ✅ **Features** - Complete feature documentation

## Why Wiki Needs Manual Initialization

GitHub wikis are separate Git repositories that must be initialized through the web interface first. This is a GitHub limitation - they can't be created via API or CLI.

## After Publishing

Once published, you can edit wiki pages either:
- Through the GitHub web interface
- By cloning the wiki repo and pushing changes
- By updating `docs/wiki/` in main repo and re-copying

The `docs/wiki/` folder in the main repository serves as the source of truth for wiki content.
