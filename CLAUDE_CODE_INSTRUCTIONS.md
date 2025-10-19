# CLAUDE CODE MASTER INSTRUCTIONS
# Plex Poster Manager - Autonomous Debugging & Development

**READ THIS FILE FIRST before asking the user for information.**

---

## 🎯 PRIMARY DIRECTIVE

**ELIMINATE THE MIDDLEMAN:** You have direct access to the running application, filesystem, browser automation, and API testing. DO NOT ask the user to manually:
- Copy/paste console logs
- Take screenshots
- Describe what they see
- Run commands and send output
- Test the app manually

**Instead:** Use your tools to see, test, and fix everything yourself.

---

## 🛠️ AVAILABLE TOOLS & HOW TO USE THEM

### 1. **Playwright** (Visual/UI Debugging)
When user reports a UI issue (e.g., "0 results showing", "button doesn't work"):

**IMPORTANT: macOS Big Sur 11.7.4 Compatibility**
- Chromium 141+ requires macOS 12+ (LocalAuthenticationEmbeddedUI.framework)
- **Solution**: Use Firefox instead of Chromium on Big Sur

**IMPORTANT: Headless Mode Guidelines**
- **Default: Use headless=True** - Don't interfere with user's workspace
- **Only use headless=False when:** Debugging tests or need to see browser interactions
- Headless mode is faster and still captures screenshots perfectly

```python
# Python Playwright (WORKS on Big Sur 11.7.4)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Use Firefox for Big Sur compatibility
    # headless=True by default (don't interrupt user's work)
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()

    # Your testing code here
    page.goto('http://localhost:3000')

    # Screenshots work perfectly in headless mode
    page.screenshot(path='screenshot.png')

    browser.close()
```

**When to use headless=False:**
- First time writing/debugging a new test
- Need to visually verify browser behavior
- User specifically requests to see the browser
- Investigating why a test is failing

```javascript
// JavaScript Playwright (if using Node.js)
const { firefox } = require('playwright');  // Use firefox, not chromium

const browser = await firefox.launch({ headless: false }); // Show browser
const page = await browser.newPage();

// Capture console logs
const logs = [];
page.on('console', msg => logs.push(`[${msg.type()}] ${msg.text()}`));

// Capture network requests
const networkLog = [];
page.on('response', async response => {
  networkLog.push({
    url: response.url(),
    status: response.status(),
    body: await response.text().catch(() => 'binary')
  });
});

// Navigate and interact
await page.goto('http://localhost:3000');
await page.click('button:has-text("Scan Library")');
await page.waitForTimeout(5000);

// Check what happened
const itemCount = await page.locator('.item-card').count();
const errorMessages = await page.locator('.error').allTextContents();

// Save evidence
await page.screenshot({ path: 'debug-screenshot.png' });
console.log('Items found:', itemCount);
console.log('Console logs:', logs);
console.log('Network requests:', networkLog);

await browser.close();
```

**When to use:** ANY visual/UI issue, button clicks, form submissions, display problems

---

### 2. **Filesystem** (Direct Code/Log Access)
Read backend logs, check file structure, inspect bundles:

```javascript
// Read backend logs (if logging to file)
const backendLog = await fs.readFile('backend/app.log', 'utf8');
console.log('Last 100 lines:', backendLog.split('\n').slice(-100));

// Check actual bundle structure (Windows path)
const bundlePath = 'C:\\Users\\butta\\AppData\\Local\\Plex Media Server\\Metadata\\TV Shows';
const bundles = await fs.readdir(bundlePath);
console.log(`Total bundles: ${bundles.length}`);

// Inspect first bundle's contents
const firstBundle = bundles[0];
const bundleContents = await fs.readdir(path.join(bundlePath, firstBundle, 'Contents'));
console.log('Bundle structure:', bundleContents);

// Check for artwork
const postersPath = path.join(bundlePath, firstBundle, 'Contents', 'Posters');
const posters = await fs.readdir(postersPath).catch(() => []);
console.log(`Posters found: ${posters.length}`);
```

**When to use:** File structure issues, path problems, checking if files exist

---

### 3. **curl/fetch** (API Testing)
Test backend endpoints directly without UI:

```bash
# Test scan endpoint
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"library": "TV Shows"}' \
  -v  # verbose output

# Test config endpoint
curl http://localhost:5000/api/config

# Test thumbnail endpoint
curl http://localhost:5000/api/thumbnail?path=C:\\path\\to\\image.jpg
```

