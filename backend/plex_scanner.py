"""
Plex Scanner Module
Scans Plex metadata bundles and extracts information about shows, seasons, and their artwork.

ARCHITECTURE (Modern Plex):
- Metadata (titles, summaries) stored in SQLite database
- Artwork (posters, backgrounds) stored in filesystem bundles
- Bundle hash maps to database hash column
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import hashlib


class PlexScanner:
    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        self.cache = {}

        # Find Plex database (go up from Metadata/ to Plex Media Server root)
        plex_root = self.metadata_path.parent.parent
        self.db_path = plex_root / "Plug-in Support" / "Databases" / "com.plexapp.plugins.library.db"

        print(f"[PlexScanner] Initialized with path: {self.metadata_path}")
        print(f"[PlexScanner] Path exists: {self.metadata_path.exists()}")
        print(f"[PlexScanner] Path is directory: {self.metadata_path.is_dir() if self.metadata_path.exists() else 'N/A'}")
        print(f"[PlexScanner] Database path: {self.db_path}")
        print(f"[PlexScanner] Database exists: {self.db_path.exists()}")

    def validate_path(self) -> bool:
        """Validate that the provided path exists and looks like a Plex metadata directory."""
        print(f"\n[validate_path] Checking path: {self.metadata_path}")

        if not self.metadata_path.exists():
            print(f"[validate_path] ERROR: Path does not exist!")
            return False

        if not self.metadata_path.is_dir():
            print(f"[validate_path] ERROR: Path is not a directory!")
            return False

        # List contents of the directory
        print(f"[validate_path] Directory contents:")
        try:
            for item in self.metadata_path.iterdir():
                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
        except Exception as e:
            print(f"[validate_path] ERROR listing directory: {e}")
            return False

        # Check for common Plex metadata folder structure
        has_tv = (self.metadata_path / "TV Shows").exists()
        has_movies = (self.metadata_path / "Movies").exists()

        print(f"[validate_path] Has 'TV Shows' subdirectory: {has_tv}")
        print(f"[validate_path] Has 'Movies' subdirectory: {has_movies}")

        # Also check if this IS the TV Shows directory (user might have pointed directly to it)
        is_tv_shows_dir = self.metadata_path.name == "TV Shows"
        print(f"[validate_path] Is this the 'TV Shows' directory itself: {is_tv_shows_dir}")

        return has_tv or has_movies or is_tv_shows_dir
    
    def get_libraries(self) -> List[str]:
        """Get list of available libraries (TV Shows, Movies, etc.)."""
        libraries = []
        for item in self.metadata_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                libraries.append(item.name)
        return libraries
    
    def get_title_from_db(self, bundle_hash: str) -> Dict:
        """Get title and metadata from Plex database by bundle hash.

        Args:
            bundle_hash: The bundle folder name without .bundle extension

        Returns:
            Dict with title, type, year, etc. from database
        """
        if not self.db_path.exists():
            print(f"[get_title_from_db] Database not found, using hash as title")
            return {
                "title": f"Bundle {bundle_hash[:12]}",
                "type": "unknown",
                "year": "",
                "studio": "",
                "guid": "",
                "rating_key": "",
                "parent_title": ""
            }

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Query metadata_items table by hash
            cursor.execute("""
                SELECT title, metadata_type, year, studio, summary, guid, id
                FROM metadata_items
                WHERE hash = ?
                LIMIT 1
            """, (bundle_hash,))

            result = cursor.fetchone()
            conn.close()

            if result:
                title, meta_type, year, studio, summary, guid, item_id = result

                # Map metadata_type to string
                type_map = {1: "movie", 2: "show", 3: "season", 4: "episode"}
                type_str = type_map.get(meta_type, "unknown")

                return {
                    "title": title or f"Bundle {bundle_hash[:12]}",
                    "type": type_str,
                    "year": str(year) if year else "",
                    "studio": studio or "",
                    "guid": guid or "",
                    "rating_key": str(item_id) if item_id else "",
                    "parent_title": ""
                }
            else:
                # Hash not found in database
                print(f"[get_title_from_db] Hash {bundle_hash[:12]}... not in database")
                return {
                    "title": f"Bundle {bundle_hash[:12]}",
                    "type": "unknown",
                    "year": "",
                    "studio": "",
                    "guid": "",
                    "rating_key": "",
                    "parent_title": ""
                }

        except Exception as e:
            print(f"[get_title_from_db] Error querying database: {e}")
            return {
                "title": f"Bundle {bundle_hash[:12]}",
                "type": "unknown",
                "year": "",
                "studio": "",
                "guid": "",
                "rating_key": "",
                "parent_title": ""
            }

    def find_bundles(self, library: str = "TV Shows") -> List[Path]:
        """Find all .bundle directories in a library."""
        print(f"\n[find_bundles] Looking for bundles in library: '{library}'")
        library_path = self.metadata_path / library
        print(f"[find_bundles] Library path: {library_path}")
        print(f"[find_bundles] Library path exists: {library_path.exists()}")

        if not library_path.exists():
            print(f"[find_bundles] ERROR: Library path does not exist!")
            # If the metadata_path itself might be the TV Shows directory, try scanning it directly
            if self.metadata_path.name == library or self.metadata_path.name == library.replace(" ", ""):
                print(f"[find_bundles] Metadata path itself appears to be the library directory, scanning it...")
                library_path = self.metadata_path
            else:
                return []

        bundles = []
        print(f"[find_bundles] Scanning directory tree...")
        try:
            for root, dirs, files in os.walk(library_path):
                for d in dirs:
                    if d.endswith(".bundle"):
                        bundle_path = Path(root) / d
                        bundles.append(bundle_path)
                        print(f"[find_bundles] Found bundle: {bundle_path.name}")
        except Exception as e:
            print(f"[find_bundles] ERROR during directory walk: {e}")

        print(f"[find_bundles] Total bundles found: {len(bundles)}")
        return bundles
    
    def parse_info_xml(self, bundle_path: Path) -> Optional[Dict]:
        """Parse Info.xml from a bundle to extract metadata."""
        # Try multiple possible locations for Info.xml (Plex uses different structures)
        candidates = [
            bundle_path / "Contents" / "Info.xml",
            bundle_path / "Info.xml",
            bundle_path / "Contents" / "_combined" / "Info.xml",
            bundle_path / "Contents" / "com.plexapp.agents.thetvdb" / "Info.xml",
            bundle_path / "Contents" / "com.plexapp.agents.themoviedb" / "Info.xml"
        ]

        if self.detailed_logging:
            print(f"\n[parse_info_xml] Parsing bundle: {bundle_path.name}")

        for info_path in candidates:
            if self.detailed_logging:
                print(f"[parse_info_xml]   Trying: {info_path}")
            if info_path.exists():
                if self.detailed_logging:
                    print(f"[parse_info_xml]   [OK] FOUND at: {info_path}")
                try:
                    # Read and show first part of file for debugging (only if detailed logging)
                    if self.detailed_logging:
                        with open(info_path, 'r', encoding='utf-8') as f:
                            first_chars = f.read(500)
                            print(f"[parse_info_xml]   First 500 chars of XML:")
                            print(f"   {first_chars[:500]}")

                    # Parse the XML
                    tree = ET.parse(info_path)
                    root = tree.getroot()

                    if self.detailed_logging:
                        print(f"[parse_info_xml]   Root tag: {root.tag}")
                        print(f"[parse_info_xml]   Root attribs: {root.attrib}")

                    # Try different XML structures that Plex might use

                    # Structure 1: MediaContainer > Directory
                    directory = root.find(".//Directory")
                    if directory is not None:
                        if self.detailed_logging:
                            print(f"[parse_info_xml]   Found <Directory> element")
                        result = {
                            "title": directory.attrib.get("title", "Unknown"),
                            "type": directory.attrib.get("type", "unknown"),
                            "key": directory.attrib.get("key", ""),
                            "parent_title": directory.attrib.get("parentTitle", ""),
                            "year": directory.attrib.get("year", ""),
                            "guid": directory.attrib.get("guid", ""),
                            "rating_key": directory.attrib.get("ratingKey", ""),
                            "info_xml_path": str(info_path)
                        }
                        if self.detailed_logging:
                            print(f"[parse_info_xml]   [OK] Successfully parsed: {result['title']}")
                        return result

                    # Structure 2: MediaContainer > Video
                    video = root.find(".//Video")
                    if video is not None:
                        if self.detailed_logging:
                            print(f"[parse_info_xml]   Found <Video> element")
                        result = {
                            "title": video.attrib.get("title", "Unknown"),
                            "type": video.attrib.get("type", "unknown"),
                            "key": video.attrib.get("key", ""),
                            "parent_title": video.attrib.get("grandparentTitle", ""),
                            "year": video.attrib.get("year", ""),
                            "guid": video.attrib.get("guid", ""),
                            "rating_key": video.attrib.get("ratingKey", ""),
                            "info_xml_path": str(info_path)
                        }
                        if self.detailed_logging:
                            print(f"[parse_info_xml]   [OK] Successfully parsed: {result['title']}")
                        return result

                    # Structure 3: Root IS MediaContainer with attributes
                    if root.tag == "MediaContainer" and root.attrib:
                        if self.detailed_logging:
                            print(f"[parse_info_xml]   Root is MediaContainer with attributes")
                        result = {
                            "title": root.attrib.get("title", root.attrib.get("title1", "Unknown")),
                            "type": root.attrib.get("type", "unknown"),
                            "key": root.attrib.get("key", ""),
                            "parent_title": root.attrib.get("parentTitle", ""),
                            "year": root.attrib.get("year", ""),
                            "guid": root.attrib.get("guid", ""),
                            "rating_key": root.attrib.get("ratingKey", ""),
                            "info_xml_path": str(info_path)
                        }
                        if self.detailed_logging:
                            print(f"[parse_info_xml]   [OK] Successfully parsed: {result['title']}")
                        return result

                    # If we get here, we found XML but couldn't parse it
                    if self.detailed_logging:
                        print(f"[parse_info_xml]   [X] Found XML but couldn't parse structure")
                        print(f"[parse_info_xml]   Available elements:")
                        for child in root:
                            print(f"     - {child.tag}: {child.attrib}")

                except ET.ParseError as e:
                    if self.detailed_logging:
                        print(f"[parse_info_xml]   [X] XML Parse Error: {e}")
                    continue
                except Exception as e:
                    if self.detailed_logging:
                        print(f"[parse_info_xml]   [X] Unexpected error: {e}")
                    continue
            else:
                if self.detailed_logging:
                    print(f"[parse_info_xml]   [X] Not found")

        if self.detailed_logging:
            print(f"[parse_info_xml]   [X] No valid Info.xml found in any location")
        return None
    
    def get_artwork_files(self, bundle_path: Path) -> Dict[str, List[Dict]]:
        """Get all artwork files from a bundle (posters, art, backgrounds, etc.)."""
        artwork = {
            "posters": [],
            "art": [],
            "backgrounds": [],
            "banners": [],
            "themes": []
        }
        
        # Map folder names to artwork types
        folder_mapping = {
            "Posters": "posters",
            "Art": "art",
            "Backgrounds": "backgrounds",
            "Banners": "banners",
            "Themes": "themes"
        }
        
        for folder_name, artwork_type in folder_mapping.items():
            folder_path = bundle_path / folder_name
            if folder_path.exists():
                for file_path in folder_path.iterdir():
                    if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                        # Extract source agent from filename
                        filename = file_path.name
                        source = self._extract_source_from_filename(filename)
                        
                        # Get file info
                        file_stat = file_path.stat()
                        
                        artwork[artwork_type].append({
                            "path": str(file_path),
                            "filename": filename,
                            "source": source,
                            "size": file_stat.st_size,
                            "modified": file_stat.st_mtime,
                            "hash": self._get_file_hash(file_path)
                        })
        
        return artwork
    
    def _extract_source_from_filename(self, filename: str) -> str:
        """Extract the source agent from a filename."""
        # Example: com.plexapp.agents.thetvdb_abc123.jpg -> thetvdb
        if "com.plexapp.agents." in filename:
            parts = filename.split("com.plexapp.agents.")[1]
            source = parts.split("_")[0].split(".")[0]
            return source
        elif "local" in filename.lower():
            return "local"
        else:
            return "unknown"
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of a file for duplicate detection."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def scan_library(self, library: str = "TV Shows", progress_callback=None) -> List[Dict]:
        """Scan an entire library and return all items with their artwork.

        Modern Plex Architecture:
        - Metadata (titles, etc.) stored in SQLite database
        - Artwork stored in filesystem bundles
        - This scanner queries database for titles + filesystem for artwork
        """
        print(f"\n[scan_library] Starting scan of library: '{library}'")
        print(f"[scan_library] Using Plex database for titles + filesystem for artwork")
        bundles = self.find_bundles(library)
        total = len(bundles)
        print(f"[scan_library] Found {total} bundles to process")

        if self.db_path.exists():
            print(f"[scan_library] Database found: {self.db_path}")
        else:
            print(f"[scan_library] WARNING: Database not found at {self.db_path}")
            print(f"[scan_library] Will use bundle hashes as titles")

        results = []
        bundles_without_artwork = 0
        db_hits = 0
        db_misses = 0

        for idx, bundle_path in enumerate(bundles):
            if progress_callback:
                progress_callback(idx + 1, total)

            # Print progress every 100 bundles or first 5
            if idx % 100 == 0 or idx < 5:
                print(f"\n[scan_library] Processing bundle {idx+1}/{total}: {bundle_path.name}")

            # Extract bundle hash (filename without .bundle extension)
            bundle_hash = bundle_path.name.replace('.bundle', '')

            # Get title from database
            info = self.get_title_from_db(bundle_hash)

            # Track database hits/misses
            if info["title"].startswith("Bundle "):
                db_misses += 1
            else:
                db_hits += 1

            # Get artwork from filesystem
            artwork = self.get_artwork_files(bundle_path)
            total_artwork = sum(len(v) for v in artwork.values())

            if idx < 5:
                print(f"[scan_library] Bundle hash: {bundle_hash[:16]}...")
                print(f"[scan_library] Title from DB: {info['title']}")
                print(f"[scan_library] Found {total_artwork} artwork files")

            if total_artwork > 0:
                # Combine database info + filesystem artwork
                results.append({
                    "bundle_path": str(bundle_path),
                    "bundle_name": bundle_path.name,
                    "info": info,  # Real title from database!
                    "artwork": artwork,
                    "total_artwork": total_artwork
                })
            else:
                bundles_without_artwork += 1

        print(f"\n[scan_library] Scan complete!")
        print(f"[scan_library] Results summary:")
        print(f"  - Total bundles scanned: {total}")
        print(f"  - Bundles with artwork (returned): {len(results)}")
        print(f"  - Bundles without artwork (skipped): {bundles_without_artwork}")
        print(f"  - Database hits (real titles): {db_hits}")
        print(f"  - Database misses (hash titles): {db_misses}")

        return results
    
    def find_duplicates(self, items: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Find duplicate artwork across items based on file hash."""
        hash_map = {}
        duplicates = []
        
        for item in items:
            for artwork_type, files in item["artwork"].items():
                for file_info in files:
                    file_hash = file_info["hash"]
                    if file_hash and file_hash in hash_map:
                        duplicates.append((hash_map[file_hash], file_info))
                    else:
                        hash_map[file_hash] = file_info
        
        return duplicates


def detect_plex_path() -> Optional[str]:
    """Auto-detect Plex metadata path based on OS."""
    import platform
    
    system = platform.system()
    
    if system == "Windows":
        # Windows default path
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            path = Path(local_appdata) / "Plex Media Server" / "Metadata"
            if path.exists():
                return str(path)
    
    elif system == "Darwin":  # macOS
        home = Path.home()
        path = home / "Library" / "Application Support" / "Plex Media Server" / "Metadata"
        if path.exists():
            return str(path)
    
    elif system == "Linux":
        # Try common Linux paths
        paths = [
            Path("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Metadata"),
            Path.home() / ".config" / "Plex Media Server" / "Metadata"
        ]
        for path in paths:
            if path.exists():
                return str(path)
    
    return None
