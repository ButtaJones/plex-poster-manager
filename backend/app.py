"""
Flask API Server for Plex Poster Manager
Provides REST endpoints for scanning, managing, and deleting Plex artwork.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import os
import sys
import io
import json
from PIL import Image
import requests

from plex_scanner_api import PlexScannerAPI, detect_plex_url
from file_manager import FileManager

app = Flask(__name__)
CORS(app)

# Global instances
scanner = None
file_manager = FileManager()
config = {}
scan_progress = {
    "scanning": False,
    "current": 0,
    "total": 0,
    "current_item": "",
    "library": ""
}

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
            "plex_url": detect_plex_url() or "http://localhost:32400",
            "plex_token": "",
            "backup_directory": str(Path(__file__).parent.parent / "backups"),
            "thumbnail_size": [300, 450],
            "auto_detect_url": True
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

        # Reinitialize scanner if URL or token changed
        if 'plex_url' in data or 'plex_token' in data:
            plex_url = config.get('plex_url', 'http://localhost:32400')
            plex_token = config.get('plex_token', '')

            if not plex_token:
                print(f"[API /api/config POST] WARNING: No Plex token provided")
                return jsonify({
                    "success": False,
                    "error": "Plex token is REQUIRED for API-based scanning. Please provide a valid token."
                }), 400

            print(f"[API /api/config POST] Initializing API scanner with URL: {plex_url}")
            scanner = PlexScannerAPI(plex_url, plex_token)

            if not scanner.connect():
                print(f"[API /api/config POST] WARNING: Connection to Plex failed")
                return jsonify({
                    "success": False,
                    "error": "Could not connect to Plex server. Check URL and token."
                }), 400

            print(f"[API /api/config POST] Scanner initialized successfully")

        print(f"[API /api/config POST] [OK] Configuration updated successfully")
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
    """Auto-detect Plex server URL."""
    print("\n[API /api/detect-path] Auto-detecting Plex server URL...")

    try:
        detected_url = detect_plex_url()

        if detected_url:
            print(f"[API /api/detect-path] Found URL: {detected_url}")
            return jsonify({
                "success": True,
                "url": detected_url
            })
        else:
            print(f"[API /api/detect-path] No URL found")
            return jsonify({
                "success": False,
                "error": "Could not auto-detect Plex server"
            }), 404
    except Exception as e:
        print(f"[API /api/detect-path] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Error during URL detection: {str(e)}"
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
        # Try both header and query param methods for compatibility
        response = requests.get(
            f"https://plex.tv/api/v2/user?X-Plex-Token={token}",
            headers={"Accept": "application/json"},
            timeout=10
        )

        print(f"[test-token] Response status: {response.status_code}")
        print(f"[test-token] Response headers: {dict(response.headers)}")
        print(f"[test-token] Response text (first 200 chars): {response.text[:200]}")
        print(f"[test-token] Response length: {len(response.text)} chars")

        if response.status_code == 200:
            try:
                # Check if response is empty
                if not response.text or len(response.text.strip()) == 0:
                    print(f"[test-token] ERROR: Empty response from Plex API")
                    return jsonify({
                        "success": False,
                        "error": "Plex API returned empty response. Token may be invalid or Plex servers may be down."
                    }), 500

                # Check if response is JSON
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type and 'application/xml' not in content_type:
                    print(f"[test-token] WARNING: Unexpected content type: {content_type}")
                    # Try to parse as JSON anyway (Plex sometimes returns wrong content-type)

                user_data = response.json()
                username = user_data.get("username", user_data.get("title", "Unknown"))
                print(f"[test-token] [OK] Token valid for user: {username}")

                return jsonify({
                    "success": True,
                    "username": username,
                    "message": f"Token valid for user: {username}"
                })
            except ValueError as json_error:
                print(f"[test-token] JSON parsing error: {json_error}")
                print(f"[test-token] Response was: {response.text[:500]}")
                return jsonify({
                    "success": False,
                    "error": f"Token validation failed: Plex returned invalid response. The token may be incorrect or expired."
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
    print("\n[API /api/libraries] Getting libraries...")

    if not scanner:
        print("[API /api/libraries] ERROR: Scanner not initialized")
        return jsonify({"error": "Plex scanner not initialized. Please configure URL and token."}), 400

    try:
        libraries = scanner.get_libraries()
        print(f"[API /api/libraries] Returning {len(libraries)} libraries: {libraries}")
        return jsonify({"libraries": libraries})
    except Exception as e:
        print(f"[API /api/libraries] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "libraries": []}), 500


@app.route('/api/scan', methods=['POST'])
def scan_library():
    """Scan a Plex library for items and artwork."""
    global scan_progress

    if not scanner:
        return jsonify({
            "success": False,
            "error": "Plex scanner not initialized. Please configure URL and token."
        }), 400

    data = request.json
    library = data.get('library', 'TV Shows')
    limit = data.get('limit', None)  # None = scan all
    offset = data.get('offset', 0)  # Start position for pagination

    if limit:
        print(f"\n[API /api/scan] Scanning library: {library} (limit: {limit} items, offset: {offset})")
    else:
        print(f"\n[API /api/scan] Scanning library: {library} (all items)")

    # Initialize progress
    scan_progress = {
        "scanning": True,
        "current": 0,
        "total": 0,
        "current_item": "",
        "library": library
    }

    def progress_callback(current, total, item_name):
        """Update scan progress."""
        scan_progress.update({
            "scanning": True,
            "current": current,
            "total": total,
            "current_item": item_name,
            "library": library
        })

    try:
        result = scanner.scan_library(library, progress_callback=progress_callback, limit=limit, offset=offset)

        # Mark scanning complete
        scan_progress["scanning"] = False

        # Extract items and total count from result
        items = result['items']
        total_count = result['total_count']
        total_artwork = sum(item['total_artwork'] for item in items)

        print(f"[API /api/scan] Scan completed. Items returned: {len(items)}, Total in library: {total_count}, Artwork: {total_artwork}")

        # Build response
        response = {
            "success": True,
            "library": library,
            "items": items,
            "stats": {
                "total_items": len(items),
                "total_artwork": total_artwork,
                "total_count": total_count,  # Total items in library (for pagination)
                "offset": offset,
                "limit": limit
            }
        }

        # Add helpful message if no results
        if len(items) == 0:
            response["warning"] = (
                "No items with artwork found. Please check:\n"
                "1. The Plex server is running and accessible\n"
                "2. The Plex token is valid\n"
                f"3. The '{library}' library exists and contains media\n"
                "4. The library items have artwork assigned"
            )
            print(f"[API /api/scan] WARNING: No items found!")

        return jsonify(response)

    except Exception as e:
        scan_progress["scanning"] = False
        print(f"[API /api/scan] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/thumbnail', methods=['GET'])
def get_thumbnail():
    """Fetch and serve a thumbnail from Plex API."""
    thumb_url = request.args.get('url')
    size = config.get('thumbnail_size', [300, 450])

    if not thumb_url:
        return jsonify({"error": "No thumbnail URL provided"}), 400

    try:
        # Fetch image from Plex
        print(f"[thumbnail] Fetching: {thumb_url[:100]}...")
        response = requests.get(thumb_url, timeout=10)

        if response.status_code != 200:
            print(f"[thumbnail] HTTP {response.status_code} for URL: {thumb_url[:100]}")
            return jsonify({"error": f"Plex returned {response.status_code}"}), 404

        # Check if response is actually an image
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"[thumbnail] Invalid content type: {content_type}")
            return jsonify({"error": f"Invalid content type: {content_type}"}), 400

        # Open and resize image
        img = Image.open(io.BytesIO(response.content))
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Save to bytes
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)

        # Create response with proper headers to prevent CORB
        response = send_file(img_io, mimetype='image/jpeg')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cross-Origin-Resource-Policy'] = 'cross-origin'
        return response

    except requests.exceptions.Timeout:
        print(f"[thumbnail] Timeout fetching URL: {thumb_url[:100]}")
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        print(f"[thumbnail] Request error: {e}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        print(f"[thumbnail] ERROR processing {thumb_url[:100]}: {e}")
        import traceback
        traceback.print_exc()
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
        return jsonify({"error": "Plex scanner not initialized"}), 400

    data = request.json
    query = data.get('query', '').lower()
    library = data.get('library', 'TV Shows')

    try:
        # scan_library returns {'items': [...], 'total_count': N}
        result = scanner.scan_library(library)
        all_items = result['items']

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
        print(f"[API /api/search] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/duplicates', methods=['POST'])
def find_duplicates():
    """Find duplicate artwork files (TODO: implement for API scanner)."""
    return jsonify({
        "success": True,
        "duplicates": [],
        "count": 0,
        "message": "Duplicate detection not yet implemented for API scanner"
    })


@app.route('/api/scan-progress', methods=['GET'])
def get_scan_progress():
    """Get current scan progress."""
    return jsonify(scan_progress)


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

    # Initialize scanner if URL and token are configured
    plex_url = config.get('plex_url')
    plex_token = config.get('plex_token')

    if plex_url and plex_token:
        print(f"\n[initialize] Initializing Plex API scanner...")
        scanner = PlexScannerAPI(plex_url, plex_token)
        scanner.connect()
    else:
        print(f"\n[initialize] No Plex URL/token configured. Scanner not initialized.")


if __name__ == '__main__':
    initialize()
    print("=" * 60)
    print("Plex Poster Manager API Server (v2.0.0 - Plex API)")
    print("=" * 60)
    print(f"Server running on http://localhost:5000")
    print(f"Plex URL: {config.get('plex_url', 'Not configured')}")
    print(f"Plex Token: {'Configured' if config.get('plex_token') else 'Not configured'}")
    print(f"Backup directory: {config.get('backup_directory')}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
