# Plex Poster Manager v2.2.0-dev - Windows Testing Report

**Date:** October 21, 2025
**Tester:** Windows Machine Setup
**Platform:** Windows 10 Build 19045.6456
**Python:** 3.10.0
**Node.js:** v25.0.0

---

## Setup Status: ✅ SUCCESSFUL

### Backend Setup
- ✅ Virtual environment created
- ✅ All dependencies installed successfully
  - Flask 3.0.0
  - PlexAPI 4.15.16 (critical for v2.2.0-dev)
  - Pillow 10.4.0
  - customtkinter 5.2.2
- ✅ Backend server starts without errors
- ✅ Health check passes

### Frontend Setup
- ✅ npm install completed (1326 packages)
- ✅ No blocking errors
- ⚠️ 9 dev-dependency vulnerabilities (non-critical, safe for local dev)

### Plex Connection
- ✅ Plex Media Server running (v1.42.1.10060)
- ✅ Token authentication successful
- ✅ Libraries detected: 14 libraries found
  - TV Shows: 2,262 items
  - TV Shows 4K: 52 items
  - Movies: 6,596 items
  - Movies 4K: 161 items
  - Plus 10 other libraries

### Configuration
- ✅ config.json created with:
  - plex_url: http://localhost:32400
  - plex_token: [valid token provided]
  - backup_directory: ./backups
  - backup_retention_days: 7

---

## 🐛 CRITICAL BUG DISCOVERED: Scan Logic File Extension Issue

### Bug Description
The scan feature returns 0 items even when custom artwork exists in Uploads folders.

### Root Cause
**File:** `backend/plex_scanner_api.py`
**Method:** `_get_uploads_file_count()` (lines 467-468)

```python
# Current code only looks for files with extensions:
for ext in ['*.jpg', '*.jpeg', '*.png']:
    files = list(uploads_dir.glob(ext))
```

### The Problem
Plex stores uploaded artwork files **WITHOUT file extensions**. Example real files found:

```
/Metadata/TV Shows/.../Uploads/posters/c3074109ac427681678c1ec6ade63183352d698c
/Metadata/TV Shows/.../Uploads/art/com.plexapp.agents.localmedia_588db8ddecd019f1b5d71d14b25258dc06bdd088
```

File type verification:
```
$ file c3074109ac427681678c1ec6ade63183352d698c
JPEG image data, Exif standard, progressive, precision 8, 360x540, components 3
Size: 144 KB
```

These are valid JPEG images but have NO .jpg extension.

### Impact
- ❌ Scan returns 0 items with artwork
- ❌ Users cannot see what can be deleted
- ❌ Smart filtering is too aggressive
- ⚠️ Delete function likely has the same bug (uses same glob pattern)

### Evidence
**Test Command:**
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"library_name": "TV Shows", "limit": 500}'
```

**Result:**
```json
{
    "items": [],
    "stats": {
        "limit": 500,
        "total_items": 0,
        "total_artwork": 0,
        "total_count": 2262
    },
    "success": true,
    "warning": "No items with artwork found..."
}
```

**Manual Verification:**
```bash
$ find "/c/Users/butta/AppData/Local/Plex Media Server/Metadata/TV Shows" \
    -type d -name "Uploads" | wc -l
# Result: Multiple Uploads folders found

$ ls "/Metadata/TV Shows/0/0141c23da2b741b8e6e2c812b3f783965e36468.bundle/Uploads/"
art/
posters/

$ find ".../Uploads/" -type f
.../Uploads/art/com.plexapp.agents.localmedia_588db8ddecd019f1b5d71d14b25258dc06bdd088
.../Uploads/posters/c3074109ac427681678c1ec6ade63183352d698c
.../Uploads/posters/seasons/1/com.plexapp.agents.thetvdb_7469798e2a58ebc1a305846f3608c96892abe54b
```

**Conclusion:** Files exist, but scan doesn't find them due to missing extensions.

---

## 🔧 RECOMMENDED FIX

### Option 1: Look for all files (Recommended)
```python
# In _get_uploads_file_count() method:
for subfolder in ['posters', 'art', 'backgrounds', 'banners', 'themes']:
    subfolder_path = uploads_dir / subfolder
    if subfolder_path.exists():
        # Get ALL files, not just specific extensions
        files = [f for f in subfolder_path.iterdir() if f.is_file()]
        file_count += len(files)

        # Optionally: Filter by checking if they're valid images
        # import imghdr
        # files = [f for f in files if imghdr.what(f) in ['jpeg', 'png', 'gif']]
