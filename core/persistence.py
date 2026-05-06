"""
Safe data persistence layer with backup, validation, and atomic operations.
Prevents data corruption by validating before write and maintaining backups.
"""
import json
import shutil
from pathlib import Path
from typing import Any, Optional, Type
from datetime import datetime
from pydantic import BaseModel, ValidationError


class DataPersistenceManager:
    """
    Manages safe read/write operations with automatic backup and validation.
    
    Features:
    - Automatic backup before write
    - Pydantic validation before write
    - Atomic file operations (write to temp, then move)
    - Rollback capability
    """
    
    def __init__(self, backup_dir: str = "data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create timestamped backup of existing file."""
        if not file_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / file_path.parent.name / backup_name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def save_model(
        self, 
        model: BaseModel, 
        file_path: str | Path,
        create_backup: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Safely save a Pydantic model to JSON with validation and backup.
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)
        backup_path = None
        
        try:
            # Step 1: Validate model (this will raise if invalid)
            model.model_validate(model.model_dump())
            
            # Step 2: Create backup of existing file
            if create_backup and file_path.exists():
                backup_path = self._create_backup(file_path)
            
            # Step 3: Write to temporary file first (atomic operation)
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(model.model_dump(), f, indent=2, default=str)
            
            # Step 4: Validate the written file by reading it back
            with open(temp_path, 'r', encoding='utf-8') as f:
                written_data = json.load(f)
                type(model).model_validate(written_data)  # Ensure it deserializes correctly
            
            # Step 5: Move temp file to actual location (atomic on most systems)
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
            
            return True, None
            
        except ValidationError as e:
            error_msg = f"Validation failed: {str(e)}"
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Save failed: {str(e)}"
            # Rollback: restore backup if available
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, file_path)
            return False, error_msg
    
    def load_model(
        self, 
        file_path: str | Path, 
        model_class: Type[BaseModel],
        auto_fix: bool = True
    ) -> tuple[Optional[BaseModel], Optional[str]]:
        """
        Safely load a Pydantic model from JSON with optional auto-fix.
        
        Args:
            file_path: Path to JSON file
            model_class: Pydantic model class to deserialize into
            auto_fix: If True, attempts to auto-generate missing required fields
        
        Returns:
            (model: Optional[BaseModel], error_message: Optional[str])
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None, f"File not found: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Try direct validation first
            try:
                model = model_class.model_validate(data)
                return model, None
            except ValidationError as e:
                if not auto_fix:
                    return None, f"Validation failed: {str(e)}"
                
                # Auto-fix: Apply fixes based on model type
                from core.models import Syllabus, Module, Topic
                import uuid
                
                if model_class == Syllabus:
                    # Fix missing IDs in top-level topics (backward compatibility)
                    if 'topics' in data:
                        for topic in data['topics']:
                            if not topic.get('id'):
                                topic['id'] = str(uuid.uuid4())
                    
                    # Fix missing module IDs
                    if 'modules' in data:
                        for module in data['modules']:
                            if not module.get('id'):
                                module['id'] = str(uuid.uuid4())
                            
                            # Fix missing topic IDs within modules
                            if 'topics' in module:
                                for topic in module['topics']:
                                    if not topic.get('id'):
                                        topic['id'] = str(uuid.uuid4())
                
                # Retry validation after fixes
                model = model_class.model_validate(data)
                
                # Save the fixed version
                self.save_model(model, file_path, create_backup=True)
                
                return model, None
                
        except Exception as e:
            return None, f"Load failed: {str(e)}"
    
    def list_backups(self, original_file: str | Path) -> list[Path]:
        """List all backups for a given file, sorted by timestamp (newest first)."""
        original_file = Path(original_file)
        backup_subdir = self.backup_dir / original_file.parent.name
        
        if not backup_subdir.exists():
            return []
        
        pattern = f"{original_file.stem}_*{original_file.suffix}"
        backups = sorted(
            backup_subdir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return backups
    
    def restore_backup(
        self, 
        target_file: str | Path, 
        backup_index: int = 0
    ) -> tuple[bool, Optional[str]]:
        """
        Restore a backup to the original location.
        
        Args:
            target_file: Original file path to restore to
            backup_index: Index of backup to restore (0 = most recent)
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        target_file = Path(target_file)
        backups = self.list_backups(target_file)
        
        if not backups:
            return False, "No backups found"
        
        if backup_index >= len(backups):
            return False, f"Backup index {backup_index} out of range (only {len(backups)} backups)"
        
        try:
            backup_path = backups[backup_index]
            
            # Create a backup of current file before restoring
            if target_file.exists():
                self._create_backup(target_file)
            
            shutil.copy2(backup_path, target_file)
            return True, None
            
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    def safe_markdown_append(
        self,
        file_path: str | Path,
        content: str,
        create_backup: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Safely append content to a markdown file with backup.
        
        Args:
            file_path: Path to markdown file
            content: Content to append
            create_backup: Whether to create backup before append
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)
        
        try:
            # Create backup if file exists
            backup_path = None
            if create_backup and file_path.exists():
                backup_path = self._create_backup(file_path)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing content
            existing_content = ""
            if file_path.exists():
                existing_content = file_path.read_text(encoding='utf-8')
            
            # Write to temp file
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
            new_content = existing_content + content
            temp_path.write_text(new_content, encoding='utf-8')
            
            # Verify temp file is readable
            temp_path.read_text(encoding='utf-8')
            
            # Move temp to actual location
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
            
            return True, None
            
        except Exception as e:
            error_msg = f"Markdown append failed: {str(e)}"
            # Rollback if backup exists
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, file_path)
            return False, error_msg
    
    def safe_markdown_write(
        self,
        file_path: str | Path,
        content: str,
        create_backup: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Safely write content to a markdown file (overwrite) with backup.
        
        Args:
            file_path: Path to markdown file
            content: Content to write
            create_backup: Whether to create backup before write
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)
        
        try:
            # Create backup if file exists
            backup_path = None
            if create_backup and file_path.exists():
                backup_path = self._create_backup(file_path)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
            temp_path.write_text(content, encoding='utf-8')
            
            # Verify temp file is readable
            temp_path.read_text(encoding='utf-8')
            
            # Move temp to actual location
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
            
            return True, None
            
        except Exception as e:
            error_msg = f"Markdown write failed: {str(e)}"
            # Rollback if backup exists
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, file_path)
            return False, error_msg



# Global instance
_persistence_manager = None

def get_persistence_manager() -> DataPersistenceManager:
    """Get or create global persistence manager instance."""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = DataPersistenceManager()
    return _persistence_manager
