"""
Plex Scanner using Official Plex API (v2.0.0)
Professional approach using python-plexapi library.
Based on how Kometa and Tautulli handle Plex artwork.
"""

import sys
import io

# Fix Windows console encoding for Unicode characters (emojis in library names, etc.)
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass  # Fallback to default encoding if wrapper fails

from plexapi.server import PlexServer
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import platform


class PlexScannerAPI:
    """
    Plex artwork scanner using the official Plex API.

    This is the CORRECT way to manage Plex artwork, as used by:
    - Kometa (Plex Meta Manager)
    - Tautulli
    - Other professional Plex tools

    Advantages over filesystem scanning:
    - Always works (no folder structure changes break it)
    - Gets real titles from Plex metadata
    - Shows which artwork is selected
    - Can trigger Plex refreshes
    - Future-proof (Plex API is stable)
    """

    def __init__(self, plex_url: str, plex_token: str):
        """
        Initialize Plex API scanner.

        Args:
            plex_url: Plex server URL (e.g., 'http://localhost:32400')
            plex_token: Plex authentication token (REQUIRED)
        """
        self.plex_url = plex_url.rstrip('/')
        self.plex_token = plex_token
        self.plex = None

        print(f"\n[PlexScannerAPI] Initializing with Plex API")
        print(f"[PlexScannerAPI] URL: {plex_url}")
        print(f"[PlexScannerAPI] Token: {plex_token[:10]}..." if plex_token else "[PlexScannerAPI] Token: None")

    def connect(self) -> bool:
        """
        Connect to Plex server and verify authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            print(f"\n[PlexScannerAPI] Connecting to Plex server...")
            self.plex = PlexServer(self.plex_url, self.plex_token)

            # Verify connection by getting server identity
            print(f"[PlexScannerAPI] Connected to: {self.plex.friendlyName}")
            print(f"[PlexScannerAPI] Version: {self.plex.version}")
            print(f"[PlexScannerAPI] Platform: {self.plex.platform}")
            return True

        except Unauthorized:
            print(f"[PlexScannerAPI] ERROR: Invalid Plex token")
            return False
        except Exception as e:
            print(f"[PlexScannerAPI] ERROR: Connection failed - {e}")
            return False

    def get_libraries(self) -> List[Dict]:
        """
        Get list of available libraries with item counts.

        Returns:
            List of dicts with 'name' and 'count' keys
        """
        if not self.plex:
            if not self.connect():
                return []

        try:
            libraries = []
            for section in self.plex.library.sections():
                # Use totalSize property instead of loading all items
                # This is MUCH faster (instant vs 30 seconds)
                item_count = section.totalSize
                libraries.append({
                    'name': section.title,
                    'count': item_count
                })
                print(f"[get_libraries] {section.title}: {item_count} items")

            print(f"\n[get_libraries] Found {len(libraries)} libraries")
            return libraries
        except Exception as e:
            print(f"[get_libraries] ERROR: {e}")
            return []

    def scan_library(self, library_name: str, progress_callback=None, limit: int = None, offset: int = 0) -> Dict:
        """
        Scan a library for shows/movies and their artwork.

        Args:
            library_name: Name of library to scan (e.g., 'TV Shows', 'Movies')
            progress_callback: Optional callback function(current, total, item_name)
            limit: Optional limit on number of items to scan (None = scan all)
            offset: Starting position for pagination (default 0)

        Returns:
            Dict with 'items' (list of items with artwork) and 'total_count' (total items in library)
        """
        if not self.plex:
            if not self.connect():
                return []

        print(f"\n[scan_library] Scanning library: '{library_name}'")
        print(f"[scan_library] Using Plex API (professional approach)")

        try:
            library = self.plex.library.section(library_name)
            print(f"[scan_library] Library type: {library.type}")

            items = []
            all_content = library.all()
            total_items = len(all_content)

            # Apply offset and limit for pagination
            if limit and limit > 0:
                end_pos = offset + limit
                all_content = all_content[offset:end_pos]
                print(f"[scan_library] Found {total_items} items in library (showing {offset+1}-{min(end_pos, total_items)})")
            else:
                print(f"[scan_library] Found {total_items} items in library (scanning all)")

            # Use threading to process items in parallel (5 workers for speed)
            print(f"[scan_library] Processing {len(all_content)} items with parallel threads...")

            def process_item(idx_content_tuple):
                idx, content = idx_content_tuple
                if idx < 5:
                    print(f"\n[scan_library] Processing item {idx + 1}: {content.title}")
                elif idx == 5:
                    print(f"\n[scan_library] Processing remaining items (summary mode)...")

                try:
                    item_data = self._get_item_artwork(content, detailed=idx < 5)

                    # FILTER: Only show items with custom artwork in Uploads folder
                    # This prevents showing items that only have agent posters (can't be deleted)
                    if item_data.get('has_custom_artwork', False):
                        if idx < 5:
                            print(f"  ✓ Has {item_data['custom_artwork_count']} deletable file(s) in Uploads folder")
                        return item_data
                    else:
                        if idx < 5:
                            print(f"  ✗ No custom artwork (only agent posters) - skipping")
                        return None
                except Exception as e:
                    if idx < 5:
                        print(f"[scan_library] ERROR processing {content.title}: {e}")
                return None

            # Process items in parallel with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_item = {executor.submit(process_item, (idx, content)): idx
                                  for idx, content in enumerate(all_content)}

                for future in as_completed(future_to_item):
                    idx = future_to_item[future]
                    if progress_callback:
                        progress_callback(idx + 1, total_items, all_content[idx].title)

                    try:
                        item_data = future.result()
                        if item_data:
                            items.append(item_data)
                    except Exception as e:
                        print(f"[scan_library] ERROR in thread: {e}")

            print(f"\n[scan_library] Scan complete!")
            print(f"[scan_library] Total items with CUSTOM artwork: {len(items)}")
            print(f"[scan_library] Total deletable files: {sum(item.get('custom_artwork_count', 0) for item in items)}")

            return {
                'items': items,
                'total_count': total_items
            }

        except NotFound:
            print(f"[scan_library] ERROR: Library '{library_name}' not found")
            return {'items': [], 'total_count': 0}
        except Exception as e:
            print(f"[scan_library] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {'items': [], 'total_count': 0}

    def _build_thumb_url(self, thumb_path: str, item_rating_key: str = None) -> str:
        """
        Build complete thumbnail URL, handling both relative and absolute URLs.

        Args:
            thumb_path: Thumb path from PlexAPI (can be relative or absolute URL)
            item_rating_key: Optional rating key of the parent item (for fallback)

        Returns:
            Complete thumbnail URL with token
        """
        # If it's already a full URL (starts with http:// or https://)
        if thumb_path.startswith('http://') or thumb_path.startswith('https://'):
            # External URLs (Plex transcoder, TVDB, TMDB, etc.) - use as-is
            # These are already authenticated or publicly accessible
            return thumb_path

        # Handle internal Plex metadata references (metadata://, upload://, etc.)
        if '/file?url=' in thumb_path or 'metadata://' in thumb_path or 'upload://' in thumb_path:
            # These are internal Plex references that don't work well as direct URLs
            # Use the item's thumb endpoint instead if available
            if item_rating_key:
                return f"{self.plex_url}/library/metadata/{item_rating_key}/thumb?X-Plex-Token={self.plex_token}"
            # If no rating key, try to extract it from the path
            if '/library/metadata/' in thumb_path:
                # Extract rating key from path like /library/metadata/303344/file?...
                import re
                match = re.search(r'/library/metadata/(\d+)/', thumb_path)
                if match:
                    rating_key = match.group(1)
                    return f"{self.plex_url}/library/metadata/{rating_key}/thumb?X-Plex-Token={self.plex_token}"

        # It's a relative path to local Plex server - prepend server URL and token
        return f"{self.plex_url}{thumb_path}?X-Plex-Token={self.plex_token}"

    def _get_item_artwork(self, item, detailed: bool = False) -> Dict:
        """
        Get all artwork for a single item (show/movie).

        Args:
            item: PlexAPI item object
            detailed: Whether to print detailed logs

        Returns:
            Dictionary with item metadata and artwork
        """
        artwork_data = {
            "posters": [],
            "art": [],  # Background artwork
            "banners": [],
            "themes": []
        }

        # Get available posters
        try:
            posters = item.posters()
            if detailed:
                print(f"  [artwork] Found {len(posters)} posters")

            for idx, poster in enumerate(posters):
                # Use index as rating key since poster.ratingKey might be a URL
                poster_key = f"poster_{idx}"
                artwork_data["posters"].append({
                    "path": f"{item.ratingKey}/poster/{poster_key}",  # Unique path for React keys
                    "provider": poster.provider if hasattr(poster, 'provider') else "unknown",
                    "selected": poster.selected if hasattr(poster, 'selected') else False,
                    "thumb_url": self._build_thumb_url(poster.thumb, item.ratingKey),
                    "rating_key": poster_key,
                    "type": "poster"
                })
        except Exception as e:
            if detailed:
                print(f"  [artwork] No posters available: {e}")

        # Get available art (backgrounds)
        try:
            arts = item.arts()
            if detailed:
                print(f"  [artwork] Found {len(arts)} background arts")

            for idx, art in enumerate(arts):
                art_key = f"art_{idx}"
                artwork_data["art"].append({
                    "path": f"{item.ratingKey}/art/{art_key}",  # Unique path for React keys
                    "provider": art.provider if hasattr(art, 'provider') else "unknown",
                    "selected": art.selected if hasattr(art, 'selected') else False,
                    "thumb_url": self._build_thumb_url(art.thumb, item.ratingKey),
                    "rating_key": art_key,
                    "type": "background"
                })
        except Exception as e:
            if detailed:
                print(f"  [artwork] No background arts available: {e}")

        # Get available banners (TV shows)
        try:
            banners = item.banners()
            if detailed:
                print(f"  [artwork] Found {len(banners)} banners")

            for idx, banner in enumerate(banners):
                banner_key = f"banner_{idx}"
                artwork_data["banners"].append({
                    "path": f"{item.ratingKey}/banner/{banner_key}",  # Unique path for React keys
                    "provider": banner.provider if hasattr(banner, 'provider') else "unknown",
                    "selected": banner.selected if hasattr(banner, 'selected') else False,
                    "thumb_url": self._build_thumb_url(banner.thumb, item.ratingKey),
                    "rating_key": banner_key,
                    "type": "banner"
                })
        except Exception as e:
            if detailed:
                print(f"  [artwork] No banners available: {e}")

        # Get available themes
        try:
            themes = item.themes()
            if detailed:
                print(f"  [artwork] Found {len(themes)} themes")

            for idx, theme in enumerate(themes):
                theme_key = f"theme_{idx}"
                artwork_data["themes"].append({
                    "path": f"{item.ratingKey}/theme/{theme_key}",  # Unique path for React keys
                    "provider": theme.provider if hasattr(theme, 'provider') else "unknown",
                    "selected": theme.selected if hasattr(theme, 'selected') else False,
                    "thumb_url": self._build_thumb_url(theme.thumb, item.ratingKey),
                    "rating_key": theme_key,
                    "type": "theme"
                })
        except Exception as e:
            if detailed:
                print(f"  [artwork] No themes available: {e}")

        # FILTER: Only show artwork that can actually be deleted (exists in Uploads folder)
        # This prevents showing agent-provided posters that can't be deleted
        uploads_file_count = self._get_uploads_file_count(item, debug=detailed)

        if uploads_file_count > 0:
            # Mark that this item has deletable artwork
            if detailed:
                print(f"  [artwork] ✓ Found {uploads_file_count} deletable files in Uploads folder")
        else:
            # No custom artwork to delete - clear all artwork lists
            if detailed:
                print(f"  [artwork] ✗ No custom artwork in Uploads folder")
            # Don't clear - we still want to show the posters for viewing
            # But we could add a flag to indicate they're not deletable

        # Calculate total artwork
        total_artwork = (
            len(artwork_data["posters"]) +
            len(artwork_data["art"]) +
            len(artwork_data["banners"]) +
            len(artwork_data["themes"])
        )

        return {
            "info": {
                "title": item.title,
                "year": getattr(item, 'year', None),
                "type": item.type,
                "rating_key": item.ratingKey,
                "guid": item.guid if hasattr(item, 'guid') else None,
                "parent_title": getattr(item, 'parentTitle', None) if item.type == 'season' else None
            },
            "artwork": artwork_data,
            "total_artwork": total_artwork,
            "has_custom_artwork": uploads_file_count > 0,  # NEW: Flag for frontend
            "custom_artwork_count": uploads_file_count  # NEW: How many deletable files
        }

    def _get_uploads_file_count(self, item, debug: bool = False) -> int:
        """
        Check how many actual artwork files exist in the Uploads folder.
        Returns count of deletable files.
        """
        try:
            if not hasattr(item, 'metadataDirectory'):
                if debug:
                    print(f"    [uploads_check] No metadataDirectory property")
                return 0

            metadata_dir_raw = item.metadataDirectory
            metadata_dir = Path(metadata_dir_raw)

            if debug:
                print(f"    [uploads_check] Raw path: {metadata_dir_raw}")

            # Resolve relative paths
            if not metadata_dir.is_absolute():
                try:
                    transcoder_path = self.plex.transcodeDirectory
                    plex_data_dir = Path(transcoder_path).parent
                    metadata_dir = plex_data_dir / metadata_dir_raw
                    if debug:
                        print(f"    [uploads_check] Resolved via transcoder: {metadata_dir}")
                except Exception:
                    system = platform.system()
                    if system == 'Windows':
                        plex_data_dir = Path(os.environ.get('LOCALAPPDATA')) / "Plex Media Server"
                    elif system == 'Darwin':
                        plex_data_dir = Path.home() / "Library" / "Application Support" / "Plex Media Server"
                    else:
                        plex_data_dir = Path("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server")
                    metadata_dir = plex_data_dir / metadata_dir_raw
                    if debug:
                        print(f"    [uploads_check] Resolved via platform default: {metadata_dir}")

            if not metadata_dir.exists():
                if debug:
                    print(f"    [uploads_check] ✗ Metadata directory does not exist: {metadata_dir}")
                return 0

            if debug:
                print(f"    [uploads_check] ✓ Metadata directory exists: {metadata_dir}")

            # Check what's actually in the metadata directory
            if debug:
                try:
                    contents = list(metadata_dir.iterdir())
                    print(f"    [uploads_check] Contents: {[f.name for f in contents[:10]]}")
                except Exception as e:
                    print(f"    [uploads_check] Could not list directory: {e}")

            uploads_dir = metadata_dir / "Uploads"
            if not uploads_dir.exists():
                if debug:
                    print(f"    [uploads_check] ✗ No Uploads folder at: {uploads_dir}")
                return 0

            if debug:
                print(f"    [uploads_check] ✓ Uploads folder exists: {uploads_dir}")

            # Count .jpg, .jpeg, .png files in Uploads subfolders
            # Structure: Uploads/posters/*.jpg, Uploads/art/*.jpg, Uploads/themes/*.mp3
            file_count = 0
            all_files = []

            # Check multiple subfolder patterns (posters, art, backgrounds, etc.)
            subfolders = ['posters', 'art', 'backgrounds', 'banners', 'themes']

            for subfolder in subfolders:
                subfolder_path = uploads_dir / subfolder
                if subfolder_path.exists():
                    # FIX: Plex stores files WITHOUT extensions, so look for all files
                    # Changed from looking for *.jpg, *.jpeg, *.png to all files
                    files = [f for f in subfolder_path.iterdir() if f.is_file()]
                    if files:
                        file_count += len(files)
                        if debug:
                            all_files.extend([f"{subfolder}/{f.name}" for f in files])

                    # Also check season subfolders (e.g., posters/seasons/1/)
                    if subfolder == 'posters':
                        seasons_dir = subfolder_path / 'seasons'
                        if seasons_dir.exists():
                            for season_folder in seasons_dir.iterdir():
                                if season_folder.is_dir():
                                    season_files = [f for f in season_folder.iterdir() if f.is_file()]
                                    if season_files:
                                        file_count += len(season_files)
                                        if debug:
                                            all_files.extend([f"{subfolder}/seasons/{season_folder.name}/{f.name}" for f in season_files])

            # Also check root Uploads folder (some setups might put files there directly)
            root_files = [f for f in uploads_dir.iterdir() if f.is_file()]
            if root_files:
                file_count += len(root_files)
                if debug:
                    all_files.extend([f.name for f in root_files])

            if debug:
                if file_count > 0:
                    print(f"    [uploads_check] ✓ Found {file_count} file(s): {all_files[:5]}")
                else:
                    # Check if there are ANY files in Uploads folder
                    try:
                        all_contents = list(uploads_dir.iterdir())
                        print(f"    [uploads_check] ✗ No .jpg/.png files, but folder has: {[f.name for f in all_contents[:5]]}")
                    except Exception as e:
                        print(f"    [uploads_check] ✗ Could not list Uploads folder: {e}")

            return file_count

        except Exception as e:
            if debug:
                print(f"    [uploads_check] ERROR: {e}")
                import traceback
                traceback.print_exc()
            return 0

    def delete_artwork(self, item_rating_key: str, artwork_path: str) -> Dict:
        """
        Delete artwork FILES from disk (not just unlock in Plex).

        This method finds the actual .jpg/.png files in the Plex Metadata folder
        and deletes them using the FileManager backup system.

        Args:
            item_rating_key: Plex rating key for the item (show/movie)
            artwork_path: Full path like "303344/poster/poster_0"

        Returns:
            Dict with success status, files deleted, bytes freed, and backup info
        """
        print(f"\n[delete_artwork] Processing FILESYSTEM deletion request")
        print(f"[delete_artwork] Item rating key: {item_rating_key}")
        print(f"[delete_artwork] Artwork path: {artwork_path}")

        try:
            # Parse path to get artwork type
            # Format: "item_rating_key/artwork_type/artwork_id"
            parts = artwork_path.split('/')
            if len(parts) != 3:
                return {
                    "success": False,
                    "error": f"Invalid artwork path format: {artwork_path}"
                }

            _, artwork_type, artwork_id = parts
            print(f"[delete_artwork] Type: {artwork_type}, ID: {artwork_id}")

            # Fetch the item from Plex
            print(f"[delete_artwork] Fetching item with rating key: {item_rating_key}")
            try:
                item = self.plex.fetchItem(int(item_rating_key))
                print(f"[delete_artwork] Found item: {item.title}")
            except Exception as e:
                print(f"[delete_artwork] fetchItem failed: {e}, trying alternative method...")
                # Alternative: search through all libraries
                for section in self.plex.library.sections():
                    try:
                        item = section.fetchItem(int(item_rating_key))
                        print(f"[delete_artwork] Found item via library search: {item.title}")
                        break
                    except:
                        continue
                else:
                    raise Exception(f"Could not find item with rating key: {item_rating_key}")

            # Get the metadata directory for this item
            if not hasattr(item, 'metadataDirectory'):
                return {
                    "success": False,
                    "error": f"Item type '{item.type}' does not have metadataDirectory property"
                }

            metadata_dir_raw = item.metadataDirectory
            print(f"[delete_artwork] Raw metadata directory: {metadata_dir_raw}")

            # PlexAPI sometimes returns relative paths like "Metadata\\TV Shows\\..."
            # We need to convert to absolute path using Plex data directory
            metadata_dir = Path(metadata_dir_raw)

            if not metadata_dir.is_absolute():
                # Get Plex data directory from server
                print(f"[delete_artwork] Path is relative, finding Plex data directory...")

                # Try to get from Plex server transcoder path
                try:
                    # The transcoder path typically points to the Plex data directory
                    # Example: "C:\Users\...\AppData\Local\Plex Media Server\Plex Transcoder.exe"
                    transcoder_path = self.plex.transcodeDirectory
                    plex_data_dir = Path(transcoder_path).parent
                    metadata_dir = plex_data_dir / metadata_dir_raw
                    print(f"[delete_artwork] Resolved to absolute path: {metadata_dir}")
                except Exception as e:
                    print(f"[delete_artwork] Could not resolve via transcoder path: {e}")

                    # Fallback: Try common Plex data directory locations
                    system = platform.system()

                    if system == 'Windows':
                        plex_data_dir = Path(os.environ.get('LOCALAPPDATA')) / "Plex Media Server"
                    elif system == 'Darwin':  # macOS
                        plex_data_dir = Path.home() / "Library" / "Application Support" / "Plex Media Server"
                    else:  # Linux
                        plex_data_dir = Path("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server")

                    metadata_dir = plex_data_dir / metadata_dir_raw
                    print(f"[delete_artwork] Using platform default: {metadata_dir}")

            print(f"[delete_artwork] Final metadata directory: {metadata_dir}")

            if not metadata_dir.exists():
                return {
                    "success": False,
                    "error": f"Metadata directory does not exist: {metadata_dir}",
                    "info": f"Tried to resolve relative path '{metadata_dir_raw}' but directory not found"
                }

            # Look for Uploads subfolder
            uploads_dir = metadata_dir / "Uploads"
            print(f"[delete_artwork] Checking uploads directory: {uploads_dir}")

            if not uploads_dir.exists():
                print(f"[delete_artwork] No Uploads folder found - no custom artwork to delete")
                return {
                    "success": False,
                    "error": f"No Uploads folder found in {metadata_dir}",
                    "info": "This item has no custom uploaded artwork to delete"
                }

            # Find artwork files in Uploads folder and subfolders
            # Structure: Uploads/posters/*.jpg, Uploads/art/*.jpg, etc.
            artwork_files = []

            # Check subfolders first (posters, art, backgrounds, banners, themes)
            subfolders = ['posters', 'art', 'backgrounds', 'banners', 'themes']
            for subfolder in subfolders:
                subfolder_path = uploads_dir / subfolder
                if subfolder_path.exists():
                    # FIX: Plex stores files WITHOUT extensions, so look for all files
                    # Changed from looking for *.jpg, *.jpeg, *.png to all files
                    files = [f for f in subfolder_path.iterdir() if f.is_file()]
                    artwork_files.extend(files)

                    # Also check season subfolders (e.g., posters/seasons/1/)
                    if subfolder == 'posters':
                        seasons_dir = subfolder_path / 'seasons'
                        if seasons_dir.exists():
                            for season_folder in seasons_dir.iterdir():
                                if season_folder.is_dir():
                                    season_files = [f for f in season_folder.iterdir() if f.is_file()]
                                    artwork_files.extend(season_files)

            # Also check root Uploads folder (some setups might put files there directly)
            root_files = [f for f in uploads_dir.iterdir() if f.is_file()]
            artwork_files.extend(root_files)

            if not artwork_files:
                print(f"[delete_artwork] No artwork files found in Uploads folder or subfolders")
                return {
                    "success": False,
                    "error": "No artwork files found in Uploads folder",
                    "info": "Uploads folder exists but contains no image files in posters/art/backgrounds subfolders"
                }

            print(f"[delete_artwork] Found {len(artwork_files)} artwork files to delete")
            for f in artwork_files:
                print(f"  - {f.name} ({f.stat().st_size} bytes)")

            # Initialize file manager with backup directory from config
            from file_manager import FileManager
            import json
            config_path = Path(__file__).parent.parent / "config.json"
            backup_dir = None
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    backup_dir = config.get('backup_directory')

            file_manager = FileManager(backup_dir=backup_dir)

            # Delete files using file manager (moves to backup)
            deleted_files = []
            total_bytes = 0
            failed = []

            for artwork_file in artwork_files:
                file_size = artwork_file.stat().st_size
                result = file_manager.delete_file(
                    str(artwork_file),
                    reason=f"Deleted via Plex Poster Manager - {item.title}"
                )

                if result['success']:
                    deleted_files.append(str(artwork_file))
                    total_bytes += file_size
                    print(f"[delete_artwork] ✓ Deleted: {artwork_file.name} ({file_size} bytes)")
                else:
                    failed.append({
                        "file": str(artwork_file),
                        "error": result.get('error')
                    })
                    print(f"[delete_artwork] ✗ Failed: {artwork_file.name} - {result.get('error')}")

            # Trigger Plex to refresh metadata after file deletion
            print(f"[delete_artwork] Triggering Plex metadata refresh...")
            try:
                item.refresh()
                print(f"[delete_artwork] ✓ Plex refresh triggered")
            except Exception as e:
                print(f"[delete_artwork] Warning: Plex refresh failed: {e}")

            if deleted_files:
                print(f"[delete_artwork] ✓ Successfully deleted {len(deleted_files)} files ({total_bytes} bytes)")
                return {
                    "success": True,
                    "deleted_count": len(deleted_files),
                    "deleted_files": deleted_files,
                    "bytes_freed": total_bytes,
                    "mb_freed": round(total_bytes / (1024 * 1024), 2),
                    "failed": failed,
                    "item_title": item.title,
                    "message": f"Deleted {len(deleted_files)} artwork files for {item.title} ({round(total_bytes / (1024 * 1024), 2)} MB freed)"
                }
            else:
                return {
                    "success": False,
                    "error": "All file deletions failed",
                    "failed": failed
                }

        except NotFound:
            error = f"Item not found with rating key: {item_rating_key}"
            print(f"[delete_artwork] ERROR: {error}")
            return {"success": False, "error": error}
        except Exception as e:
            error = f"Failed to delete artwork: {str(e)}"
            print(f"[delete_artwork] ERROR: {error}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": error}

    def refresh_metadata(self, rating_key: str) -> bool:
        """
        Trigger Plex to refresh metadata for an item.

        Args:
            rating_key: Plex rating key for the item

        Returns:
            True if successful
        """
        try:
            item = self.plex.fetchItem(rating_key)
            item.refresh()
            print(f"[refresh_metadata] Triggered refresh for: {item.title}")
            return True
        except Exception as e:
            print(f"[refresh_metadata] ERROR: {e}")
            return False


def detect_plex_url() -> Optional[str]:
    """
    Auto-detect local Plex server URL.

    Returns:
        Plex server URL or None
    """
    # Try common local URLs
    common_urls = [
        "http://localhost:32400",
        "http://127.0.0.1:32400",
        "http://0.0.0.0:32400"
    ]

    import requests

    for url in common_urls:
        try:
            response = requests.get(f"{url}/identity", timeout=2)
            if response.status_code == 200:
                print(f"[detect_plex_url] Found Plex server at: {url}")
                return url
        except:
            continue

    print(f"[detect_plex_url] No local Plex server found")
    return None
