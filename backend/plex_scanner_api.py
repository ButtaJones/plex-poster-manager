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
                    if item_data['total_artwork'] > 0:
                        return item_data
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
            print(f"[scan_library] Total items with artwork: {len(items)}")
            print(f"[scan_library] Total artwork files: {sum(item['total_artwork'] for item in items)}")

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
                rating_key = poster.ratingKey if hasattr(poster, 'ratingKey') else f"poster_{idx}"
                artwork_data["posters"].append({
                    "path": f"{item.ratingKey}/poster/{rating_key}",  # Unique path for React keys
                    "provider": poster.provider if hasattr(poster, 'provider') else "unknown",
                    "selected": poster.selected if hasattr(poster, 'selected') else False,
                    "thumb_url": self._build_thumb_url(poster.thumb, item.ratingKey),
                    "rating_key": rating_key,
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
                rating_key = art.ratingKey if hasattr(art, 'ratingKey') else f"art_{idx}"
                artwork_data["art"].append({
                    "path": f"{item.ratingKey}/art/{rating_key}",  # Unique path for React keys
                    "provider": art.provider if hasattr(art, 'provider') else "unknown",
                    "selected": art.selected if hasattr(art, 'selected') else False,
                    "thumb_url": self._build_thumb_url(art.thumb, item.ratingKey),
                    "rating_key": rating_key,
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
                rating_key = banner.ratingKey if hasattr(banner, 'ratingKey') else f"banner_{idx}"
                artwork_data["banners"].append({
                    "path": f"{item.ratingKey}/banner/{rating_key}",  # Unique path for React keys
                    "provider": banner.provider if hasattr(banner, 'provider') else "unknown",
                    "selected": banner.selected if hasattr(banner, 'selected') else False,
                    "thumb_url": self._build_thumb_url(banner.thumb, item.ratingKey),
                    "rating_key": rating_key,
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
                rating_key = theme.ratingKey if hasattr(theme, 'ratingKey') else f"theme_{idx}"
                artwork_data["themes"].append({
                    "path": f"{item.ratingKey}/theme/{rating_key}",  # Unique path for React keys
                    "provider": theme.provider if hasattr(theme, 'provider') else "unknown",
                    "selected": theme.selected if hasattr(theme, 'selected') else False,
                    "thumb_url": self._build_thumb_url(theme.thumb, item.ratingKey),
                    "rating_key": rating_key,
                    "type": "theme"
                })
        except Exception as e:
            if detailed:
                print(f"  [artwork] No themes available: {e}")

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
            "total_artwork": total_artwork
        }

    def delete_artwork(self, rating_key: str, artwork_type: str) -> bool:
        """
        Delete/unlock artwork for an item.

        Note: Plex API doesn't directly delete artwork files from disk.
        Instead, it can unlock artwork to allow Plex to re-fetch from agents.

        Args:
            rating_key: Plex rating key for the artwork
            artwork_type: Type of artwork (poster, art, banner, theme)

        Returns:
            True if successful
        """
        # TODO: Implement artwork deletion/unlocking via Plex API
        # This requires using the Plex API endpoint to unlock poster
        print(f"[delete_artwork] Unlocking {artwork_type} with rating_key: {rating_key}")
        return False

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
