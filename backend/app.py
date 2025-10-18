"""
Flask API Server for Plex Poster Manager
Provides REST endpoints for scanning, managing, and deleting Plex artwork.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import os
import json
from io import BytesIO
from PIL import Image
import requests

from plex_scanner import PlexScanner, detect_plex_path
from file_manager import FileManager

app = Flask(__name__)
CORS(app)

# Global instances
scanner = None
file_manager = FileManager()
config = {}

# Configuration file path
CONFIG_FILE = Path(__file__).parent.parent / "config.json"


def load_config():
    """Load configuration from file."""
    global config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        # Default config
        config = {
            "plex_metadata_path": detect_plex_path() or "",
            "plex_token": "",
            "backup_directory": str(Path(__file__).parent.parent / "backups"),
            "thumbnail_size": [300, 450],
            "auto_detect_path": True
        }
        save_config()


def save_config():
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    global config, scanner

    print("\n[API /api/config POST] Updating configuration...")

    try:
        data = request.json
        print(f"[API /api/config POST] Received data: {data}")

        if not data:
            print(f"[API /api/config POST] ERROR: No data received")
            return jsonify({
                "success": False,
                "error": "No configuration data provided"
            }), 400

        # Update config
        config.update(data)
        save_config()
        print(f"[API /api/config POST] Configuration saved")

        # Reinitialize scanner if path changed
        if 'plex_metadata_path' in data and data['plex_metadata_path']:
            print(f"[API /api/config POST] Initializing scanner with path: {data['plex_metadata_path']}")
            scanner = PlexScanner(data['plex_metadata_path'])

            if not scanner.validate_path():
                print(f"[API /api/config POST] WARNING: Path validation failed")
                return jsonify({
                    "success": False,
                    "error": "Invalid Plex metadata path - path does not exist or is not a valid Plex directory"
                }), 400

            print(f"[API /api/config POST] Scanner initialized successfully")

        print(f"[API /api/config POST] ✓ Configuration updated successfully")
        return jsonify({"success": True, "config": config})

    except Exception as e:
        print(f"[API /api/config POST] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to update configuration: {str(e)}"
        }), 500


@app.route('/api/detect-path', methods=['GET'])
def auto_detect_path():
    """Auto-detect Plex metadata path."""
    print("\n[API /api/detect-path] Auto-detecting Plex metadata path...")

    try:
        detected_path = detect_plex_path()

        if detected_path:
            print(f"[API /api/detect-path] Found path: {detected_path}")
            return jsonify({
                "success": True,
                "path": detected_path
            })
        else:
            print(f"[API /api/detect-path] No path found")
            return jsonify({
                "success": False,
                "error": "Could not auto-detect Plex path"
            }), 404
    except Exception as e:
        print(f"[API /api/detect-path] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Error during path detection: {str(e)}"
        }), 500


@app.route('/api/test-token', methods=['POST'])
def test_plex_token():
    """Test if a Plex token is valid."""
    data = request.json
    token = data.get('token', '').strip()

    if not token:
        return jsonify({
            "success": False,
            "error": "No token provided"
        }), 400

    print(f"\n[test-token] Testing token: {token[:10]}...")

    try:
        response = requests.get(
            "https://plex.tv/api/v2/user",
            headers={"X-Plex-Token": token,
                     "Accept": "application/json"},
            timeout=10
        )

        print(f"[test-token] Response status: {response.status_code}")
        print(f"[test-token] Response headers: {dict(response.headers)}")
        print(f"[test-token] Response text (first 200 chars): {response.text[:200]}")

        if response.status_code == 200:
            try:
                # Check if response is JSON
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    print(f"[test-token] WARNING: Response is not JSON, Content-Type: {content_type}")
                    return jsonify({
                        "success": False,
                        "error": f"Unexpected response format (Content-Type: {content_type})"
                    }), 500

                user_data = response.json()
                username = user_data.get("username", user_data.get("title", "Unknown"))
                print(f"[test-token] Token valid for user: {username}")

                return jsonify({
                    "success": True,
                    "username": username,
                    "message": f"Token valid for user: {username}"
                })
            except ValueError as json_error:
                print(f"[test-token] JSON parsing error: {json_error}")
                return jsonify({
                    "success": False,
                    "error": f"Failed to parse response: {str(json_error)}"
                }), 500
        else:
            print(f"[test-token] Invalid token, status: {response.status_code}")
            return jsonify({
                "success": False,
                "error": f"Invalid token (Status: {response.status_code})"
            }), 401

    except requests.exceptions.Timeout:
        print(f"[test-token] Request timeout")
        return jsonify({
            "success": False,
            "error": "Request timed out - check internet connection"
        }), 500
    except requests.exceptions.RequestException as e:
        print(f"[test-token] Network error: {e}")
        return jsonify({
            "success": False,
            "error": f"Network error: {str(e)}"
        }), 500
    except Exception as e:
        print(f"[test-token] Unexpected error: {e}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    """Get list of available Plex libraries."""
    if not scanner:
        return jsonify({"error": "Plex path not configured"}), 400
    
    libraries = scanner.get_libraries()
    return jsonify({"libraries": libraries})


@app.route('/api/scan', methods=['POST'])
def scan_library():
    """Scan a Plex library for items and artwork."""
    if not scanner:
        return jsonify({
            "success": False,
            "error": "Plex path not configured"
        }), 400

    data = request.json
    library = data.get('library', 'TV Shows')

    print(f"\n[API /api/scan] Scanning library: {library}")

    try:
        items = scanner.scan_library(library)

        # Add statistics
        total_items = len(items)
        total_artwork = sum(item['total_artwork'] for item in items)

        print(f"[API /api/scan] Scan completed. Items: {total_items}, Artwork: {total_artwork}")

        # Build response with helpful message if empty
        response = {
            "success": True,
            "library": library,
            "items": items,
            "stats": {
                "total_items": total_items,
                "total_artwork": total_artwork
            }
        }

        # Add helpful message if no results
        if total_items == 0:
            response["warning"] = (
                "No items with artwork found. Please check:\n"
                "1. The path contains Plex metadata (.bundle folders)\n"
                "2. The path is correct and accessible\n"
                f"3. The '{library}' library exists at this location\n"
                "4. The metadata folders contain artwork files"
            )
            print(f"[API /api/scan] WARNING: No items found!")

        return jsonify(response)

    except Exception as e:
        print(f"[API /api/scan] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/thumbnail', methods=['GET'])
def get_thumbnail():
    """Generate and serve a thumbnail for an artwork file."""
    file_path = request.args.get('path')
    size = config.get('thumbnail_size', [300, 450])
    
    if not file_path or not Path(file_path).exists():
        return jsonify({"error": "File not found"}), 404
    
    try:
        # Open and resize image
        img = Image.open(file_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Save to bytes
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete', methods=['POST'])
def delete_artwork():
    """Delete one or more artwork files."""
    data = request.json
    file_paths = data.get('files', [])
    reason = data.get('reason', 'User deletion')
    
    if not file_paths:
        return jsonify({"error": "No files specified"}), 400
    
    if len(file_paths) == 1:
        result = file_manager.delete_file(file_paths[0], reason)
    else:
        result = file_manager.delete_multiple(file_paths, reason)
    
    return jsonify(result)


@app.route('/api/undo', methods=['POST'])
def undo_deletion():
    """Undo a deletion operation."""
    data = request.json
    operation_id = data.get('operation_id')
    
    if operation_id is None:
        return jsonify({"error": "Operation ID required"}), 400
    
    result = file_manager.undo_operation(operation_id)
    return jsonify(result)


@app.route('/api/operations', methods=['GET'])
def get_operations():
    """Get recent operations."""
    limit = request.args.get('limit', 50, type=int)
    operations = file_manager.get_recent_operations(limit)
    return jsonify({"operations": operations})


@app.route('/api/backup-info', methods=['GET'])
def get_backup_info():
    """Get backup directory information."""
    info = file_manager.get_backup_size()
    return jsonify(info)


@app.route('/api/clean-backups', methods=['POST'])
def clean_old_backups():
    """Clean backups older than specified days."""
    data = request.json
    days = data.get('days', 30)
    
    result = file_manager.clean_old_backups(days)
    return jsonify(result)


@app.route('/api/search', methods=['POST'])
def search_items():
    """Search for items by title."""
    if not scanner:
        return jsonify({"error": "Plex path not configured"}), 400
    
    data = request.json
    query = data.get('query', '').lower()
    library = data.get('library', 'TV Shows')
    
    try:
        all_items = scanner.scan_library(library)
        
        # Filter by search query
        filtered_items = [
            item for item in all_items
            if query in item['info']['title'].lower()
        ]
        
        return jsonify({
            "success": True,
            "items": filtered_items,
            "total": len(filtered_items)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/duplicates', methods=['POST'])
def find_duplicates():
    """Find duplicate artwork files."""
    if not scanner:
        return jsonify({"error": "Plex path not configured"}), 400
    
    data = request.json
    library = data.get('library', 'TV Shows')
    
    try:
        all_items = scanner.scan_library(library)
        duplicates = scanner.find_duplicates(all_items)
        
        return jsonify({
            "success": True,
            "duplicates": duplicates,
            "count": len(duplicates)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "scanner_initialized": scanner is not None,
        "config_loaded": bool(config)
    })


def initialize():
    """Initialize the application."""
    global scanner
    load_config()
    
    # Initialize scanner if path is configured
    if config.get('plex_metadata_path'):
        scanner = PlexScanner(config['plex_metadata_path'])


if __name__ == '__main__':
    initialize()
    print("=" * 60)
    print("Plex Poster Manager API Server")
    print("=" * 60)
    print(f"Server running on http://localhost:5000")
    print(f"Plex path: {config.get('plex_metadata_path', 'Not configured')}")
    print(f"Backup directory: {config.get('backup_directory')}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
