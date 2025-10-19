# Publishing the Wiki to GitHub

There are two common ways to publish these pages to the GitHub Wiki.

## Option A — Use the GitHub UI (Quick)

1. Open: https://github.com/hunes3d/kAIcad/wiki
2. Create pages with these titles and paste content from the local `wiki/` files:
   - Home
   - Architecture
   - Component-Inspection
   - Hierarchical-Sheets
   - Roadmap
   - Changelog
   - Dev-Notes
3. Save each page. The sidebar will update automatically.

## Option B — Git clone of the Wiki (Scriptable)

1. Clone the wiki repository:
```powershell
git clone https://github.com/hunes3d/kAIcad.wiki.git
cd kAIcad.wiki
```

2. Copy pages from the local project wiki folder:
```powershell
Copy-Item ..\kAIcad\wiki\*.md .
```

3. Commit and push:
```powershell
git add .
git commit -m "Publish wiki pages"
git push
```

Your wiki will be available at: https://github.com/hunes3d/kAIcad/wiki