Or in JavaScript:
```javascript
const response = await fetch('http://localhost:5000/api/scan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ library: 'TV Shows' })
});

const data = await response.json();
console.log('API response:', data);
console.log('Items returned:', data.items?.length || 0);
console.log('Errors:', data.error || 'none');
```

**When to use:** Testing if backend logic works, isolating frontend vs backend issues

---

### 4. **GitHub** (Version Control)
Push fixes automatically:

```bash
git add .
git commit -m "Fix: [describe what you fixed]"
git push origin main
```

**When to use:** After confirming a fix works

---

## 🔍 DEBUGGING WORKFLOW

### ⚡ **CRITICAL: Always Test Authentication FIRST**

Before debugging ANYTHING, test if the system can authenticate:

```bash
# For Plex-based apps: TEST THE TOKEN FIRST
curl "http://192.168.5.141:32400/identity?X-Plex-Token=YOUR_TOKEN"

# Expected: 200 OK with XML response
# If 401 Unauthorized: TOKEN IS EXPIRED - get new token, don't waste time debugging other things
```

**Why this matters:**
- Expired authentication = everything breaks
- Symptoms look like: CORS errors, missing data, 404s, empty responses
- Fix time with token test: 5 minutes
- Fix time without token test: HOURS (wasted on red herrings)

**Golden Rule:** Authentication → Source → Destination
1. Can we authenticate? (token/credentials)
2. Can we reach the source? (Plex server, database, API)
3. Can we display the destination? (frontend, UI)

### When User Says: "Feature X is broken" or "I see Y issue"

**STEP 1: Reproduce the issue yourself**
```javascript
// Use Playwright to do exactly what user described
await page.goto('http://localhost:3000');
await page.click('button:has-text("Scan Library")');
const itemCount = await page.locator('.item-card').count();
console.log(`I see ${itemCount} items (user says 0)`);
```

**STEP 2: Capture all evidence**
- Console logs (Playwright: `page.on('console')`)
- Network requests (Playwright: `page.on('response')`)
- Screenshots (Playwright: `page.screenshot()`)
- Backend logs (Filesystem: read log files or console output)
- API responses (fetch/curl: test endpoints)

**STEP 3: Identify root cause**
```javascript
// Check each layer:
// 1. Does backend endpoint work?
const apiResponse = await fetch('http://localhost:5000/api/scan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ library: 'TV Shows' })
});
console.log('Backend returns:', await apiResponse.json());

// 2. Do files exist where backend expects them?
const exists = await fs.access(expectedPath).then(() => true).catch(() => false);
console.log('Files exist:', exists);

// 3. Does frontend receive the data?
// (Already captured in network logs from Playwright)
```

**STEP 4: Fix the bug**
```javascript
// Edit the file
await fs.writeFile('backend/plex_scanner.py', fixedCode);

// Tell user to restart backend
console.log('Fixed! User needs to restart backend.');
```

**STEP 5: Verify the fix**
```javascript
// Run Playwright test again (after user restarts)
await page.reload();
await page.click('button:has-text("Scan Library")');
const newItemCount = await page.locator('.item-card').count();
console.log(`After fix: ${newItemCount} items`);

if (newItemCount > 0) {
  console.log('✓ FIX CONFIRMED');
  // Commit to GitHub
  await exec('git add . && git commit -m "Fix scan returning 0 results" && git push');
} else {
  console.log('✗ FIX FAILED, investigating further...');
}
```

**STEP 6: Report to user**
Tell them:
- What was broken
- What you fixed
- That it's pushed to GitHub (if applicable)
- They should restart and test

**DO NOT ask them to test manually first - YOU already tested it with Playwright!**

---

## 📋 PROJECT-SPECIFIC CONTEXT

### Architecture
- **Backend:** Python/Flask (port 5000)
- **Frontend:** React (port 3000)
- **Launcher:** `launcher_gui.py` (starts both servers)
- **Database:** Plex's SQLite (read-only, for reference only - NOT USED FOR BUNDLE LOOKUP)

### Key Files
- `backend/plex_scanner.py` - Core scanning logic
- `backend/file_manager.py` - Deletion/backup/undo
- `frontend/src/App.jsx` - Main React component
- `frontend/src/api.js` - API client

