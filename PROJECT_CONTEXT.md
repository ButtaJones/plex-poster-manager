# Plex Poster Manager - Project Context

**Last Updated:** 2025-10-18
**Current Version:** 1.1.3
**Status:** Backend Working, Info.xml Parsing Issue (BLOCKING)

---

## 📋 Project Overview

### Goal
Web application to manage Plex Media Server artwork files. Users can browse, view, and delete posters, backgrounds, and other artwork from their Plex metadata bundles.

### Architecture
- **Backend:** Flask (Python 3.8+) REST API
- **Frontend:** React 18.2 with Tailwind CSS
- **Deployment:**
  - **Development:** macOS (developer machine)
  - **Production:** Windows (where Plex Media Server runs)
  - **Challenge:** Cross-platform compatibility issues (Windows encoding)

### Key Components
1. **backend/app.py** - Flask REST API server
2. **backend/plex_scanner.py** - Scans Plex metadata bundles, parses Info.xml
3. **backend/file_manager.py** - Handles file operations and backups
4. **frontend/** - React web interface
5. **launcher_gui.py** - Tkinter GUI for one-click server management

---

## 🚨 CURRENT BLOCKING ISSUE

### Info.xml Parsing Returns 0 Results

**Problem:**
- Backend starts successfully ✅
- Scan finds 2724 bundles ✅
- HTTP 200 response ✅
- **BUT:** 0 items returned to frontend ❌
- All bundles being skipped (no valid Info.xml found)

**Evidence:**
```
[scan_library] Found 2724 bundles to process
[scan_library] Results summary:
  - Total bundles scanned: 2724
  - Bundles without Info.xml: 2724  ← PROBLEM!
  - Bundles with artwork (returned): 0
```

**What We're Checking:**
```python
candidates = [
    bundle_path / "Contents" / "Info.xml",
    bundle_path / "Info.xml",
    bundle_path / "Contents" / "_combined" / "Info.xml",
    bundle_path / "Contents" / "com.plexapp.agents.thetvdb" / "Info.xml",
    bundle_path / "Contents" / "com.plexapp.agents.themoviedb" / "Info.xml"
]
```

**Current Debug Status:**
- Enhanced logging added (v1.1.3)
- Shows bundle contents for first 5 failed bundles
- Will reveal actual directory structure
- Need user to run scan and report console output

**Next Steps:**
1. User runs scan on Windows
2. Send console output showing bundle directory structure
3. Identify where Info.xml actually lives
4. Add correct paths to candidates list

---

## 📚 Version History & Bug Fixes

### Version 1.1.3 (Current) - ASCII Symbol Fix
**Date:** 2025-10-18

**Changes:**
- Removed UTF-8 TextIOWrapper (caused Flask reload crashes)
- Replaced all Unicode symbols with ASCII:
  - ✓ → [OK]
  - ✗ → [X]
- Enhanced debugging for Info.xml parsing failures
- Shows bundle directory structure when parsing fails

**Why:** TextIOWrapper incompatible with Flask debug mode auto-reload

---

### Version 1.1.2 - Critical Windows Fixes
**Date:** 2025-10-18

**Critical Bugs Fixed:**
1. **Import Order Crash**
   - Problem: from io import BytesIO then import io shadowed BytesIO
   - Backend crashed before Flask could start
   - Frontend showed: "Network Error" (ECONNREFUSED)
   - Fix: Moved sys and io imports to top, use io.BytesIO()

2. **Windows Unicode Encoding Error**
   - Problem: UnicodeEncodeError on Windows (cp1252 encoding)
   - Print statements with ✓ and ✗ caused 500 errors
   - Blocked: Config save, library scan, ALL functionality
   - Fix: Added UTF-8 TextIOWrapper for Windows console
   - **Later reverted:** See v1.1.3 (TextIOWrapper caused reload issues)

3. **I/O Operation on Closed File**
   - Problem: TextIOWrapper file handle closed on Flask reload
   - Backend crashed with: ValueError: I/O operation on closed file
   - Fix: Replaced UTF-8 wrapper with ASCII symbols (v1.1.3)

---

### Version 1.1.1 - First-Time User Experience
**Date:** 2025-10-18

**Improvements:**
1. **Auto-Setup for GitHub Users**
   - Detects missing dependencies automatically
   - One-click installation: venv + pip + npm
   - Shows progress in launcher GUI log

2. **API Error Logging**
   - /api/detect-path: Comprehensive error logging
   - /api/config POST: Detailed logging for debugging
   - Better error messages for configuration issues

3. **Plex Token Optional Messaging**
   - Help text: "ℹ️ Not required - app works without it"
   - Explains what token enables
   - Reduces user confusion

4. **Quick Start Guide**
   - Prominent README section for GitHub users
   - 4-step setup process with automatic installation
   - Updated version badge to 1.1.0

---

### Version 1.0.0 - Initial Release
**Date:** 2025-10-17

**Features Built:**
- Flask REST API backend with Plex metadata scanning
- React frontend with Tailwind CSS
- Plex bundle scanner and Info.xml parser
- File manager with backup system
- Auto-detect Plex metadata path
- GUI launcher with tkinter
- Cross-platform support (Windows, macOS, Linux)

---

## 🔧 Technical Learnings

### 1. Windows Unicode Encoding
**Problem:** Windows console (cp1252) can't display Unicode characters
**Solutions Tried:**
- ❌ TextIOWrapper: Works but breaks Flask auto-reload
- ✅ ASCII symbols: Simple, reliable, 100% compatible

**Key Insight:** Sometimes the simplest solution is the best solution.

---

### 2. Flask Debug Mode Auto-Reload
**Issue:** Flask watchdog restarts process on file changes
**Impact:** File handles (like TextIOWrapper) get closed
**Solution:** Avoid wrapping stdout/stderr, use ASCII instead

---

### 3. Import Order Matters
**Issue:** from io import BytesIO then import io shadows BytesIO
**Impact:** Backend crashes with NameError when using BytesIO()
**Solution:** Import full module first, use qualified names (io.BytesIO())

---

### 4. Plex Token Confusion
**Issue:** Users think token is required
**Reality:** Token is 100% optional for core functionality
**Solution:** Clear help text and "optional" labels everywhere

**Without token (works perfectly):**
- Scans metadata files from disk
- Manages artwork
- Deletes files
- All core functionality

**With token (nice-to-have):**
- API verification
- Future Plex API features
- Not implemented yet

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

### Testing Backend Import
```bash
cd backend
source venv/bin/activate
python -c "import app; print('Import successful!')"
```

---

## 📡 API Endpoints Reference

### Configuration
- GET /api/config - Get current configuration
- POST /api/config - Update configuration
- GET /api/detect-path - Auto-detect Plex metadata path
- POST /api/test-token - Test Plex token validity (optional)

### Library Scanning
- GET /api/libraries - Get available Plex libraries
- POST /api/scan - Scan library for items and artwork
- POST /api/search - Search for items by title
- POST /api/duplicates - Find duplicate artwork

### Artwork Management
- GET /api/thumbnail?path=<path> - Get thumbnail image
- POST /api/delete - Delete artwork files
- POST /api/undo - Undo deletion operation

---

## 📝 Note for Future Claude Sessions

**If you're a new Claude session helping with this project:**

1. **Read this file first** - It contains all critical context
2. **Current blocking issue:** Info.xml parsing returns 0 results
3. **Don't suggest UTF-8 TextIOWrapper** - Already tried, breaks Flask auto-reload
4. **Use ASCII symbols** - [OK] and [X] instead of Unicode
5. **Plex token is optional** - Don't focus on token errors
6. **User is on Windows** - Test/debug Windows-specific issues
7. **Check git log** - See recent commits for latest changes

**Key Files:**
- backend/plex_scanner.py - Info.xml parsing (issue here)
- backend/app.py - Flask API (working)
- launcher_gui.py - GUI launcher (working)

---

## 🔗 Repository
https://github.com/ButtaJones/plex-poster-manager

**End of Context Document**
