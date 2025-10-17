# Plex Poster Manager

A powerful web application for managing Plex Media Server artwork. Easily browse, organize, and delete posters, backgrounds, and other artwork files from your Plex metadata.

![Plex Poster Manager](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)

## Features

✨ **Visual Management**
- Browse all artwork (posters, art, backgrounds, banners) with thumbnail previews
- See source information (TheTVDB, TheMovieDB, local files)
- Multi-select deletion with visual feedback
- Search and filter by show name or season

🛡️ **Safety First**
- Safe deletion with backup system
- Confirmation dialogs before deletion
- Undo functionality
- Automatic backup creation before any changes

🎨 **Modern Interface**
- Responsive design works on desktop and mobile
- Fast thumbnail loading with lazy loading
- Clean, intuitive UI built with React and Tailwind CSS
- Real-time scanning progress

🔧 **Flexible Configuration**
- Auto-detect Plex metadata path
- Manual path configuration for custom setups
- Support for Windows, macOS, and Linux paths
- Per-library scanning

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

### Backend Setup

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

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

## Usage

### Starting the Application

**NEW: Easy GUI Launcher (Recommended)**

Simply double-click `launcher_gui.py` or run:
```bash
python3 launcher_gui.py
```

The GUI launcher provides:
- ✅ One-click start/stop for both servers
- 📁 Browse button for selecting Plex metadata folder
- 🔑 Optional Plex token configuration and testing
- 📊 Live server output logs
- 🌐 Quick browser launch button
- ✨ Works on macOS, Windows, and Linux

**OR: Manual Start (Advanced)**

You can still run both servers manually in separate terminals:

#### Start Backend (Terminal 1):
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```
The backend will run on `http://localhost:5000`

#### Start Frontend (Terminal 2):
```bash
cd frontend
npm start
```
The frontend will open automatically at `http://localhost:3000`

### First Time Setup

**Using the GUI Launcher:**
1. Launch the app using `launcher_gui.py`
2. In the Configuration section:
   - Click "Browse" to select your Plex metadata folder
   - OR click "Auto-Detect" to find it automatically
   - (Optional) Add your Plex token and click "Test Token"
3. Click "Save Configuration"
4. Click "▶ Launch Servers"
5. The browser will auto-open to http://localhost:3000

**OR via the Web Interface:**
1. Open the application in your browser (http://localhost:3000)
2. Click the settings icon (⚙️) in the top right
3. Either:
   - Click "Auto-detect Path" to automatically find your Plex metadata
   - Or manually enter your Plex metadata path
4. Save the configuration

### Managing Artwork

1. **Scan Library**: Click "Scan Library" to load all shows and their artwork
2. **Browse**: Scroll through shows and seasons with their artwork
3. **Select**: Click on artwork thumbnails to select them for deletion
4. **Delete**: Use the "Delete Selected" button to remove artwork
5. **Confirm**: Review the confirmation dialog and proceed

### Common Plex Metadata Paths

**Windows:**
```
C:\Users\[YourUsername]\AppData\Local\Plex Media Server\Metadata\TV Shows
```

**macOS:**
```
~/Library/Application Support/Plex Media Server/Metadata/TV Shows
```

**Linux:**
```
/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Metadata/TV Shows
```

## Project Structure

```
plex-poster-manager/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── plex_scanner.py        # Plex metadata scanning logic
│   ├── file_manager.py        # File operations and backups
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html         # HTML entry point
│   ├── src/
│   │   ├── App.jsx            # Main React component
│   │   ├── api.js             # API client
│   │   ├── index.jsx          # React entry point
│   │   └── components/        # React components
│   └── package.json           # Node dependencies
└── README.md                  # This file
```

## Plex Token (Optional)

The Plex token feature is optional and provides additional functionality:

### Why use a Plex Token?
- **Verification**: Confirm you're connected to the right Plex account
- **Future Features**: Will enable direct Plex API integration for:
  - Triggering metadata refresh after artwork deletion
  - Accessing Plex server information
  - Remote Plex server management

### How to get your Plex Token:
1. Log in to https://app.plex.tv
2. Open your browser's developer tools (F12)
3. Go to the Network tab
4. Refresh the page and look for requests to `plex.tv`
5. Check the request headers for `X-Plex-Token`
6. OR follow the official guide: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

**Note:** Your token is stored locally in `config.json`. Keep this file secure and never commit it to version control.

## API Endpoints

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/detect-path` - Auto-detect Plex metadata path
- `POST /api/test-token` - Test if a Plex token is valid

### Library
- `GET /api/libraries` - Get available libraries
- `POST /api/scan` - Scan a library for shows and artwork
- `POST /api/search` - Search for shows/seasons

### Artwork
- `GET /api/thumbnail?path=<path>` - Get thumbnail image
- `DELETE /api/artwork` - Delete selected artwork files
- `POST /api/undo` - Undo last deletion

## Configuration

The app stores configuration in `config.json` (created automatically):

```json
{
  "plex_metadata_path": "/path/to/Plex Media Server/Metadata/TV Shows",
  "plex_token": "your-plex-token-here",
  "backup_directory": "./backups",
  "thumbnail_size": [300, 450],
  "auto_detect_path": true
}
```

**Note:** The `config.json` file is automatically excluded from git via `.gitignore` to protect your Plex token.

## Troubleshooting

### Backend won't start
- Make sure Python 3.8+ is installed: `python --version`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is already in use

### Frontend won't start
- Make sure Node.js is installed: `node --version`
- Delete `node_modules` and run `npm install` again
- Check if port 3000 is already in use

### Can't find Plex metadata
- Make sure Plex Media Server is installed
- Try auto-detect first
- Check the common paths listed above
- Verify you have read permissions for the metadata directory

### Artwork not loading
- Check browser console for errors
- Verify the backend is running
- Check file permissions on metadata directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial use.

## Acknowledgments

- Built for the Plex community
- Inspired by the need for better artwork management tools
- Uses Flask, React, and Tailwind CSS

## Support

If you encounter any issues or have suggestions, please open an issue on GitHub.

---

**Note**: This tool directly modifies your Plex metadata. While it includes safety features like backups, always ensure you have a complete backup of your Plex data before using this tool.