```

### Option 2: Check file type instead of extension
```python
import imghdr

for subfolder in ['posters', 'art', 'backgrounds', 'banners', 'themes']:
    subfolder_path = uploads_dir / subfolder
    if subfolder_path.exists():
        for file_path in subfolder_path.iterdir():
            if file_path.is_file():
                # Check if it's an image file
                if imghdr.what(file_path) in ['jpeg', 'png', 'gif']:
                    file_count += 1
```

### Option 3: Glob for all files
```python
# Simple: just look for any file
for subfolder in ['posters', 'art', 'backgrounds', 'banners', 'themes']:
    subfolder_path = uploads_dir / subfolder
    if subfolder_path.exists():
        files = list(subfolder_path.glob('*'))  # All files
        files = [f for f in files if f.is_file()]  # Exclude directories
        file_count += len(files)
```

---

## Testing Summary

### ✅ What Works
1. Backend setup and installation
2. Frontend setup and installation
3. Plex connection and authentication
4. PlexAPI integration
5. Library detection
6. Configuration management

### ❌ What Doesn't Work
1. **Scan feature** - Returns 0 items due to file extension bug
2. **Delete feature** - Likely has same bug (not tested yet due to scan issue)

### ⏳ Not Yet Tested
1. Actual file deletion
2. Disk space reporting
3. Backup creation
4. Backup restoration
5. Empty trash functionality
6. Frontend UI (server not launched yet)

---

## Recommendations for Development Team

### Priority 1: Fix File Extension Bug
- Update `_get_uploads_file_count()` to find files without extensions
- Update `delete_artwork()` to use same logic
- Test with real Plex metadata that has no extensions

### Priority 2: Add Debug Logging
- Add option to print ALL files found in Uploads folders
- Show which files are being skipped and why
- Make it easier to diagnose scan issues

### Priority 3: Update Documentation
- Document that Plex stores files without extensions
- Add troubleshooting guide for "0 items found"
- Include manual verification steps

### Priority 4: Add Frontend Testing
- The backend works, but frontend UI hasn't been tested
- Need to verify React app displays results correctly
- Test thumbnail loading and selection

---

## Next Steps for Testing

Once the scan bug is fixed:
1. Re-test scan with various limits (100, 500, all)
2. Test delete functionality
3. Verify backups are created before deletion
4. Verify disk space is actually freed
5. Test empty trash feature
6. Test undo functionality
7. Launch frontend and test full UI workflow

---

## Files for Reference

**Uploads Folder Example:**
```
C:\Users\butta\AppData\Local\Plex Media Server\Metadata\TV Shows\0\0141c23da2b741b8e6e2c812b3f783965e36468.bundle\Uploads\
├── art\
│   └── com.plexapp.agents.localmedia_588db8ddecd019f1b5d71d14b25258dc06bdd088 (JPEG, no ext)
└── posters\
    ├── c3074109ac427681678c1ec6ade63183352d698c (JPEG, 144KB, no ext)
    └── seasons\
        └── 1\
            └── com.plexapp.agents.thetvdb_7469798e2a58ebc1a305846f3608c96892abe54b (JPEG, no ext)
```

**Backend Log Excerpt:**
```
[PlexScannerAPI] Connected to: BFLlX
[PlexScannerAPI] Version: 1.42.1.10060-4e8b05daf
[PlexScannerAPI] Platform: Windows
[get_libraries] TV Shows: 2262 items
[API /api/scan] Scanning library: TV Shows, limit: 500
[Result] 0 items with artwork found
```

---

## Contact & Environment Info

**Testing Environment:**
- OS: Windows 10.0.19045
- Plex Server: 1.42.1.10060-4e8b05daf
- Python: 3.10.0
- PlexAPI: 4.15.16
- Git Branch: dev
- Project Version: v2.2.0-dev

**Tester Notes:**
This is a clean Windows installation with real Plex data. The bug is reproducible 100% of the time with current code. The fix should be straightforward - just need to update the file glob pattern to include files without extensions.
