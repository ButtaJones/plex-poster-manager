"""
Plex Scanner Module
Scans Plex metadata bundles and extracts artwork for management.

HYBRID APPROACH (Best Solution - Thanks to Gemini & Grok LLMs!):
- Parse Info.xml files INSIDE bundles to get real show titles (offline!)
- Bundle hashes are NOT in database (proven by testing)
- Info.xml files exist at: Contents/<agent>/Info.xml (e.g., com.plexapp.agents.thetvdb)
- Fallback to bundle hash for bundles without Info.xml
- No database queries needed - pure filesystem + XML parsing
- Works 100% offline, no Plex token required
"""

import os
import xml.etree.ElementTree as ET
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
        print(f"[PlexScanner] HYBRID MODE: XML parsing for real titles + artwork scanning")
        print(f"[PlexScanner] Parses Info.xml inside bundles (offline, no database/token needed)")

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
        """Parse Info.xml from a bundle to extract metadata.

        Checks multiple agent-specific locations:
        - Contents/com.plexapp.agents.thetvdb/Info.xml
        - Contents/com.plexapp.agents.themoviedb/Info.xml
        - Contents/com.plexapp.agents.imdb/Info.xml
        - Contents/Info.xml (fallback)
        """
        # Try agent-specific locations first (most reliable)
        agent_candidates = [
            bundle_path / "Contents" / "com.plexapp.agents.thetvdb" / "Info.xml",
            bundle_path / "Contents" / "com.plexapp.agents.themoviedb" / "Info.xml",
            bundle_path / "Contents" / "com.plexapp.agents.imdb" / "Info.xml",
            bundle_path / "Contents" / "com.plexapp.agents.localmedia" / "Info.xml"
        ]

        # Fallback locations
        fallback_candidates = [
            bundle_path / "Contents" / "Info.xml",
            bundle_path / "Info.xml",
            bundle_path / "Contents" / "_combined" / "Info.xml"
        ]

        candidates = agent_candidates + fallback_candidates

        for info_path in candidates:
            if info_path.exists():
                try:
                    # Parse the XML
                    tree = ET.parse(info_path)
                    root = tree.getroot()

                    # Try different XML structures that Plex might use

                    # Structure 1: MediaContainer > Directory
                    directory = root.find(".//Directory")
                    if directory is not None:
                        return {
                            "title": directory.attrib.get("title", "Unknown"),
                            "type": directory.attrib.get("type", "unknown"),
                            "key": directory.attrib.get("key", ""),
                            "parent_title": directory.attrib.get("parentTitle", ""),
                            "year": directory.attrib.get("year", ""),
                            "guid": directory.attrib.get("guid", ""),
                            "rating_key": directory.attrib.get("ratingKey", ""),
                            "studio": ""
                        }

                    # Structure 2: MediaContainer > Video
                    video = root.find(".//Video")
                    if video is not None:
                        return {
                            "title": video.attrib.get("title", "Unknown"),
                            "type": video.attrib.get("type", "unknown"),
                            "key": video.attrib.get("key", ""),
                            "parent_title": video.attrib.get("grandparentTitle", ""),
                            "year": video.attrib.get("year", ""),
                            "guid": video.attrib.get("guid", ""),
                            "rating_key": video.attrib.get("ratingKey", ""),
                            "studio": ""
                        }

                    # Structure 3: Root IS MediaContainer with attributes
                    if root.tag == "MediaContainer" and root.attrib:
                        return {
                            "title": root.attrib.get("title", root.attrib.get("title1", "Unknown")),
                            "type": root.attrib.get("type", "unknown"),
                            "key": root.attrib.get("key", ""),
                            "parent_title": root.attrib.get("parentTitle", ""),
                            "year": root.attrib.get("year", ""),
                            "guid": root.attrib.get("guid", ""),
                            "rating_key": root.attrib.get("ratingKey", ""),
                            "studio": ""
                        }

                except (ET.ParseError, Exception):
                    # Failed to parse this XML, try next candidate
                    continue

        # No valid Info.xml found
        return None
    
    def get_artwork_files(self, bundle_path: Path) -> Dict[str, List[Dict]]:
        """Get all artwork files from a bundle (modern Plex structure 2024/2025).

        Modern Plex stores artwork in:
        - Contents/_combined/<type>/ (selected artwork - symlinks/copies)
        - Contents/<agent>/<type>/ (agent-specific caches, e.g., com.plexapp.agents.thetvdb)
        - Uploads/<type>/ (user-uploaded custom artwork)

        OLD structure (bundle/Posters/) is no longer used in modern Plex!
        """
        artwork = {
            "posters": [],
            "art": [],
            "backgrounds": [],
            "banners": [],
            "themes": []
        }

        # Modern Plex locations to check
        search_bases = [
            bundle_path / "Contents" / "_combined",  # Selected artwork (priority)
            bundle_path / "Uploads"  # User uploads
        ]

        # Also scan agent-specific folders (com.plexapp.agents.*)
        contents_path = bundle_path / "Contents"
        if contents_path.exists():
            try:
                for agent_dir in contents_path.iterdir():
                    if agent_dir.is_dir() and agent_dir.name.startswith("com.plexapp.agents."):
                        search_bases.append(agent_dir)
            except Exception:
                pass  # Skip if can't read Contents/

        # Map folder names to artwork types (lowercase for modern Plex)
        folder_mapping = {
            "posters": "posters",
            "art": "art",
            "backgrounds": "backgrounds",
            "banners": "banners",
            "themes": "themes"
        }

        # Scan all locations
        for base_path in search_bases:
            if not base_path.exists():
                continue

            for folder_name, artwork_type in folder_mapping.items():
                folder_path = base_path / folder_name
                if folder_path.exists() and folder_path.is_dir():
                    try:
                        for file_path in folder_path.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                                # Determine source from path
                                if "_combined" in str(base_path):
                                    source = "selected"
                                elif "Uploads" in str(base_path):
                                    source = "uploaded"
                                elif "com.plexapp.agents." in str(base_path):
                                    # Extract agent name (e.g., thetvdb, themoviedb)
                                    agent = base_path.name.replace("com.plexapp.agents.", "")
                                    source = agent
                                else:
                                    source = "unknown"

                                # Get file info
                                file_stat = file_path.stat()

                                artwork[artwork_type].append({
                                    "path": str(file_path),
                                    "filename": file_path.name,
                                    "source": source,
                                    "location": base_path.name,  # _combined, Uploads, or agent name
                                    "size": file_stat.st_size,
                                    "modified": file_stat.st_mtime,
                                    "hash": self._get_file_hash(file_path)
                                })
                    except Exception:
                        # Skip folders we can't read
                        continue

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

        HYBRID APPROACH (Best of Both Worlds):
        - Parse Info.xml files in bundles to get real show titles (offline, no database!)
        - Fallback to bundle hash for bundles without Info.xml
        - Users see real titles when available, visual identification when not
        """
        print(f"\n[scan_library] Starting scan of library: '{library}'")
        print(f"[scan_library] HYBRID MODE: XML parsing for titles + artwork scanning")
        bundles = self.find_bundles(library)
        total = len(bundles)
        print(f"[scan_library] Found {total} bundles to process")

        results = []
        bundles_without_artwork = 0
        xml_title_count = 0
        hash_title_count = 0

        for idx, bundle_path in enumerate(bundles):
            if progress_callback:
                progress_callback(idx + 1, total)

            # Print progress every 100 bundles or first 5
            if idx % 100 == 0 or idx < 5:
                print(f"\n[scan_library] Processing bundle {idx+1}/{total}: {bundle_path.name}")

            # Get artwork from filesystem
            artwork = self.get_artwork_files(bundle_path)
            total_artwork = sum(len(v) for v in artwork.values())

            if total_artwork > 0:
                # Extract bundle hash for fallback
                bundle_hash = bundle_path.name.replace('.bundle', '')

                # Try to get title from Info.xml in bundle
                xml_info = self.parse_info_xml(bundle_path)

                if xml_info:
                    # Use real title from XML!
                    info = xml_info
                    xml_title_count += 1
                    if idx < 5:
                        print(f"[scan_library] Title from XML: {info['title']}")
                        print(f"[scan_library] Found {total_artwork} artwork files")
                else:
                    # Fallback to bundle hash
                    info = {
                        "title": f"Bundle {bundle_hash[:12]}",
                        "type": "unknown",
                        "year": "",
                        "studio": "",
                        "guid": "",
                        "rating_key": "",
                        "parent_title": ""
                    }
                    hash_title_count += 1
                    if idx < 5:
                        print(f"[scan_library] No XML found, using hash: {info['title']}")
                        print(f"[scan_library] Found {total_artwork} artwork files")

                results.append({
                    "bundle_path": str(bundle_path),
                    "bundle_name": bundle_path.name,
                    "info": info,
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
        print(f"  - Titles from XML (real titles): {xml_title_count}")
        print(f"  - Titles from hash (fallback): {hash_title_count}")

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
