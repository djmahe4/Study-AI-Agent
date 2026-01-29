"""
TODO list manager with gamification (points, deadlines, difficulty).
Pure Python logic - no LLM calls needed.
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import json
from core.models import TodoItem


class TodoManager:
    """
    Manages TODO items with points,deadlines, and difficulty tracking.
    """
    
    def __init__(self, data_path: str = "data/todos.json"):
        self.data_path = Path(data_path)
        self.todos: List[TodoItem] = self._load_todos()
        
    def _load_todos(self) -> List[TodoItem]:
        """Load TODO items from file."""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    return [TodoItem(**item) for item in data]
            except:
                return []
        return []
    
    def save_todos(self):
        """Save all TODO items to file."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w') as f:
            json.dump([t.model_dump() for t in self.todos], f, indent=2, default=str)
    
    def add_todo(self, title: str, description: Optional[str] = None,
                subject: Optional[str] = None, topic: Optional[str] = None,
                difficulty: str = "medium", estimated_hours: float = 1.0,
                deadline: Optional[datetime] = None, tags: List[str] = None) -> TodoItem:
        """Add a new TODO item."""
        todo = TodoItem(
            title=title,
            description=description,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            estimated_hours=estimated_hours,
            deadline=deadline,
            tags=tags or []
        )
        
        # Calculate base points
        todo.base_points = todo.calculate_base_points()
        
        self.todos.append(todo)
        self.save_todos()
        return todo
    
    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """Get a specific TODO by ID."""
        return next((t for t in self.todos if t.id == todo_id), None)
    
    def complete_todo(self, todo_id: str, notes: Optional[str] = None) -> TodoItem:
        """Mark a TODO as completed and calculate points earned."""
        todo = self.get_todo(todo_id)
        if not todo:
            raise ValueError(f"TODO with ID {todo_id} not found")
        
        if todo.completed:
            raise ValueError("TODO already completed")
        
        todo.completed = True
        todo.completed_at = datetime.now()
        
        # Calculate points earned with bonuses/penalties
        points = todo.base_points
        
        # Bonus for early completion
        if todo.deadline:
            days_early = (todo.deadline - datetime.now()).days
            if days_early > 0:
                bonus = int(points * 0.5)  # 50% bonus
                points += bonus
            elif days_early < 0:
                penalty = int(points * 0.25)  # 25% penalty for late
                points = max(1, points - penalty)  # At least 1 point
        
        todo.points_earned = points
        
        # Add notes if provided
        if notes:
            todo.description = (todo.description or "") + f"\n\nCompletion Notes: {notes}"
        
        self.save_todos()
        return todo
    
    def delete_todo(self, todo_id: str) -> bool:
        """Delete a TODO item."""
        todo = self.get_todo(todo_id)
        if todo:
            self.todos.remove(todo)
            self.save_todos()
            return True
        return False
    
    def get_pending_todos(self, subject: Optional[str] = None) -> List[TodoItem]:
        """Get all pending (uncompleted) TODOs, optionally filtered by subject."""
        pending = [t for t in self.todos if not t.completed]
        if subject:
            pending = [t for t in pending if t.subject and subject.lower() in t.subject.lower()]
        return sorted(pending, key=lambda t: (t.deadline or datetime.max, t.difficulty))
    
    def get_completed_todos(self, subject: Optional[str] = None) -> List[TodoItem]:
        """Get all completed TODOs, optionally filtered by subject."""
        completed = [t for t in self.todos if t.completed]
        if subject:
            completed = [c for c in completed if c.subject and subject.lower() in c.subject.lower()]
        return sorted(completed, key=lambda t: t.completed_at, reverse=True)
    
    def get_overdue_todos(self) -> List[TodoItem]:
        """Get all overdue TODOs."""
        now = datetime.now()
        return [t for t in self.todos 
                if not t.completed and t.deadline and t.deadline < now]
    
    def get_today_todos(self) -> List[TodoItem]:
        """Get TODOs due today."""
        today = datetime.now().date()
        return [t for t in self.todos 
                if not t.completed and t.deadline and t.deadline.date() == today]
    
    def get_upcoming_todos(self, days: int = 7) -> List[TodoItem]:
        """Get TODOs due in the next N days."""
        now = datetime.now()
        future = now + timedelta(days=days)
        return [t for t in self.todos 
                if not t.completed and t.deadline and now <= t.deadline <= future]
    
    def get_stats(self) -> dict:
        """Get TODO statistics."""
        total = len(self.todos)
        completed = len([t for t in self.todos if t.completed])
        pending = total - completed
        overdue = len(self.get_overdue_todos())
        
        total_points_earned = sum(t.points_earned for t in self.todos if t.completed)
        potential_points = sum(t.base_points for t in self.todos if not t.completed)
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "total_points_earned": total_points_earned,
            "potential_points": potential_points
        }
    
    def get_list_display(self, show_completed: bool = False, subject: Optional[str] = None) -> str:
        """Generate formatted TODO list display."""
        if show_completed:
            todos = self.get_completed_todos(subject)
            title = "COMPLETED TASKS"
            empty_msg = "No completed tasks yet."
        else:
            todos = self.get_pending_todos(subject)
            title = "PENDING TASKS"
            empty_msg = "No pending tasks. Add one with 'todo add'!"
        
        if subject:
            title += f" - {subject}"
        
        display = f"""
╔════════════════════════════════════════════════════╗
║  📝 {title:<45} ║
╠════════════════════════════════════════════════════╣
"""
        
        if not todos:
            display += f"║  {empty_msg:<49} ║\n"
        else:
            for i, todo in enumerate(todos[:20], 1):  # Show max 20
                # Format difficulty
                diff_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
                diff = diff_emoji[todo.difficulty]
                
                # Format deadline
                deadline_str = ""
                if todo.deadline:
                    days_until = (todo.deadline - datetime.now()).days
                    if days_until < 0:
                        deadline_str = f"⚠️ {abs(days_until)}d overdue"
                    elif days_until ==0:
                        deadline_str = "📅 Due today!"
                    else:
                        deadline_str = f"📅 {days_until}d left"
                
                # Truncate title if too long
                title_display = todo.title[:35] + "..." if len(todo.title) > 35 else todo.title
                
                pts = f"{todo.points_earned}pts" if todo.completed else f"{todo.base_points}pts"
                
                display += f"║                                                    ║\n"
                display += f"║  {i}. {diff} {title_display:<40} ║\n"
                
                if todo.subject:
                    display += f"║     Subject: {todo.subject:<37} ║\n"
                
                if deadline_str:
                    display += f"║     {deadline_str:<45} ║\n"
                
                display += f"║     {pts} • {todo.estimated_hours}h estimated                      ║\n"
        
        display += "╚════════════════════════════════════════════════════╝"
        
        return display
    
    def get_dashboard_display(self, subject: Optional[str] = None) -> str:
        """Generate comprehensive dashboard with stats."""
        stats = self.get_stats()
        overdue = self.get_overdue_todos()
        today = self.get_today_todos()
        upcoming = self.get_upcoming_todos(7)
        
        # Progress bar
        progress_bar_length = 30
        completion_rate = stats['completion_rate']
        filled = int((completion_rate / 100) * progress_bar_length)
        bar = "█" * filled + "░" * (progress_bar_length - filled)
        
        display = f"""
╔════════════════════════════════════════════════════╗
║          📋 TODO DASHBOARD                         ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  📊 STATISTICS                                     ║
║  Total Tasks: {stats['total']:<37} ║
║  ✅ Completed: {stats['completed']:<36} ║
║  ⏳ Pending: {stats['pending']:<38} ║
║  ⚠️  Overdue: {len(overdue):<38} ║
║                                                    ║
║  Completion Rate:                                  ║
║  [{bar}] {completion_rate:.1f}%        ║
║                                                    ║
║  Points Earned: {stats['total_points_earned']:<34} ║
║  Potential: {stats['potential_points']:<39} ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║  🎯 PRIORITIES                                     ║
╠════════════════════════════════════════════════════╣
"""
        
        if overdue:
            display += f"║  ⚠️  {len(overdue)} OVERDUE TASKS!                           ║\n"
            for todo in overdue[:3]:
                days = abs((todo.deadline - datetime.now()).days)
                title_short = todo.title[:30] + "..." if len(todo.title) > 30 else todo.title
                display += f"║     • {title_short} ({days}d)                      ║\n"
        
        if today:
            display += f"║  📅 {len(today)} DUE TODAY:                                 ║\n"
            for todo in today[:3]:
                title_short = todo.title[:35] + "..." if len(todo.title) > 35 else todo.title
                display += f"║     • {title_short}                        ║\n"
        
        if upcoming and not overdue and not today:
            display += f"║  📅 Upcoming (next 7 days): {len(upcoming)}                  ║\n"
            for todo in upcoming[:3]:
                days = (todo.deadline - datetime.now()).days
                title_short = todo.title[:30] + "..." if len(todo.title) > 30 else todo.title
                display += f"║     • {title_short} ({days}d)                     ║\n"
        
        if not overdue and not today and not upcoming:
            display += "║  All clear! No urgent tasks.                   ║\n"
        
        display += "╚════════════════════════════════════════════════════╝"
        
        return display