### Important Paths (Windows Production)
- **Plex Metadata:** `C:\Users\butta\AppData\Local\Plex Media Server\Metadata`
- **TV Shows Bundles:** `C:\Users\butta\AppData\Local\Plex Media Server\Metadata\TV Shows`
- **Movies Bundles:** `C:\Users\butta\AppData\Local\Plex Media Server\Metadata\Movies`
- **Project Root (Windows):** `C:\Plex\plex-poster-manager-main`
- **Project Root (Mac):** `/Users/butta/development/plex-poster-manager`

### Bundle Structure
```
0141c23da2b741b8e6e2c812b3f783965e36468.bundle/
├── Contents/
│   ├── _combined/
│   ├── Posters/          ← Poster images here
│   │   └── 1234567890.jpg
│   ├── Art/              ← Background art here
│   └── Banners/          ← Banner images here
└── Uploads/              ← User-uploaded images
```

**CRITICAL:** Bundle folder names are SHA-1 hashes (41 chars) that do NOT exist in the Plex database. You CANNOT look up show titles from bundle names. Users identify items visually from thumbnails.

### Known Issues & Solutions

#### Issue: "Scan returns 0 results"
**Debug steps:**
1. Use Playwright to click scan and see network response
2. Use curl/fetch to test `/api/scan` directly
3. Check if `find_bundles()` finds any bundles (look for console logs)
4. Check if `get_artwork_files()` finds images in bundles
5. Verify paths are correct (Windows vs Mac)
6. Check if artwork folders exist: `Contents/Posters`, `Contents/Art`, etc.

**Common causes:**
- Empty `Contents` folders (no artwork downloaded yet)
- Wrong artwork folder names
- Path separator issues (Windows `\` vs Mac `/`)
- `get_artwork_files()` not checking correct subdirectories

#### Issue: "Images don't display"
**Debug steps:**
1. Check `/api/thumbnail` endpoint with curl
2. Verify image files exist at paths returned by scan
3. Check CORS headers in Flask
4. Check if PIL/Pillow can read the images
5. Use Playwright to see network tab for failed image requests

#### Issue: "Delete doesn't work"
**Debug steps:**
1. Test `/api/delete` endpoint with curl
2. Verify backup directory exists and is writable
3. Check file permissions
4. Use Playwright to see if delete button triggers API call

---

## ⚠️ COMMON DEBUGGING MISTAKES (LEARN FROM HISTORY)

### Mistake #1: Debugging Symptoms Instead of Root Cause
**Example from this project:**
- Symptoms: CORS errors, missing posters, 404s
- Wasted time on: Frontend URL detection, CORB headers, network configs
- **Root cause**: Expired Plex authentication token (would have found in 30 seconds with curl test)

**Lesson**: Always test authentication/credentials FIRST before debugging anything else.

### Mistake #2: Starting at the Wrong End
**Wrong order**: Frontend → Network → Backend → Source
**Right order**: Source → Backend → Network → Frontend

**Example:**
```bash
# RIGHT: Test source first
curl "http://192.168.5.141:32400/identity?X-Plex-Token=TOKEN"  # 30 seconds
# If 401: Token expired, fix immediately
# If 200: Token works, look elsewhere

# WRONG: Debug frontend first
# Spend hours on React state, API calls, CORS, etc.
# Finally discover token was expired the whole time
```

### Mistake #3: Chasing Red Herrings
**Red herrings that waste time:**
- CORS/CORB errors (usually happen AFTER successful auth)
- Network timeouts (check auth first)
- Empty responses (check auth first)
- 404 errors on thumbnails (check if source URLs are even valid)

**Rule**: If you see multiple unrelated errors, suspect authentication/credentials first.

### Mistake #4: Giving Up on Tools Too Easily
**Example**: Playwright failing on macOS Big Sur
- ❌ Gave up: "Playwright doesn't work, moving on"
- ✅ Fixed: Installed Firefox instead of Chromium (5 minutes)

**Lesson**: Most tool failures have simple fixes. Try alternatives before abandoning.

### Mistake #5: Not Using Tools at All
**Wrong approach:**
> "User says feature is broken. Let me ask them what they see."

**Right approach:**
> "User says feature is broken. Let me use Playwright to see it myself in 30 seconds."

---

## 🚫 WHAT NOT TO DO

❌ **DON'T ask user to:**
- "Can you send me the console logs?"
- "What do you see when you click X?"
- "Take a screenshot of Y"
- "Run this command and send output"
- "Check if file Z exists"

✅ **DO instead:**
- Use Playwright to see what they see
- Read logs with Filesystem (if logged to file)
- Test commands yourself
- Check if files exist with Filesystem

❌ **DON'T guess or assume**
✅ **DO verify with tools**

❌ **DON'T ask user to test fixes**
✅ **DO test with Playwright first, then tell them it works**

---

## 🎯 AUTOMATION SCRIPTS

### Quick Debug Script Template
```javascript
// Save as: tests/debug-scan.js
const { chromium } = require('playwright');
const fs = require('fs').promises;

async function debugScan() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Capture everything
  const logs = [];
  const networkRequests = [];
  
  page.on('console', msg => logs.push(`[${msg.type()}] ${msg.text()}`));
  page.on('response', async response => {
    networkRequests.push({
      url: response.url(),
      status: response.status(),
      body: await response.text().catch(() => 'binary')
    });
  });
  
  // Test the scan flow
  await page.goto('http://localhost:3000');
  await page.screenshot({ path: 'debug-1-loaded.png' });
  
  await page.click('button:has-text("Scan Library")');
  await page.waitForTimeout(5000);
  
  const itemCount = await page.locator('.item-card').count();
  await page.screenshot({ path: 'debug-2-after-scan.png' });
  
  // Save evidence
  await fs.writeFile('debug-logs.json', JSON.stringify({ logs, networkRequests }, null, 2));
  await fs.writeFile('debug-summary.txt', `
Items displayed: ${itemCount}
Total console logs: ${logs.length}
Total network requests: ${networkRequests.length}
  `.trim());
  
  console.log(`✓ Debug complete`);
  console.log(`  Items found: ${itemCount}`);
  console.log(`  Logs: debug-logs.json`);
  console.log(`  Screenshots: debug-1-loaded.png, debug-2-after-scan.png`);
  
  await browser.close();
  
  return { itemCount, logs, networkRequests };
}

