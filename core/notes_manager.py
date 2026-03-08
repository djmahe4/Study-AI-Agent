"""
Custom notes manager for personal annotations and highlights.
Pure Python - no LLM needed.
"""
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime
from core.models import CustomNote


class NotesManager:
    """
    Manages user's custom notes and annotations.
    """
    
    def __init__(self, data_path: str = "data/custom_notes"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.notes: List[CustomNote] = self._load_notes()
    
    def _load_notes(self) -> List[CustomNote]:
        """Load all custom notes."""
        notes = []
        if self.data_path.exists():
            for note_file in self.data_path.glob("*.json"):
                try:
                    with open(note_file, 'r') as f:
                        data = json.load(f)
                    notes.append(CustomNote(**data))
                except Exception as e:
                    print(f"Error loading note {note_file}: {e}")
        return notes
    
    def save_note(self, note: CustomNote):
        """Save a single note using safe persistence."""
        from .persistence import get_persistence_manager
        
        pm = get_persistence_manager()
        file_path = self.data_path / f"{note.id}.json"
        
        temp_path = file_path.with_suffix('.tmp.json')
        try:
            with open(temp_path, 'w') as f:
                json.dump(note.model_dump(), f, indent=2, default=str)
            
            if file_path.exists():
                pm._create_backup(file_path)
                file_path.unlink()
            temp_path.rename(file_path)
        except Exception as e:
            print(f"Warning: Failed to save note: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    def create_note(self, title: str, content: str, subject: str,
                   module: Optional[str] = None, topic: Optional[str] = None,
                   tags: List[str] = None, is_highlight: bool = False) -> CustomNote:
        """Create a new custom note."""
        note = CustomNote(
            title=title,
            content=content,
            subject=subject,
            module=module,
            topic=topic,
            tags=tags or [],
            is_highlight=is_highlight
        )
        self.notes.append(note)
        self.save_note(note)
        return note
    
    def get_note(self, note_id: str) -> Optional[CustomNote]:
        """Get a specific note by ID."""
        return next((n for n in self.notes if n.id == note_id), None)
    
    def update_note(self, note_id: str, title: Optional[str] = None,
                   content: Optional[str] = None, tags: Optional[List[str]] = None,
                   is_highlight: Optional[bool] = None) -> Optional[CustomNote]:
        """Update an existing note."""
        note = self.get_note(note_id)
        if not note:
            return None
        
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if tags is not None:
            note.tags = tags
        if is_highlight is not None:
            note.is_highlight = is_highlight
        
        note.last_modified = datetime.now()
        self.save_note(note)
        return note
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        note = self.get_note(note_id)
        if note:
            self.notes.remove(note)
            file_path = self.data_path / f"{note_id}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        return False
    
    def get_notes_by_subject(self, subject: str) -> List[CustomNote]:
        """Get all notes for a subject."""
        return [n for n in self.notes if n.subject and subject.lower() in n.subject.lower()]
    
    def get_notes_by_topic(self, topic: str) -> List[CustomNote]:
        """Get all notes for a topic."""
        return [n for n in self.notes if n.topic and topic.lower() in n.topic.lower()]
    
    def get_highlights(self) -> List[CustomNote]:
        """Get all highlighted notes."""
        return [n for n in self.notes if n.is_highlight]
    
    def search_notes(self, query: str) -> List[CustomNote]:
        """Search notes by title, content, or tags."""
        query_lower = query.lower()
        results = []
        for note in self.notes:
            if (query_lower in note.title.lower() or
                query_lower in note.content.lower() or
                any(query_lower in tag.lower() for tag in note.tags)):
                results.append(note)
        return results
    
    def export_to_markdown(self, output_file: str, subject: Optional[str] = None):
        """Export notes to a single markdown file."""
        notes_to_export = self.get_notes_by_subject(subject) if subject else self.notes
        
        md = f"# Custom Notes\n\n"
        if subject:
            md += f"**Subject:** {subject}\n\n"
        md += f"**Total Notes:** {len(notes_to_export)}\n\n"
        md += "---\n\n"
        
        # Group by subject/module
        by_subject = {}
        for note in notes_to_export:
            key = note.subject
            if key not in by_subject:
                by_subject[key] = []
            by_subject[key].append(note)
        
        for subj, notes_list in by_subject.items():
            md += f"## {subj}\n\n"
            
            # Group by module
            by_module = {}
            for note in notes_list:
                mod_key = note.module or "General"
                if mod_key not in by_module:
                    by_module[mod_key] = []
                by_module[mod_key].append(note)
            
            for module, mod_notes in by_module.items():
                md += f"### {module}\n\n"
                
                for note in mod_notes:
                    highlight = "⭐ " if note.is_highlight else ""
                    md += f"#### {highlight}{note.title}\n\n"
                    
                    if note.topic:
                        md += f"**Topic:** {note.topic}\n\n"
                    
                    if note.tags:
                        md += f"**Tags:** {', '.join(note.tags)}\n\n"
                    
                    md += f"{note.content}\n\n"
                    
                    md += f"*Created: {note.created_at.strftime('%Y-%m-%d')}*\n\n"
                    md += "---\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)
    
    def get_recent_notes(self, limit: int = 10) -> List[CustomNote]:
        """Get most recently modified notes."""
        sorted_notes = sorted(self.notes, key=lambda n: n.last_modified, reverse=True)
        return sorted_notes[:limit]
