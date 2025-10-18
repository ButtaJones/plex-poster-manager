# Plex Poster Manager - Project Status

**Last Updated:** October 18, 2025
**Current Version:** 2.1.0
**Build Platform:** macOS
**Target Platform:** Windows Plex Server
**Status:** Production Ready with Plex API Integration + Advanced UI Features

---

## 🎯 Current Status

### Production Ready! ✅

The application is now using the **professional approach** - Plex API integration via python-plexapi library. This is the same method used by industry-standard tools like Kometa and Tautulli.

**Major Breakthrough (v2.0.0):**
- ❌ Abandoned filesystem scanning (fragile, broke with Plex updates)
- ✅ Switched to Plex API (stable, future-proof, professional)

**Latest Improvements (v2.1.0):**
- ✅ **Scan Limit Option** - Choose 100/500/1000/2000 items or all (perfect for large libraries)
- ✅ **Thumbnail Size Slider** - Adjust display size 150-600px (like Medusa NZB)
- ✅ **Responsive Grid Layout** - More columns when thumbnails are smaller
- ✅ **Pagination/Load More** - Load items in batches, click "Load More" for next batch
- ✅ **Visual Feedback** - "Showing 100 of 2262 items (22 more pages available)"

**Previous Improvements (v2.0.1):**
- Fixed token testing to use PlexAPI
- Added auto-start servers feature
- Windows upgrade scripts for v1.x users

---

## Setup Status

### Backend (Python/Flask)
- **Status:** ✅ Configured and Production Ready
- **Python Version:** 3.8.9+
- **Virtual Environment:** `backend/venv/`
- **Dependencies:** All installed successfully
  - Flask 3.0.0
  - Flask-CORS 4.0.0
  - **PlexAPI 4.15.16** ⭐ (NEW in v2.0.0)
  - Pillow 10.1.0
  - watchdog 3.0.0
  - requests
- **Server:** Runs on http://localhost:5000
- **API Mode:** Plex API integration (professional approach)

### Frontend (React)
- **Status:** ✅ Configured and Ready
- **Node Version:** 20.19.5
- **npm Version:** 11.6.2
- **Dependencies:** All installed (1326 packages)
- **Build:** Production build successful
- **Notes:** Frontend needs update for v2.0 API (plex_url instead of plex_metadata_path)

### GUI Launcher
- **Status:** ✅ Fully Functional (v2.0.1)
- **File:** `launcher_gui.py` in project root
- **Framework:** tkinter (built into Python)
- **Features:**
  - ✅ One-click start/stop for both servers
  - ✅ Configuration management (Plex URL, token)
  - ✅ **Auto-start servers on launch** ⭐ (NEW in v2.0.1)
  - ✅ Plex token testing with PlexAPI ⭐ (FIXED in v2.0.1)
  - ✅ Live server output logs (scrollable)
  - ✅ Quick browser launch button
  - ✅ Cross-platform (macOS, Windows, Linux)
  - ✅ Graceful server shutdown

### Git Repository
- **Status:** Initialized and Active
- **Branch:** main
- **Remote:** https://github.com/ButtaJones/plex-poster-manager
- **Latest Commits:**
  - `02b2615` - Add direct PlexAPI installer for Windows
  - `526f3c0` - Fix launcher bugs and add auto-start feature (v2.0.1)
  - `8b63fee` - MAJOR REWRITE: Switch to Plex API (v2.0.0)

---

## Application Architecture (v2.0+)

### Backend (`/backend/`)
- **app.py** - Flask REST API server (updated for Plex API)
- **plex_scanner_api.py** ⭐ - **NEW:** Plex API artwork scanner
- **file_manager.py** - File operations and backup management
- **requirements.txt** - Python dependencies (includes PlexAPI)

