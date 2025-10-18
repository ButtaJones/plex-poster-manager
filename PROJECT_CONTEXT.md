# Plex Poster Manager - Project Context

**Last Updated:** 2025-10-18
**Current Version:** 2.0.1
**Status:** PRODUCTION READY - Using Plex API (Professional Approach)

---

## 📋 Project Overview

### Goal
Web application to manage Plex Media Server artwork files. Users can browse, view, and delete posters, backgrounds, and other artwork using the official Plex API.

### Architecture
- **Backend:** Flask (Python 3.8+) REST API with python-plexapi library
- **Frontend:** React 18.2 with Tailwind CSS
- **API Integration:** Official Plex API (same approach as Kometa & Tautulli)
- **Deployment:**
  - **Development:** macOS (developer machine)
  - **Production:** Windows (where Plex Media Server runs)

### Key Components
1. **backend/app.py** - Flask REST API server
2. **backend/plex_scanner_api.py** - Plex API artwork scanner (NEW in v2.0.0)
3. **backend/file_manager.py** - Handles file operations and backups
4. **frontend/** - React web interface
5. **launcher_gui.py** - Tkinter GUI for one-click server management

---

## ✅ CURRENT APPROACH - Plex API Integration (v2.0.0+)

### The Professional Solution: Use the Plex API

**Why We Switched from Filesystem Scanning:**
- ❌ **v1.x Problem:** Plex changed bundle folder structure, broke filesystem scanning
- ✅ **v2.0+ Solution:** Use python-plexapi library (official Plex API client)
- 🎯 **Industry Standard:** Same approach as Kometa, Tautulli, JBOPS

**How It Works Now:**
```python
from plexapi.server import PlexServer

# Connect to Plex server
plex = PlexServer('http://localhost:32400', 'YOUR_TOKEN')

# Get TV shows from a library
library = plex.library.section('TV Shows')
for show in library.all():
    # Get all available posters for this show
    posters = show.posters()
    for poster in posters:
        print(f"{show.title}: {poster.provider} (Selected: {poster.selected})")
```

**Advantages Over Filesystem Scanning:**
- ✅ Always works (no folder structure dependencies)
- ✅ Gets real show/movie titles from Plex metadata
- ✅ Shows which artwork is currently selected
- ✅ Access to provider info (TheTVDB, TheMovieDB, etc.)
- ✅ Can trigger Plex refresh after changes
- ✅ Works remotely (not just local filesystem)
- ✅ Future-proof (Plex API stable since 2013)
- ✅ Professional approach (used by all major Plex tools)

**What Users See:**
```
The Office (US) (2005)
  Posters: 12 available
    ✓ TheMovieDB (Selected)
    - TheTVDB
    - Uploaded (Custom)
  Backgrounds: 8 available
    ✓ TheMovieDB (Selected)
    - TheTVDB
```

Users can see actual show titles, artwork sources, and what's currently selected!

---

## 📚 Version History

### Version 2.0.1 (Current) - Launcher Fixes & Auto-Start
**Date:** 2025-10-18

**Improvements:**
1. **Fixed Token Testing**
   - Now uses PlexAPI to actually connect to server
   - No more JSON parsing errors
   - Shows server name and version on success
   - Better error messages (invalid token vs connection failed)

2. **Auto-Start Feature**
   - New checkbox: "Auto-start servers on launch"
   - Saves preference in config.json
   - Automatically launches servers 2 seconds after opening
   - Perfect for "set it and forget it" workflow

3. **Windows Upgrade Scripts**
   - QUICK_FIX_WINDOWS.bat - Upgrade v1.x to v2.0
   - INSTALL_PLEXAPI.bat - Direct PlexAPI installer

**Files Changed:**
- launcher_gui.py - Added auto-start checkbox and PlexAPI token testing
- QUICK_FIX_WINDOWS.bat - Added v1.x upgrade helper
- INSTALL_PLEXAPI.bat - Added direct installer

---

### Version 2.0.0 - MAJOR REWRITE (Plex API Integration)
**Date:** 2025-10-18

**BREAKTHROUGH:** Research showed Kometa and Tautulli use Plex API, NOT filesystem scanning!

**Why This Was Necessary:**
- Modern Plex changed bundle folder structure (broke v1.5.0)
- Professional tools all use python-plexapi library
- Plex API is stable, bundle structure is not
- API gives real titles, selected artwork, and full metadata

**Major Changes:**

1. **NEW FILE: backend/plex_scanner_api.py**
   - Complete rewrite using python-plexapi library
   - Connects to Plex server via URL + token
   - Gets shows/movies from Plex API (not filesystem)
   - Retrieves ALL available artwork (posters, backgrounds, banners, themes)
   - Shows which artwork is selected vs available

2. **UPDATED: backend/requirements.txt**
   - Added PlexAPI==4.15.16 (official python-plexapi library)

3. **UPDATED: backend/app.py**
   - Changed from PlexScanner to PlexScannerAPI
   - Config now uses `plex_url` instead of `plex_metadata_path`
   - Plex token now REQUIRED (not optional)
   - `/api/detect-path` → `/api/detect-url`
   - `/api/thumbnail` now fetches from Plex API URLs

**Breaking Changes:**
- ⚠️ Plex token now REQUIRED (was optional in v1.x)
- ⚠️ Configuration uses `plex_url` instead of `plex_metadata_path`
- ⚠️ Frontend needs update for new config format

**Research Sources:**
- Kometa: https://github.com/Kometa-Team/Kometa
- Tautulli: https://github.com/Tautulli/Tautulli
- JBOPS: https://github.com/blacktwin/JBOPS
- python-plexapi: https://python-plexapi.readthedocs.io

---

### Version 1.5.0 - Modern Plex Folder Fix (Attempted)
**Date:** 2025-10-18

**Problem:** Modern Plex uses different bundle structure
- Old: `Metadata/TV Shows/{hash}/Contents/*.jpg`
- New: `Metadata/TV Shows/{hash}/*.jpg` (no Contents folder!)

**Solution Attempted:**
- Updated scanner to check both old and new structures
- Added fallback logic for modern Plex installations

**Result:** Partial success, but ultimately led to v2.0.0 rewrite

---

### Version 1.3.0 - Artwork-Only Mode (Filesystem Scanning)
**Date:** 2025-10-18

**Approach:** Give up on database lookups, scan bundles directly
- Discovered bundle hashes are NOT in Plex database
- Switched to visual identification via thumbnails
- Users identify shows by seeing the artwork itself

**Why This Was Replaced:**
- Worked temporarily but broke when Plex changed folder structure
- v2.0.0 API approach is more robust and professional

---

### Versions 1.0.0 - 1.2.2 - Initial Development
**Dates:** 2025-10-17 to 2025-10-18

**Key Learnings:**
- Windows Unicode encoding issues (use ASCII only!)
- Flask auto-reload breaks stdout wrappers
- Import order matters (BytesIO shadowing)
- Bundle hashes not in Plex database
- Filesystem scanning is fragile

---

## 🔧 Technical Learnings

### 1. Why Filesystem Scanning Failed
**Problem:** Plex bundle structure changes between versions
- Old Plex: `{hash}/Contents/*.jpg`
- New Plex: `{hash}/*.jpg`
- Future Plex: ???

**Solution:** Use the API, it doesn't change!

---

### 2. Professional Approach = Plex API
**Discovery:** All professional Plex tools use python-plexapi
- Kometa (Plex Meta Manager)
- Tautulli (Plex monitoring)
- JBOPS (Plex scripts)

**Lesson:** Follow the professionals, not the easy path

---

### 3. Windows Compatibility
**Issue:** Windows console (cp1252) can't display Unicode
**Solutions Tried:**
- ❌ TextIOWrapper: Breaks Flask auto-reload
- ✅ ASCII symbols: [OK] and [X] instead of ✓ and ✗

**Rule:** Always use ASCII symbols in print statements!

---

### 4. Plex Token is Now Required
**v1.x:** Token was optional (filesystem scanning didn't need it)
**v2.0+:** Token is REQUIRED (API authentication)

**How to Get Token:**
1. Sign in to Plex Web
2. Go to Settings → Account
3. Click "Get Token" or use: https://www.plexopedia.com/plex-media-server/general/plex-token/

---

## 💻 Development Commands

### Setup (First Time)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Running Manually
```bash
# Backend (Terminal 1)
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py

# Frontend (Terminal 2)
cd frontend
npm start
```

### Running via GUI Launcher (Recommended)
```bash
python launcher_gui.py
```

Then:
1. Configure Plex URL (e.g., `http://localhost:32400`)
2. Enter your Plex token (required!)
3. Check "Auto-start servers on launch" (optional)
4. Click "Save Configuration"
5. Click "▶ Launch Servers"

---

## 📡 API Endpoints Reference

### Configuration
- GET /api/config - Get current configuration
- POST /api/config - Update configuration (plex_url, plex_token)
- GET /api/detect-url - Auto-detect Plex server URL
- POST /api/test-token - Test Plex token validity (REQUIRED)

### Library Scanning
- GET /api/libraries - Get available Plex libraries
- POST /api/scan - Scan library for items and artwork via API
- POST /api/search - Search for items by title
- POST /api/duplicates - Find duplicate artwork

### Artwork Management
- GET /api/thumbnail?url=<plex_url> - Get thumbnail from Plex API
- POST /api/delete - Delete artwork files
- POST /api/undo - Undo deletion operation

---

## 📝 Important Notes for Future Development

**If you're working on this project:**

1. **Current Status: v2.0.1 - PRODUCTION READY**
   - Uses Plex API (professional approach)
   - Plex token REQUIRED
   - Auto-start feature available

2. **NEVER suggest filesystem scanning**
   - We tried it (v1.0 - v1.5)
   - It breaks when Plex updates
   - Always use Plex API

3. **Windows Compatibility Rules:**
   - Use ASCII symbols only ([OK], [X])
   - No UTF-8 TextIOWrapper (breaks Flask reload)
   - Test on Windows before committing

4. **Plex Token is Required**
   - Not optional anymore
   - Needed for API authentication
   - Test token validation before scanning

5. **Key Files:**
   - backend/plex_scanner_api.py - Plex API scanner (NEW in v2.0)
   - backend/app.py - Flask API (updated for v2.0)
   - launcher_gui.py - GUI launcher (auto-start in v2.0.1)

6. **Testing Checklist:**
   - ✅ Connect to Plex server with token
   - ✅ List available libraries
   - ✅ Scan library and retrieve artwork
   - ✅ Display thumbnails from Plex URLs
   - ✅ Delete artwork (with backup)
   - ✅ Undo deletion

---

## 🔗 Repository
https://github.com/ButtaJones/plex-poster-manager

**End of Context Document**
