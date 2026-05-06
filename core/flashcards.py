"""
Flashcard system with spaced repetition (SM-2 algorithm).
Pure Python logic - no LLM calls needed for basic operations.
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import json
import random
from core.models import Flashcard, FlashcardDeck


class FlashcardManager:
    """
    Manages flashcard decks and spaced repetition learning.
    """
    
    def __init__(self, data_path: str = "data/flashcards"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.decks: List[FlashcardDeck] = self._load_decks()
    
    def _load_decks(self) -> List[FlashcardDeck]:
        """Load all flashcard decks from files."""
        decks = []
        if self.data_path.exists():
            for deck_file in self.data_path.glob("*.json"):
                try:
                    with open(deck_file, 'r') as f:
                        data = json.load(f)
                    decks.append(FlashcardDeck(**data))
                except Exception as e:
                    print(f"Error loading deck {deck_file}: {e}")
        return decks
    
    def save_deck(self, deck: FlashcardDeck):
        """Save a single deck to file using safe persistence."""
        from .persistence import get_persistence_manager
        
        pm = get_persistence_manager()
        file_path = self.data_path / f"{deck.id}.json"
        
        temp_path = file_path.with_suffix('.tmp.json')
        try:
            with open(temp_path, 'w') as f:
                json.dump(deck.model_dump(), f, indent=2, default=str)
            
            if file_path.exists():
                pm._create_backup(file_path)
                file_path.unlink()
            temp_path.rename(file_path)
        except Exception as e:
            print(f"Warning: Failed to save deck: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    def create_deck(self, name: str, subject: Optional[str] = None, 
                   module: Optional[str] = None, description: Optional[str] = None) -> FlashcardDeck:
        """Create a new flashcard deck."""
        deck = FlashcardDeck(
            name=name,
            description=description,
            subject=subject,
            module=module
        )
        self.decks.append(deck)
        self.save_deck(deck)
        return deck
    
    def list_decks(self) -> List[FlashcardDeck]:
        """List all available decks."""
        return self.decks

    def get_cards_for_review(self, deck_id: str, limit: int = 50) -> List[Flashcard]:
        """Get cards due for review plus some new cards."""
        try:
            session_data = self.start_study_session(deck_id, max_review=limit)
            return session_data["queue"]
        except ValueError:
            return []

    def get_deck(self, deck_id: str) -> Optional[FlashcardDeck]:
        """Get a specific deck by ID."""
        return next((d for d in self.decks if d.id == deck_id), None)
    
    def get_decks_by_subject(self, subject: str) -> List[FlashcardDeck]:
        """Get all decks for a subject."""
        return [d for d in self.decks if d.subject and subject.lower() in d.subject.lower()]
    
    def add_card_to_deck(self, deck_id: str, front: str, back: str, 
                        hints: List[str] = None, tags: List[str] = None,
                        diagram: Optional[str] = None) -> Flashcard:
        """Add a new flashcard to a deck."""
        deck = self.get_deck(deck_id)
        if not deck:
            raise ValueError(f"Deck {deck_id} not found")
        
        card = Flashcard(
            front=front,
            back=back,
            hints=hints or [],
            tags=tags or [],
            subject=deck.subject,
            module=deck.module,
            diagram_mermaid=diagram
        )
        
        deck.cards.append(card)
        self.save_deck(deck)
        return card
    
    def delete_deck(self, deck_id: str) -> bool:
        """Delete a deck."""
        deck = self.get_deck(deck_id)
        if deck:
            self.decks.remove(deck)
            file_path = self.data_path / f"{deck_id}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        return False
    
    def start_study_session(self, deck_id: str, max_new: int = 20, max_review: int = 100) -> dict:
        """
        Start a study session with a deck.
        Returns study queue with new and due cards.
        """
        deck = self.get_deck(deck_id)
        if not deck:
            raise ValueError(f"Deck {deck_id} not found")
        
        # Get cards
        new_cards = deck.get_new_cards()[:max_new]
        due_cards = deck.get_due_cards()[:max_review]
        
        # Shuffle and combine
        random.shuffle(new_cards)
        random.shuffle(due_cards)
        
        # Interleave: review cards first, then new
        study_queue = due_cards + new_cards
        
        deck.last_studied = datetime.now()
        self.save_deck(deck)
        
        return {
            "deck_id": deck_id,
            "deck_name": deck.name,
            "queue": study_queue,
            "total_cards": len(study_queue),
            "new_count": len(new_cards),
            "review_count": len(due_cards)
        }
    
    def review_card(self, deck_id: str, card_id: str, quality: int):
        """
        Record a card review with quality rating (0-5).
        Updates card using SM-2 algorithm.
        """
        deck = self.get_deck(deck_id)
        if not deck:
            raise ValueError(f"Deck {deck_id} not found")
        
        card = next((c for c in deck.cards if c.id == card_id), None)
        if not card:
            raise ValueError(f"Card {card_id} not found in deck")
        
        # Update using SM-2
        card.update_sm2(quality)
        
        self.save_deck(deck)
        
        return {
            "next_review": card.next_review_date,
            "interval": card.interval,
            "ease_factor": card.ease_factor
        }
    
    def get_daily_stats(self) -> dict:
        """Get statistics for all decks today."""
        total_due = 0
        total_new = 0
        total_cards = 0
        
        for deck in self.decks:
            total_cards += len(deck.cards)
            total_due += len(deck.get_due_cards())
            total_new += len(deck.get_new_cards())
        
        return {
            "total_decks": len(self.decks),
            "total_cards": total_cards,
            "due_today": total_due,
            "new_cards": total_new
        }
    
    def export_to_anki(self, deck_id: str, output_file: str):
        """
        Export deck to Anki-compatible CSV format.
        Format: front; back; tags
        """
        deck = self.get_deck(deck_id)
        if not deck:
            raise ValueError(f"Deck {deck_id} not found")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for card in deck.cards:
                tags = " ".join(card.tags)
                # Escape semicolons in content
                front = card.front.replace(';', '\\;')
                back = card.back.replace(';', '\\;')
                f.write(f"{front};{back};{tags}\n")
    
    def get_performance_summary(self, deck_id: str, days: int = 30) -> dict:
        """Get performance summary for a deck over the last N days."""
        deck = self.get_deck(deck_id)
        if not deck:
            raise ValueError(f"Deck {deck_id} not found")
        
        cutoff = datetime.now() - timedelta(days=days)
        recent_cards = [c for c in deck.cards 
                       if c.last_reviewed and c.last_reviewed >= cutoff]
        
        if not recent_cards:
            return {
                "days": days,
                "cards_reviewed": 0,
                "accuracy": 0,
                "average_ease": 0
            }
        
        total_reviews = sum(c.times_reviewed for c in recent_cards)
        correct_reviews = sum(c.times_correct for c in recent_cards)
        
        return {
            "days": days,
            "cards_reviewed": len(recent_cards),
            "total_reviews": total_reviews,
            "accuracy": (correct_reviews / max(1, total_reviews)) * 100,
            "average_ease": sum(c.ease_factor for c in recent_cards) / len(recent_cards),
            "mastered_cards": len([c for c in deck.cards if c.repetitions > 5])
        }
    
    def get_dashboard_display(self) -> str:
        """Generate ASCII art dashboard."""
        stats = self.get_daily_stats()
        
        display = f"""
╔════════════════════════════════════════════════════╗
║          📚 FLASHCARD DASHBOARD                    ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Total Decks: {stats['total_decks']:<37} ║
║  Total Cards: {stats['total_cards']:<37} ║
║                                                    ║
║  📅 DUE TODAY: {stats['due_today']:<35} ║
║  ✨ NEW CARDS: {stats['new_cards']:<35} ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║  🎴 YOUR DECKS                                     ║
╠════════════════════════════════════════════════════╣
"""
        
        if not self.decks:
            display += "║  No decks yet. Create one to get started!      ║\n"
        else:
            for deck in self.decks[:10]:  # Show max 10
                deck_stats = deck.get_stats()
                name_short = deck.name[:30] + "..." if len(deck.name) > 30 else deck.name
                due = deck_stats['due_today']
                new = deck_stats['new_cards']
                
                display += f"║                                                    ║\n"
                display += f"║  📦 {name_short:<44} ║\n"
                display += f"║     {deck_stats['total_cards']} cards • {due} due • {new} new                     ║\n"
                
                if deck.subject:
                    display += f"║     Subject: {deck.subject[:35]:<35} ║\n"
        
        display += "╚════════════════════════════════════════════════════╝"
        
        return display
