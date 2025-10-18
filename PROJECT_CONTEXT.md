# Plex Poster Manager - Project Context

**Last Updated:** 2025-10-18
**Current Version:** 1.2.2
**Status:** Backend Working, Hash Format Mismatch Investigation (BLOCKING)

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

### Hash Format Mismatch - Bundle vs Database

**CRITICAL DISCOVERY:**
- Bundle folder names: **41 characters** (e.g., `0141c23da2b741b8e6e2c812b3f783965e36468`)
- Database hash field: **40 characters** (e.g., `4c8efc880b76c2ed0d32774bf03455f7ff6baa3e`)
- **THE FORMATS ARE DIFFERENT!** Bundle hash ≠ metadata_items.hash

**Root Cause:**
The bundle folder name is NOT directly stored in `metadata_items.hash`.
Plex likely uses a relational chain:
```
metadata_items (id, title, hash)
  -> media_items (metadata_item_id)
    -> media_parts (media_item_id, file path containing bundle hash)
```

**Current Investigation (v1.2.2):**
Debug tooling added to inspect:
1. `media_items` table schema
2. `media_parts` table schema
3. Sample `media_parts` rows (file paths)
4. Search for bundle hash in `media_parts.file` column
5. Fallback: Partial hash matching

**Next Steps:**
1. User pulls latest code (commit 7838e0a)
2. Backend starts and auto-runs debug_database()
3. User sends console output showing:
   - Table schemas
   - Sample file paths from media_parts
   - Whether bundle hashes appear in file paths
4. We identify correct table and column for mapping
5. Implement proper bundle → metadata lookup

---

## 📚 Version History & Bug Fixes

### Version 1.2.2 (Current) - Hash Investigation + Unicode Fix
**Date:** 2025-10-18

**Critical Discovery:**
- Bundle folder names are 41 chars, database hashes are 40 chars
- Bundle hash ≠ metadata_items.hash (different formats!)
- Need to investigate media_parts table for file path mapping

**Changes:**
1. **Unicode Crash Fix (Again!)**
   - Fixed remaining Unicode symbols in debug_database()
   - → (arrow) → `->` (ASCII)
   - ✓ and ✗ → `[OK]` and `[X]` (ASCII)

2. **Comprehensive Table Investigation**
   - Added media_items table inspection
   - Added media_parts table inspection
   - Sample file paths from media_parts (likely contain bundle hashes)
   - Search for bundle hash in file paths
   - Partial hash matching fallback

**Why:** Need to understand how Plex maps bundle folders to metadata titles

---

### Version 1.2.1 - Initial Debug Tooling
**Date:** 2025-10-18

**Changes:**
- Added debug_database() method to plex_scanner.py
- Inspects metadata_items table schema
- Shows sample TV show hashes
- Compares bundle folder names with database hashes
- Revealed the hash format mismatch!

---

### Version 1.1.3 - ASCII Symbol Fix
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
2. **Current blocking issue:** Hash format mismatch - bundle folders (41 chars) ≠ database hashes (40 chars)
3. **Don't suggest UTF-8 TextIOWrapper** - Already tried, breaks Flask auto-reload
4. **ALWAYS use ASCII symbols** - [OK] and [X], not ✓ and ✗ (Windows cp1252 crashes!)
5. **Plex token is optional** - Don't focus on token errors
6. **User is on Windows** - Test/debug Windows-specific issues
7. **Check git log** - See recent commits for latest changes
8. **Modern Plex architecture:**
   - Metadata in SQLite database: `com.plexapp.plugins.library.db`
   - Artwork in filesystem bundles: `.bundle` folders
   - Bundle hash mapping: Under investigation (v1.2.2)

**Key Files:**
- backend/plex_scanner.py - Database integration + bundle scanning (critical!)
- backend/app.py - Flask API (working)
- launcher_gui.py - GUI launcher (working)

**Current Focus:**
Waiting for user's debug output to reveal how media_parts table maps bundle folders to metadata_items.

---

## 🔗 Repository
https://github.com/ButtaJones/plex-poster-manager

**End of Context Document**