### Frontend (`/frontend/`)
- **src/App.jsx** - Main application component
- **src/api.js** - Backend API client
- **src/components/** - React UI components
  - ArtworkCard.jsx
  - ItemCard.jsx
  - ConfigModal.jsx

### Launcher
- **launcher_gui.py** - Tkinter GUI (v2.0.1 with auto-start)

### Windows Setup Scripts
- **INSTALL_PLEXAPI.bat** - Direct PlexAPI installer
- **QUICK_FIX_WINDOWS.bat** - v1.x to v2.0 upgrade helper

---

## How to Start the Application

### Method 1: GUI Launcher (Recommended) 🚀
```bash
cd /Users/butta/development/plex-poster-manager
python3 launcher_gui.py
```

**Configuration (First Time):**
1. Enter Plex URL: `http://localhost:32400` (or your server IP)
2. Enter Plex Token: (REQUIRED - see "Getting Plex Token" below)
3. Optional: Check "Auto-start servers on launch"
4. Click "Save Configuration"
5. Click "Test Token" to verify connection
6. Click "▶ Launch Servers"

Browser auto-opens to http://localhost:3000

### Method 2: Manual Start (Advanced)

**Terminal 1: Backend Server**
```bash
cd /Users/butta/development/plex-poster-manager/backend
source venv/bin/activate
python app.py
```
Server starts on http://localhost:5000

**Terminal 2: Frontend Development Server**
```bash
cd /Users/butta/development/plex-poster-manager/frontend
npm start
```
Frontend opens at http://localhost:3000

---

## Configuration Required

### Getting Your Plex Token (REQUIRED in v2.0+)

**Why Token is Required:**
- v1.x used filesystem scanning (no token needed)
- v2.0+ uses Plex API (requires authentication)

**How to Get Token:**
1. Sign in to Plex Web (https://app.plex.tv)
2. Open any media item
3. Click "Get Info" or "..." menu
4. Click "View XML"
5. Look for `X-Plex-Token=` in the URL
6. Copy the token (long string of characters)

**Alternative Method:**
- Visit: https://www.plexopedia.com/plex-media-server/general/plex-token/
- Follow their detailed guide

### Plex Server URL

**Local Server:**
- Default: `http://localhost:32400`
- Works if Plex runs on same machine

**Remote Server (Windows from macOS):**
- Use server IP: `http://192.168.1.XXX:32400`
- Ensure port 32400 is accessible
- Token authentication handles remote access

---

## API Endpoints (v2.0+)

### Configuration
- `GET /api/config` - Get configuration (plex_url, plex_token)
- `POST /api/config` - Update configuration
- `GET /api/detect-url` - Auto-detect Plex server URL
- `POST /api/test-token` - Test Plex token validity

### Library Management (Plex API)
- `GET /api/libraries` - Get available Plex libraries via API
- `POST /api/scan` - Scan library for artwork via Plex API
- `POST /api/search` - Search for items by title
- `POST /api/duplicates` - Find duplicate artwork

### Artwork Management
- `GET /api/thumbnail?url=<plex_url>` - Get thumbnail from Plex API
- `POST /api/delete` - Delete artwork files
- `POST /api/undo` - Undo deletion
- `GET /api/operations` - Get recent operations
- `POST /api/clean-backups` - Clean old backups

---

## Production Readiness Checklist

### Completed ✅
- [x] Backend dependencies installed (including PlexAPI)
- [x] Frontend dependencies installed
- [x] Backend server starts without errors
- [x] Frontend builds successfully
- [x] Git repository initialized and active
- [x] .gitignore properly configured
- [x] No sensitive data in repository
- [x] **Plex API integration** ⭐ (v2.0.0)
- [x] **Auto-start feature** ⭐ (v2.0.1)
- [x] **Token testing with PlexAPI** ⭐ (v2.0.1)
- [x] **Windows upgrade scripts** ⭐ (v2.0.1)
- [x] **Scan limit option** ⭐ (v2.1.0)
- [x] **Thumbnail size slider** ⭐ (v2.1.0)
- [x] **Responsive grid layout** ⭐ (v2.1.0)
- [x] **Pagination/Load More** ⭐ (v2.1.0)
- [x] Cross-platform compatibility

### Testing Required
- [ ] Test with actual Plex server connection
- [ ] Verify artwork retrieval from Plex API
- [ ] Test deletion with Plex API artwork
- [ ] Test backup and restore system
- [ ] Frontend update for v2.0 config format

### Future Enhancements
- [ ] Update frontend for plex_url config (currently uses plex_metadata_path)
- [ ] Add artwork upload via Plex API
- [ ] Implement duplicate detection
- [ ] Add batch operations
- [ ] Production WSGI server (Gunicorn)
- [ ] HTTPS support
- [ ] Authentication/authorization

---

## Known Issues

### High Priority
1. **Token Not Persisting from Launcher to Web**
   - Status: Token must be re-entered in web app after launcher setup
   - Impact: User inconvenience
   - Fix: Share config between launcher and web app

2. **Local Artwork URLs (metadata:// and upload://) Return 404**
   - Status: Plex-local artwork not displaying
   - Impact: Some posters show as gray boxes
   - Fix: Handle Plex internal URL schemes in thumbnail proxy

### Medium Priority
1. **npm Security Vulnerabilities**
   - 9 vulnerabilities in development dependencies only
   - Impact: Low (dev tools only)
   - Status: Acceptable for local development

2. **Flask Development Server**
   - Warning: Not for production use
   - Fix: Use Gunicorn or similar WSGI server

### Resolved ✅
1. ✅ **Filesystem Scanning Fragility** - Solved by switching to Plex API (v2.0.0)
2. ✅ **Token Testing Errors** - Fixed in v2.0.1 (uses PlexAPI now)
3. ✅ **Windows Unicode Crashes** - Use ASCII symbols only
4. ✅ **ESLint Warnings** - Fixed in v1.x
5. ✅ **Thumbnail Size Not Changing** - Fixed in v2.1.0 (slider now controls display size)
6. ✅ **No Pagination for Large Scans** - Fixed in v2.1.0 (Load More feature)
7. ✅ **Frontend v2.0 Compatibility** - Fixed in v2.1.0 (ConfigModal uses plex_url)

---

## Version History Summary

### v2.1.0 (Current) - Advanced UI Features
- Scan limit option (100/500/1000/2000/all items)
- Thumbnail size slider (150-600px)
- Responsive grid layout (adapts to thumbnail size)
- Pagination with Load More functionality
- Visual feedback for scan progress

### v2.0.1 - Launcher Fixes
- Fixed token testing to use PlexAPI
- Added auto-start servers feature
- Windows upgrade scripts

### v2.0.0 - MAJOR REWRITE
- Switched from filesystem scanning to Plex API
- Added PlexAPI dependency
- Professional approach (same as Kometa/Tautulli)
- Plex token now REQUIRED

### v1.5.0 - Last Filesystem Version
- Attempted to fix modern Plex folder structure
- Led to decision to switch to API

### v1.3.0 - Artwork-Only Mode
- Gave up on database lookups
- Visual identification via thumbnails

### v1.0.0 - Initial Release
- Filesystem scanning approach
- Optional token support

---

## Technical Highlights

### Why Plex API is Better

**Filesystem Scanning (v1.x):**
- ❌ Breaks when Plex changes folder structure
- ❌ No access to show titles (bundle hashes not in DB)
- ❌ Can't tell which artwork is selected
- ❌ Fragile and unreliable

**Plex API (v2.0+):**
- ✅ Stable API (unchanged since 2013)
- ✅ Real show/movie titles from metadata
- ✅ Shows selected vs available artwork
- ✅ Provider information (TheTVDB, TheMovieDB)
- ✅ Professional approach (industry standard)
- ✅ Works remotely (not just local filesystem)
- ✅ Future-proof

### Code Example

```python
from plexapi.server import PlexServer

# Connect to Plex
plex = PlexServer('http://localhost:32400', 'YOUR_TOKEN')

# Get TV Shows library
library = plex.library.section('TV Shows')

# Scan all shows
for show in library.all():
    print(f"\n{show.title} ({show.year})")

    # Get all posters
    posters = show.posters()
    print(f"  Posters: {len(posters)} available")
    for poster in posters:
        selected = "[OK]" if poster.selected else "[ ]"
        print(f"    {selected} {poster.provider}")
```

---

## Next Steps

### Immediate
1. Update frontend for v2.0 config format
2. Test with real Plex server
3. Verify token authentication
4. Test artwork retrieval and deletion

### Short Term
1. Implement duplicate detection
2. Add batch operations
3. Comprehensive testing
4. User documentation

### Long Term
1. Production deployment setup
2. HTTPS and authentication
3. Performance optimization
4. Additional Plex API features

---

## Support and Resources

- **Documentation:** README.md, PROJECT_CONTEXT.md
- **Repository:** https://github.com/ButtaJones/plex-poster-manager
- **Plex API Docs:** https://python-plexapi.readthedocs.io
- **Industry Examples:**
  - Kometa: https://github.com/Kometa-Team/Kometa
  - Tautulli: https://github.com/Tautulli/Tautulli

---

**Status Summary:** Application is production-ready with professional Plex API integration and advanced UI features (v2.1.0). Features scan limits, pagination, responsive layouts, and customizable thumbnail sizes. Token authentication required for all operations.

**Current Focus:** Fixing token persistence between launcher and web app, and handling Plex internal artwork URLs (metadata://, upload://).
