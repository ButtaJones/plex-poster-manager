"""
Plex Scanner Module
Scans Plex metadata bundles and extracts artwork for management.

SIMPLIFIED APPROACH (Proven by Testing):
- Bundle folder hashes are NOT stored in Plex database
- Plex generates bundle hashes from metadata GUIDs (one-way, not reversible)
- This scanner simply finds bundles and extracts artwork
- Users identify what to delete visually from thumbnails (better UX!)
- No database lookups needed - just pure filesystem scanning
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib


class PlexScanner:
    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        self.cache = {}

        print(f"[PlexScanner] Initialized with path: {self.metadata_path}")
        print(f"[PlexScanner] Path exists: {self.metadata_path.exists()}")
        print(f"[PlexScanner] Path is directory: {self.metadata_path.is_dir() if self.metadata_path.exists() else 'N/A'}")
        print(f"[PlexScanner] SIMPLIFIED MODE: Artwork-only scanning (no database)")
        print(f"[PlexScanner] Users will identify items visually from thumbnails")

    def debug_database(self):
        """Inspect database structure and sample data to understand schema."""
        print("\n" + "=" * 60)
        print("[DEBUG] INSPECTING PLEX DATABASE")
        print("=" * 60)

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get table schema
            print("\n[DEBUG] metadata_items table schema:")
            cursor.execute("PRAGMA table_info(metadata_items)")
            columns = cursor.fetchall()
            for col in columns:
                col_id, name, col_type, notnull, default, pk = col
                print(f"  [{col_id}] {name} ({col_type})")

            # Get sample row to see actual data
            print("\n[DEBUG] Sample row from metadata_items:")
            cursor.execute("SELECT * FROM metadata_items LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                for i, col in enumerate(columns):
                    value = sample[i]
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {col[1]}: {value}")

            # Check if hash field exists and sample values
            print("\n[DEBUG] Checking 'hash' field for TV shows:")
            cursor.execute("""
                SELECT hash, title, year
                FROM metadata_items
                WHERE metadata_type = 2
                LIMIT 5
            """)
            results = cursor.fetchall()
            if results:
                print("[DEBUG] Sample TV show hashes:")
                for hash_val, title, year in results:
                    print(f"  {hash_val} -> {title} ({year})")
            else:
                print("[DEBUG] No TV shows found with metadata_type = 2")

            # Count items by type
            print("\n[DEBUG] Item counts by metadata_type:")
            cursor.execute("""
                SELECT metadata_type, COUNT(*)
                FROM metadata_items
                GROUP BY metadata_type
            """)
            for meta_type, count in cursor.fetchall():
                type_name = {1: "movie", 2: "show", 3: "season", 4: "episode"}.get(meta_type, f"type_{meta_type}")
                print(f"  {type_name} ({meta_type}): {count}")

            # Check actual bundle folder names
            print("\n[DEBUG] Comparing with actual bundle folders:")
            bundles = list(self.metadata_path.rglob("*.bundle"))[:3]
            for bundle in bundles:
                bundle_hash = bundle.name.replace('.bundle', '')
                print(f"  Bundle folder: {bundle_hash[:20]}...")

                # Try to find this hash in database
                cursor.execute("""
                    SELECT title FROM metadata_items WHERE hash = ?
                """, (bundle_hash,))
                result = cursor.fetchone()
                if result:
                    print(f"    [OK] FOUND in DB: {result[0]}")
                else:
                    print(f"    [X] NOT FOUND in database")

            # CRITICAL: Investigate media_items and media_parts tables
            # The bundle hash might be in file paths, not in metadata_items.hash!
            print("\n[DEBUG] Investigating media_items table:")
            cursor.execute("PRAGMA table_info(media_items)")
            media_items_cols = cursor.fetchall()
            print(f"  Columns: {[col[1] for col in media_items_cols]}")

            print("\n[DEBUG] Investigating media_parts table:")
            cursor.execute("PRAGMA table_info(media_parts)")
            media_parts_cols = cursor.fetchall()
            print(f"  Columns: {[col[1] for col in media_parts_cols]}")

            # Sample media_parts data to see if file paths contain bundle hashes
            print("\n[DEBUG] Sample media_parts rows (first 3):")
            cursor.execute("SELECT * FROM media_parts LIMIT 3")
            for row in cursor.fetchall():
                print(f"  {row}")

            # Try to find bundle hash in media_parts file paths
            if bundles:
                test_bundle = bundles[0].name.replace('.bundle', '')
                print(f"\n[DEBUG] Searching for bundle hash in media_parts.file:")
                print(f"  Looking for: {test_bundle[:20]}...")
                cursor.execute("SELECT file FROM media_parts WHERE file LIKE ? LIMIT 3", (f"%{test_bundle}%",))
                results = cursor.fetchall()
                if results:
                    print(f"  [OK] FOUND in media_parts!")
                    for row in results:
                        print(f"    File path: {row[0]}")
                else:
                    print(f"  [X] NOT FOUND in media_parts.file")

                    # Try searching for just the first 10 chars of bundle hash
                    short_hash = test_bundle[:10]
                    print(f"\n[DEBUG] Searching for partial hash: {short_hash}...")
                    cursor.execute("SELECT file FROM media_parts WHERE file LIKE ? LIMIT 3", (f"%{short_hash}%",))
                    results = cursor.fetchall()
                    if results:
                        print(f"  [OK] FOUND partial match!")
                        for row in results:
                            print(f"    File path: {row[0]}")

            conn.close()

        except Exception as e:
            print(f"[DEBUG] Error inspecting database: {e}")
            import traceback
            traceback.print_exc()

        print("=" * 60 + "\n")

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

        SIMPLIFIED APPROACH:
        - Bundle folder names are NOT in the database (proven by testing)
        - Just return artwork grouped by bundle
        - Users can visually identify what to delete from thumbnails
        - This is actually BETTER UX than trying to show titles!
        """
        print(f"\n[scan_library] Starting scan of library: '{library}'")
        print(f"[scan_library] SIMPLIFIED MODE: Artwork-only (no database lookups)")
        bundles = self.find_bundles(library)
        total = len(bundles)
        print(f"[scan_library] Found {total} bundles to process")

        results = []
        bundles_without_artwork = 0

        for idx, bundle_path in enumerate(bundles):
            if progress_callback:
                progress_callback(idx + 1, total)

            # Print progress every 100 bundles or first 5
            if idx % 100 == 0 or idx < 5:
                print(f"\n[scan_library] Processing bundle {idx+1}/{total}: {bundle_path.name}")

            # Get artwork from filesystem
            artwork = self.get_artwork_files(bundle_path)
            total_artwork = sum(len(v) for v in artwork.values())

            if idx < 5:
                print(f"[scan_library] Found {total_artwork} artwork files")

            if total_artwork > 0:
                # Extract bundle hash for display
                bundle_hash = bundle_path.name.replace('.bundle', '')

                # Return simple bundle info
                results.append({
                    "bundle_path": str(bundle_path),
                    "bundle_name": bundle_path.name,
                    "info": {
                        "title": f"Bundle {bundle_hash[:12]}",
                        "type": "unknown",
                        "year": "",
                        "studio": "",
                        "guid": "",
                        "rating_key": "",
                        "parent_title": ""
                    },
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