debugScan().catch(console.error);
```

**Usage:** Run this whenever user reports visual/UI issues instead of asking for screenshots.

---

## 🔄 CONTINUOUS IMPROVEMENT

After each fix:
1. ✅ Test with Playwright
2. ✅ Commit to GitHub with clear message
3. ✅ Update this document if new patterns emerge
4. ✅ Add issue to "Known Issues" section if recurring

---

## 📞 WHEN TO INVOLVE USER

**Only ask user when:**
- You need a decision (UX choice, feature priority)
- You need authentication/credentials
- Something requires physical action (restart server if you can't automate it)
- You've tried everything and genuinely need human insight

**For 95% of bugs:** Fix autonomously using tools above.

---

## 🎓 LEARNING FROM THIS PROJECT

### What We Discovered:
1. **Modern Plex (2024+) doesn't use Info.xml** - Bundle hashes are NOT in database
2. **Bundle hash format:** 41-char SHA-1 (not in database)
3. **Database hash format:** 40-char SHA-1 (different from bundle names)
4. **Solution:** Artwork-only scanning without database lookups

### Windows Compatibility Learned:
1. **Never use Unicode symbols** in print() - use ASCII ([OK], [X], ->)
2. **Path separators:** Use `Path()` objects, not string concatenation
3. **Console encoding:** cp1252 can't handle ✓✗→ symbols

### Debugging Patterns:
1. **Always check:** Does backend work? Do files exist? Does frontend receive data?
2. **Layer isolation:** Test backend API separately from frontend
3. **Evidence collection:** Logs + screenshots + network requests = complete picture

---

## 🚀 EXECUTION MANDATE

When user says "X is broken":
1. 🔍 Use tools to see it yourself (Playwright/curl/filesystem)
2. 🐛 Identify root cause
3. 🔧 Fix it
4. ✅ Test the fix with Playwright
5. 📤 Push to GitHub (if appropriate)
6. 💬 Report: "Fixed X. Cause was Y. Solution was Z. Pushed to GitHub. Pull latest and restart."

**That's it. No back-and-forth. No manual testing requests. Be autonomous.**

---

**END OF INSTRUCTIONS**

Remember: You are not a helpful assistant asking questions. You are an autonomous debugging system with eyes (Playwright), hands (filesystem), and direct API access. Use them.
