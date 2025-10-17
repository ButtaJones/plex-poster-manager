"""
File Manager Module
Handles safe deletion, backup, and restoration of artwork files.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class FileManager:
    def __init__(self, backup_dir: str = None):
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            # Default to app directory
            self.backup_dir = Path(__file__).parent.parent / "backups"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.operations_log = self.backup_dir / "operations.json"
        self._load_operations()
    
    def _load_operations(self):
        """Load operations history from JSON file."""
        if self.operations_log.exists():
            with open(self.operations_log, 'r') as f:
                self.operations = json.load(f)
        else:
            self.operations = []
    
    def _save_operations(self):
        """Save operations history to JSON file."""
        with open(self.operations_log, 'w') as f:
            json.dump(self.operations, f, indent=2)
    
    def delete_file(self, file_path: str, reason: str = "") -> Dict:
        """
        Safely delete a file by moving it to backup directory.
        Returns operation info for potential undo.
        """
        source = Path(file_path)
        
        if not source.exists():
            return {
                "success": False,
                "error": "File does not exist"
            }
        
        # Create timestamped backup folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / timestamp
        backup_folder.mkdir(parents=True, exist_ok=True)
        
        # Preserve directory structure in backup
        relative_path = source.name
        destination = backup_folder / relative_path
        
        try:
            # Move file to backup
            shutil.move(str(source), str(destination))
            
            # Log the operation
            operation = {
                "id": len(self.operations),
                "timestamp": timestamp,
                "action": "delete",
                "original_path": str(source),
                "backup_path": str(destination),
                "reason": reason,
                "can_undo": True
            }
            
            self.operations.append(operation)
            self._save_operations()
            
            return {
                "success": True,
                "operation_id": operation["id"],
                "backup_path": str(destination)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_multiple(self, file_paths: List[str], reason: str = "") -> Dict:
        """Delete multiple files in a batch operation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_id = len(self.operations)
        results = []
        
        for file_path in file_paths:
            result = self.delete_file(file_path, reason)
            results.append({
                "file": file_path,
                **result
            })
        
        return {
            "batch_id": batch_id,
            "timestamp": timestamp,
            "total": len(file_paths),
            "results": results
        }
    
    def undo_operation(self, operation_id: int) -> Dict:
        """Undo a delete operation by restoring from backup."""
        if operation_id >= len(self.operations):
            return {
                "success": False,
                "error": "Operation not found"
            }
        
        operation = self.operations[operation_id]
        
        if not operation.get("can_undo", False):
            return {
                "success": False,
                "error": "Operation cannot be undone"
            }
        
        backup_path = Path(operation["backup_path"])
        original_path = Path(operation["original_path"])
        
        if not backup_path.exists():
            return {
                "success": False,
                "error": "Backup file not found"
            }
        
        try:
            # Ensure parent directory exists
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file back
            shutil.move(str(backup_path), str(original_path))
            
            # Update operation log
            operation["can_undo"] = False
            operation["undone_at"] = datetime.now().isoformat()
            self._save_operations()
            
            return {
                "success": True,
                "restored_path": str(original_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recent_operations(self, limit: int = 50) -> List[Dict]:
        """Get recent operations for display."""
        return self.operations[-limit:][::-1]  # Most recent first
    
    def clean_old_backups(self, days: int = 30) -> Dict:
        """Remove backups older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        removed = []
        
        for folder in self.backup_dir.iterdir():
            if folder.is_dir() and folder.name.replace("_", "").isdigit():
                try:
                    timestamp = datetime.strptime(folder.name, "%Y%m%d_%H%M%S").timestamp()
                    if timestamp < cutoff:
                        shutil.rmtree(folder)
                        removed.append(folder.name)
                except ValueError:
                    continue
        
        return {
            "success": True,
            "removed_count": len(removed),
            "removed": removed
        }
    
    def get_backup_size(self) -> Dict:
        """Get total size of backup directory."""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.backup_dir):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count
        }
    
    def permanently_delete_backup(self, operation_id: int) -> Dict:
        """Permanently delete a backup file (cannot be undone)."""
        if operation_id >= len(self.operations):
            return {
                "success": False,
                "error": "Operation not found"
            }
        
        operation = self.operations[operation_id]
        backup_path = Path(operation["backup_path"])
        
        if not backup_path.exists():
            return {
                "success": False,
                "error": "Backup file not found"
            }
        
        try:
            backup_path.unlink()
            operation["can_undo"] = False
            operation["permanently_deleted"] = True
            self._save_operations()
            
            return {
                "success": True,
                "message": "Backup permanently deleted"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
