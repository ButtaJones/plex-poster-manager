# Plex Poster Manager - Debugging Guide

## Critical Bug Fixes Applied (Latest Session)

### 1. ✅ Windows Path Scanning - FIXED
**Problem:** Scan returns 0 items even with valid Windows Plex path

**Root Cause:**
- Scanner was looking for `Metadata/TV Shows` when user provided `C:\Users\butta\AppData\Local\Plex Media Server\Metadata`
- No logging to debug what was happening
- Path validation was too strict

**Fixes Applied:**
- Added extensive logging throughout `plex_scanner.py`
- Enhanced path validation to handle direct library paths
- Added fallback logic if metadata path itself is the library directory
- Detailed directory listing in logs
- Bundle counting and processing logs

**How to Debug:**
1. Start the backend server
2. Watch the console output for these log messages:
   ```
   [PlexScanner] Initialized with path: C:\Users\...
   [PlexScanner] Path exists: True/False
   [validate_path] Directory contents: (lists all subdirectories)
   [find_bundles] Looking for bundles in library: 'TV Shows'
   [find_bundles] Total bundles found: X
   [scan_library] Starting scan...
   [scan_library] Results summary: (detailed stats)
   ```

3. Check the logs to see:
   - Does the path exist?
   - What subdirectories are found?
   - How many .bundle folders are found?
   - Are Info.xml files being parsed?
   - Are artwork files being detected?

**Expected Path Structures:**
- If you provide: `C:\Users\...\Plex Media Server\Metadata`
  - Scanner looks for: `Metadata\TV Shows\`
- If you provide: `C:\Users\...\Plex Media Server\Metadata\TV Shows`
  - Scanner scans that directory directly

---

### 2. ✅ Plex Token API Error - FIXED
**Problem:** "Expecting value: line 1 column 1 (char 0)" when testing token

**Root Cause:**
- Plex API was returning non-JSON response
- No Content-Type checking
- Poor error handling

**Fixes Applied:**
- Added `Accept: application/json` header
- Check response Content-Type before parsing
- Added detailed logging of response status, headers, and content
- Better error messages for JSON parsing failures
- Separate timeout handling

**How to Debug:**
1. Test a token in the GUI launcher or via API
2. Check backend console for:
   ```
   [test-token] Testing token: ab12cd34ef...
   [test-token] Response status: 200/401
   [test-token] Response headers: {...}
   [test-token] Response text: (first 200 chars)
   ```

3. Common issues:
   - Status 401: Invalid token
   - Status 200 but not JSON: Plex API changed format
   - Timeout: Network/firewall issue

---

### 3. ✅ Empty Scan Results - IMPROVED ERROR MESSAGES
**Problem:** Scan completes but shows 0 items with no explanation

**Fixes Applied:**
- API now returns a `warning` field when no items found
- Helpful checklist:
  1. Path contains .bundle folders
  2. Path is correct and accessible
  3. The library exists at this location
  4. Metadata folders contain artwork files
- Enhanced logging in backend console
- Frontend should display warning message (if implemented)

**How to Debug Empty Scans:**

1. **Check if path is correct:**
   ```
   # In backend console, look for:
   [validate_path] Directory contents:
     - TV Shows (dir)
     - Movies (dir)
   ```

2. **Check bundle discovery:**
   ```
   [find_bundles] Total bundles found: 0  ← PROBLEM!
   ```
   If 0 bundles found:
   - Navigate to the path in Windows Explorer
   - Look for folders ending in `.bundle`
   - Example: `The Office (US).bundle`

3. **Check if bundles have artwork:**
   ```
   [scan_library] Found 0 artwork files  ← No artwork!
   ```
   Inside each .bundle folder, check for:
   - `Posters/` folder
   - `Art/` folder
   - `Backgrounds/` folder
   - Must contain .jpg, .png files

4. **Check bundle structure:**
   A typical bundle looks like:
   ```
   The Office (US).bundle/
   ├── Contents/
   │   └── Info.xml       ← Must exist!
   ├── Posters/
   │   └── some_poster.jpg
   └── Art/
       └── some_art.jpg
   ```

---

## Common Issues and Solutions

### Issue: "No items found" after scan

**Possible Causes:**
1. **Wrong path provided**
   - Check: Is this the `Metadata` folder or `Metadata\TV Shows` folder?
   - Solution: Try both paths

2. **No .bundle folders**
   - Check: Open the path in Explorer, do you see .bundle folders?
   - Solution: You may need to scan your Plex library first

3. **Bundles don't have artwork**
   - Check: Open a .bundle folder, do you see Posters/Art folders?
   - Solution: This is normal for shows without custom artwork

4. **Permission issues**
   - Check: Can you read the files in Explorer?
   - Solution: Run the app as Administrator (Windows)

5. **Path encoding issues**
   - Check: Does the path contain special characters?
   - Solution: Try using forward slashes: `C:/Users/...`

### Issue: Port 3000 already in use

**Cause:** Another React app or service is using port 3000

**Solution 1 - Kill existing process (Windows):**
```cmd
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

**Solution 2 - Use different port:**
Edit `frontend/package.json`:
```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

### Issue: Backend shows correct path but scan finds nothing

**Debug Steps:**
1. Stop backend server
2. Start with: `python backend/app.py`
3. Trigger a scan
4. Read ALL console output carefully
5. Look for the [find_bundles] and [scan_library] messages

**Common causes:**
- Path is correct but points to wrong library (Movies vs TV Shows)
- Plex hasn't created metadata yet (scan library in Plex first)
- Bundle folders are empty (Plex is still downloading metadata)

---

## Testing Checklist

Before reporting "scan not working":

- [ ] Backend console shows path exists: `Path exists: True`
- [ ] Backend console shows directory contents (should see TV Shows/Movies)
- [ ] Backend console shows bundles found: `Total bundles found: > 0`
- [ ] Opened path in Windows Explorer - can see .bundle folders
- [ ] Opened a .bundle folder - can see Posters/ or Art/ folders
- [ ] Posters/Art folders contain .jpg or .png files
- [ ] No permission errors in console
- [ ] Backend is actually running (check http://localhost:5000/api/health)

---

## Log File Locations

**Backend logs:** Console output (not saved to file by default)
**Frontend logs:** Browser DevTools Console (F12)
**Config file:** `config.json` in project root

---

## Getting Help

When reporting issues, please provide:
1. **Full console output** from backend during scan
2. **Screenshot** of directory structure in Windows Explorer
3. **Config.json** contents (remove token if present)
4. **Browser console errors** (F12 → Console tab)
5. **Exact path** you configured

---

## Known Limitations

1. **Scanner only finds items with artwork**
   - Empty bundles won't show up
   - This is by design (no artwork = nothing to manage)

2. **Large libraries may take time to scan**
   - 100+ shows can take 30-60 seconds
   - Watch console for progress

3. **Network drives may be slow**
   - UNC paths: `\\server\share\...`
   - May timeout on slow networks

4. **Plex must have metadata downloaded**
   - Newly added shows won't appear until Plex downloads metadata
   - Force metadata refresh in Plex first

---

**Last Updated:** Oct 17, 2025
**Version:** 1.1.0 (Bug Fix Release)
