"""
Pomodoro timer for focused study sessions.
Pure Python logic - no LLM calls needed.
"""
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
import json
import time
import os
from core.models import PomodoroSession


class PomodoroTimer:
    """
    Manages Pomodoro study sessions with breaks and tracking.
    """
    
    def __init__(self, data_path: str = "data/pomodoro_sessions.json"):
        self.data_path = Path(data_path)
        self.current_session: Optional[PomodoroSession] = None
        self.sessions: List[PomodoroSession] = self._load_sessions()
        
    def _load_sessions(self) -> List[PomodoroSession]:
        """Load past sessions from file."""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    return [PomodoroSession(**s) for s in data]
            except:
                return []
        return []
    
    def save_sessions(self):
        """Save all sessions to file."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w') as f:
            json.dump([s.model_dump() for s in self.sessions], f, indent=2, default=str)
    
    def start_session(self, subject: Optional[str] = None, topic: Optional[str] = None,
                     duration: int = 25, break_duration: int = 5) -> PomodoroSession:
        """Start a new Pomodoro session."""
        self.current_session = PomodoroSession(
            subject=subject,
            topic=topic,
            duration_minutes=duration,
            break_duration=break_duration
        )
        return self.current_session
    
    def complete_session(self, notes: Optional[str] = None) -> PomodoroSession:
        """Mark current session as completed."""
        if not self.current_session:
            raise ValueError("No active session")
            
        self.current_session.end_time = datetime.now()
        self.current_session.completed = True
        self.current_session.cycles_completed = 1
        self.current_session.notes = notes
        self.current_session.points_earned = 2  # 2 points per completed Pomodoro
        
        self.sessions.append(self.current_session)
        completed = self.current_session
        self.current_session = None
        
        self.save_sessions()
        return completed
    
    def cancel_session(self):
        """Cancel current session without saving."""
        self.current_session = None
    
    def run_interactive_session(self, subject: Optional[str] = None, 
                               topic: Optional[str] = None,
                               duration: int = 25) -> PomodoroSession:
        """
        Run a complete interactive Pomodoro session with timer display.
        """
        session = self.start_session(subject, topic, duration)
        
        print(f"\n🍅 Pomodoro Session Started!")
        if subject:
            print(f"   Subject: {subject}")
        if topic:
            print(f"   Topic: {topic}")
        print(f"   Duration: {duration} minutes")
        print(f"\n   Press Ctrl+C to pause/stop\n")
        
        try:
            # Countdown timer
            total_seconds = duration * 60
            for remaining in range(total_seconds, 0, -1):
                mins, secs = divmod(remaining, 60)
                timer = f"\r   ⏰ Time Remaining: {mins:02d}:{secs:02d}"
                print(timer, end='', flush=True)
                time.sleep(1)
            
            print("\n\n   ✅ Pomodoro Complete!")
            
            # Show ASCII tomato
            print(self._get_tomato_art())
            
            # Complete session
            completed = self.complete_session()
            
            # Break time
            print(f"\n   🎉 Great job! You earned {completed.points_earned} points!")
            print(f"\n   💭 {self._get_break_message()}")
            print(f"\n   Take a {session.break_duration}-minute break!\n")
            
            return completed
            
        except KeyboardInterrupt:
            print("\n\n   ⏸️  Session paused.")
            print("   Resume with 'pomodoro resume' or cancel with 'pomodoro cancel'")
            return session
    
    def _get_tomato_art(self) -> str:
        """Get ASCII art tomato."""
        return """
        🍅
       /   \\
      |  •  |
       \\___/
    """
    
    def _get_break_message(self) -> str:
        """Get motivational message for break time."""
        messages = [
            "Stand up and stretch!",
            "Grab some water and relax.",
            "You're doing amazing!",
            "Take a deep breath.",
            "Look away from the screen.",
            "Quick walk recommended!",
            "Rest your eyes for a bit.",
            "Check your posture!"
        ]
        import random
        return random.choice(messages)
    
    def get_session_history(self, limit: int = 10) -> List[PomodoroSession]:
        """Get recent session history."""
        return self.sessions[-limit:]
    
    def get_daily_stats(self, target_date: Optional[datetime] = None) -> dict:
        """Get statistics for a specific day."""
        if not target_date:
            target_date = datetime.now()
            
        day_sessions = [
            s for s in self.sessions
            if s.completed and s.start_time.date() == target_date.date()
        ]
        
        total_study_time = sum(s.duration_minutes for s in day_sessions)
        
        return {
            "date": target_date.date(),
            "sessions_completed": len(day_sessions),
            "total_minutes": total_study_time,
            "subjects": list(set(s.subject for s in day_sessions if s.subject))
        }
    
    def get_weekly_stats(self) -> dict:
        """Get statistics for current week."""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        week_sessions = [
            s for s in self.sessions
            if s.completed and s.start_time >= week_start
        ]
        
        # Group by day
        days = {}
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_key = day.strftime("%A")
            day_sessions = [s for s in week_sessions if s.start_time.date() == day.date()]
            days[day_key] = len(day_sessions)
        
        return {
            "week_start": week_start.date(),
            "total_sessions": len(week_sessions),
            "total_minutes": sum(s.duration_minutes for s in week_sessions),
            "days_breakdown": days,
            "tomatoes": "🍅" * min(len(week_sessions), 20)  # Visual representation
        }
    
    def get_stats_display(self) -> str:
        """Generate ASCII art stats display."""
        weekly = self.get_weekly_stats()
        daily = self.get_daily_stats()
        
        display = f"""
╔════════════════════════════════════════════════════╗
║          🍅 POMODORO STATISTICS                    ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  📅 TODAY ({datetime.now().strftime('%b %d, %Y')})                      ║
║  Sessions: {daily['sessions_completed']:<39} ║
║  Study Time: {daily['total_minutes']} mins                              ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║  📊 THIS WEEK                                      ║
╠════════════════════════════════════════════════════╣
║  Total Sessions: {weekly['total_sessions']:<33} ║
║  Total Time: {weekly['total_minutes']} mins                            ║
║                                                    ║
║  {weekly['tomatoes']:<49} ║
║                                                    ║
"""
        
        # Show daily breakdown
        for day, count in weekly['days_breakdown'].items():
            tomatoes = "🍅" * count if count > 0 else "—"
            display += f"║  {day[:3]}: {tomatoes:<44} ║\n"
        
        display += "╚════════════════════════════════════════════════════╝"
        
        return display
