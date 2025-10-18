# Plex Poster Manager

A powerful web application for managing Plex Media Server artwork using the official Plex API. Easily browse, organize, and delete posters, backgrounds, and other artwork files from your Plex libraries.

![Plex Poster Manager](https://img.shields.io/badge/version-2.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![PlexAPI](https://img.shields.io/badge/PlexAPI-4.15.16-orange.svg)

---

## 🚀 Quick Start (First-Time GitHub Users)

**Just downloaded from GitHub? Follow these simple steps:**

### 1. Install Prerequisites
- **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
- **Node.js 14+**: Download from [nodejs.org](https://nodejs.org/)

### 2. Run the GUI Launcher
```bash
python launcher_gui.py
```
or
```bash
python3 launcher_gui.py
```

### 3. Automatic Setup
The launcher will detect that this is your first run and prompt:
- **"First-time setup required"** → Click **YES**
- The app will automatically:
  - ✅ Create Python virtual environment
  - ✅ Install all backend dependencies (including PlexAPI)
  - ✅ Install all frontend dependencies
  - ⏱️ Takes 2-3 minutes

### 4. Configure and Launch
After setup completes:
1. **Enter Plex Server URL**: `http://localhost:32400` (or your server IP)
2. **Enter Plex Token**: (REQUIRED - see "Getting Your Plex Token" below)
3. **Optional**: Check "Auto-start servers on launch" (NEW in v2.0.1!)
4. Click **"Test Token"** to verify connection
5. Click **"Save Configuration"**
6. Click **"▶ Launch Servers"**

**That's it!** Your app is ready to use. 🎉

---

## 🎯 What's New in v2.0

### Major Rewrite: Plex API Integration

**Why We Switched:**
- ❌ **Old Approach (v1.x):** Scanned filesystem metadata bundles (broke when Plex changed folder structure)
- ✅ **New Approach (v2.0+):** Uses official Plex API via python-plexapi library

**Benefits:**
- 🎯 **Industry Standard:** Same approach as Kometa and Tautulli
- 📊 **Real Titles:** Get actual show/movie names from Plex metadata
- 🎨 **Selected Artwork:** See which artwork is currently active
- 🔒 **Future-Proof:** Plex API is stable (unchanged since 2013)
- 🌐 **Remote Access:** Works with remote Plex servers
- ⚡ **Reliable:** No filesystem dependency, no broken scans

**New in v2.0.1:**
- ✅ Fixed token testing (now uses PlexAPI connection)
- ✅ Auto-start servers feature (set it and forget it!)
- ✅ Better error messages
- ✅ Windows upgrade scripts

---

## Features

✨ **Visual Management with Plex API**
- Browse all artwork (posters, backgrounds, banners, themes) via Plex API
- See **real show/movie titles** from Plex metadata
- View **provider information** (TheTVDB, TheMovieDB, etc.)
- Know which artwork is **currently selected** in Plex
- Multi-select deletion with visual feedback
- Search and filter by title

🛡️ **Safety First**
- Safe deletion with automatic backup system
- Confirmation dialogs before deletion
- Undo functionality
- All changes backed up before deletion

🎨 **Modern Interface**
- Responsive design works on desktop and mobile
- Fast thumbnail loading from Plex API
- Clean, intuitive UI built with React and Tailwind CSS
- Real-time scanning progress

🔧 **Easy Configuration**
- Auto-detect Plex server URL
- Token testing and validation
- **Auto-start servers on launch** (NEW!)
- Cross-platform GUI launcher (Windows, macOS, Linux)
- Per-library scanning

---

## Installation

> **💡 NEW USERS:** See the [Quick Start](#-quick-start-first-time-github-users) section above for automatic setup!

### Manual Installation (Advanced Users)

If you prefer to set up manually instead of using the automatic launcher:

#### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

This installs:
- Flask 3.0.0
- Flask-CORS 4.0.0
- **PlexAPI 4.15.16** (NEW - official Plex API library)
- Pillow 10.1.0
- watchdog 3.0.0
- requests

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

---

## Getting Your Plex Token (REQUIRED)

**IMPORTANT:** v2.0+ uses the Plex API, which requires authentication. Your Plex token is REQUIRED for the app to function.

### Method 1: Via Plex Web (Easiest)
1. Sign in to [Plex Web](https://app.plex.tv)
2. Open any media item (movie, show, etc.)
3. Click "Get Info" or the "..." menu
4. Click "View XML"
5. Look for `X-Plex-Token=` in the URL
6. Copy the token (long string of letters and numbers)

### Method 2: Via Settings
1. Sign in to [Plex Web](https://app.plex.tv)
2. Go to Settings → Account
3. Look for authentication token

### Method 3: Official Guide
Visit: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

**Security Note:** Your token is stored locally in `config.json` (excluded from git). Keep it secure!

---

## Usage

### Starting the Application

#### Option 1: GUI Launcher (Recommended)

Simply run:
```bash
python3 launcher_gui.py
```

The GUI launcher provides:
- ✅ One-click start/stop for both servers
- 🔑 Plex URL and token configuration
- 🧪 Token testing and validation
- 🚀 **Auto-start servers on launch** (NEW in v2.0.1!)
- 📊 Live server output logs
- 🌐 Quick browser launch button
- ✨ Works on macOS, Windows, and Linux

**Auto-Start Feature (v2.0.1):**
1. Check "Auto-start servers on launch"
2. Click "Save Configuration"
3. Next time you launch, servers start automatically!
4. Perfect for "set it and forget it" workflow

#### Option 2: Manual Start (Advanced)

Run both servers manually in separate terminals:

**Start Backend (Terminal 1):**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```
Backend runs on `http://localhost:5000`

**Start Frontend (Terminal 2):**
```bash
cd frontend
npm start
```
Frontend opens at `http://localhost:3000`

---

### First Time Setup

#### Using the GUI Launcher (Recommended):
1. Launch the app: `python3 launcher_gui.py`
2. In the Configuration section:
   - **Plex Server URL:** Enter `http://localhost:32400` (or your server IP/hostname)
   - **Plex Token:** Paste your Plex token (see "Getting Your Plex Token" above)
   - **Optional:** Check "Auto-start servers on launch"
3. Click **"Test Token"** to verify connection
   - Shows server name and version on success
   - Clear error messages if connection fails
4. Click **"Save Configuration"**
5. Click **"▶ Launch Servers"**
6. Browser auto-opens to http://localhost:3000

#### Via the Web Interface:
1. Open http://localhost:3000 in your browser
2. Click the settings icon (⚙️) in the top right
3. Enter:
   - Plex Server URL (e.g., `http://localhost:32400`)
   - Plex Token
4. Save the configuration

---

### Managing Artwork

1. **Select Library**: Choose a library from the dropdown (TV Shows, Movies, etc.)
2. **Scan Library**: Click "Scan Library" to load all items via Plex API
3. **Browse**: Scroll through shows/movies with their artwork
   - See **real titles** from Plex (not bundle hashes!)
   - View **provider info** (TheTVDB, TheMovieDB, etc.)
   - Know which artwork is **currently selected**
4. **Select**: Click on artwork thumbnails to select them
5. **Delete**: Use "Delete Selected" button
6. **Confirm**: Review and proceed (automatic backup created)
7. **Undo**: If needed, use the undo feature to restore

---

## Common Plex Server URLs

### Local Server (Same Machine)
```
http://localhost:32400
```

### Remote Server (Different Machine)
```
http://192.168.1.XXX:32400
```
Replace `XXX` with your Plex server's IP address

### Remote Access (Plex.tv)
```
https://YOUR-SERVER-ID.plex.direct:32400
```
Find your server ID in Plex settings

**Note:** For remote servers, ensure port 32400 is accessible. Your Plex token handles authentication.

---

## Project Structure

```
plex-poster-manager/
├── backend/
│   ├── app.py                    # Flask API server (v2.0 - Plex API)
│   ├── plex_scanner_api.py       # NEW: Plex API scanner
│   ├── file_manager.py           # File operations and backups
│   └── requirements.txt          # Python dependencies (includes PlexAPI)
├── frontend/
│   ├── public/
│   │   └── index.html            # HTML entry point
│   ├── src/
│   │   ├── App.jsx               # Main React component
│   │   ├── api.js                # API client
│   │   ├── index.jsx             # React entry point
│   │   └── components/           # React components
│   └── package.json              # Node dependencies
├── launcher_gui.py               # GUI Launcher (v2.0.1 - auto-start)
├── INSTALL_PLEXAPI.bat          # Windows PlexAPI installer
├── QUICK_FIX_WINDOWS.bat        # v1.x to v2.0 upgrade helper
└── README.md                     # This file
```

---

## API Endpoints (v2.0+)

### Configuration
- `GET /api/config` - Get current configuration (plex_url, plex_token)
- `POST /api/config` - Update configuration
- `GET /api/detect-url` - Auto-detect Plex server URL
- `POST /api/test-token` - Test Plex token validity (uses PlexAPI)

### Library Management (Plex API)
- `GET /api/libraries` - Get available Plex libraries via API
- `POST /api/scan` - Scan library for items and artwork via Plex API
- `POST /api/search` - Search for shows/movies by title
- `POST /api/duplicates` - Find duplicate artwork

### Artwork Management
- `GET /api/thumbnail?url=<plex_url>` - Get thumbnail from Plex API
- `POST /api/delete` - Delete artwork files (with backup)
- `POST /api/undo` - Undo last deletion
- `GET /api/operations` - Get recent operations
- `POST /api/clean-backups` - Clean old backups

---

## Configuration

The app stores configuration in `config.json` (created automatically):

```json
{
  "plex_url": "http://localhost:32400",
  "plex_token": "your-plex-token-here",
  "auto_start_servers": false,
  "backup_directory": "./backups"
}
```

**v2.0 Changes:**
- `plex_metadata_path` → `plex_url` (uses API, not filesystem)
- `plex_token` is REQUIRED (not optional)
- `auto_start_servers` (NEW in v2.0.1)

**Security Note:** `config.json` is automatically excluded from git via `.gitignore` to protect your Plex token.

---

## Troubleshooting

### Backend won't start
- Make sure Python 3.8+ is installed: `python --version`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- **Windows users upgrading from v1.x:** Run `INSTALL_PLEXAPI.bat`
- Check if port 5000 is already in use

### Frontend won't start
- Make sure Node.js is installed: `node --version`
- Delete `node_modules` and run `npm install` again
- Check if port 3000 is already in use

### Token test fails
- Verify your Plex token is correct (copy it again)
- Check Plex server URL is accessible (try opening in browser)
- Ensure Plex Media Server is running
- For remote servers, verify port 32400 is accessible
- Check firewall settings

### Can't connect to Plex server
- **Local server:** Use `http://localhost:32400`
- **Remote server:** Use `http://SERVER_IP:32400`
- Verify Plex Media Server is running
- Check network connectivity
- Ensure port 32400 is not blocked by firewall

### Artwork not loading
- Verify backend is running (`http://localhost:5000/api/health`)
- Check browser console for errors
- Verify Plex token is valid (use "Test Token" in launcher)
- Ensure Plex server is accessible

### Upgrading from v1.x to v2.0
**Windows Users:**
1. Run `QUICK_FIX_WINDOWS.bat` to install PlexAPI
2. Or run `INSTALL_PLEXAPI.bat` for direct installation
3. Update your configuration to use `plex_url` instead of `plex_metadata_path`
4. Add your Plex token (now required!)

**macOS/Linux Users:**
```bash
cd backend
source venv/bin/activate
pip install PlexAPI==4.15.16
```

---

## Technical Details

### Why We Switched to Plex API

**Filesystem Scanning (v1.x) Issues:**
- ❌ Broke when Plex changed bundle folder structure
- ❌ Couldn't get real show titles (bundle hashes not in database)
- ❌ No way to know which artwork was selected
- ❌ Fragile and unreliable

**Plex API (v2.0+) Benefits:**
- ✅ Stable API (unchanged since 2013)
- ✅ Real show/movie titles from Plex metadata
- ✅ Shows which artwork is currently selected
- ✅ Provider information (TheTVDB, TheMovieDB)
- ✅ Professional approach (same as Kometa, Tautulli)
- ✅ Works with remote Plex servers
- ✅ Future-proof (won't break with Plex updates)

### Code Example

```python
from plexapi.server import PlexServer

# Connect to Plex
plex = PlexServer('http://localhost:32400', 'YOUR_TOKEN')

# Get TV Shows library
library = plex.library.section('TV Shows')

# Scan all shows
for show in library.all():
    print(f"{show.title} ({show.year})")

    # Get all posters
    posters = show.posters()
    for poster in posters:
        selected = "✓" if poster.selected else " "
        print(f"  [{selected}] {poster.provider}")
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

**Development Notes:**
- v2.0+ uses Plex API (never suggest filesystem scanning)
- Always use ASCII symbols in print statements (Windows compatibility)
- Test on Windows before committing (main deployment platform)
- Plex token is REQUIRED (not optional)

---

## Resources

- **Repository:** https://github.com/ButtaJones/plex-poster-manager
- **Plex API Docs:** https://python-plexapi.readthedocs.io
- **Get Plex Token:** https://support.plex.tv/articles/204059436
- **Inspired by:**
  - [Kometa](https://github.com/Kometa-Team/Kometa) (Plex Meta Manager)
  - [Tautulli](https://github.com/Tautulli/Tautulli) (Plex monitoring)

---

## License

MIT License - feel free to use this project for personal or commercial use.

---

## Support

If you encounter any issues or have suggestions:
- Open an issue on [GitHub](https://github.com/ButtaJones/plex-poster-manager/issues)
- Check existing issues for solutions
- Include error messages and logs

---

**Note**: This tool manages your Plex artwork via the official Plex API. While it includes safety features like automatic backups, always ensure you have a complete backup of your Plex data before making changes.
