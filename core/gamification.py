"""
Gamification system for tracking user progress, levels, and achievements.
Pure Python logic - no LLM calls needed.
"""
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, date
import json
from core.models import UserProgress, Achievement, PomodoroSession, TodoItem


class GamificationManager:
    """
    Manages user progress, levels, achievements, and rewards.
    """
    
    def __init__(self, data_path: str = "data/user_progress.json"):
        self.data_path = Path(data_path)
        self.progress = self._load_progress()
        
    def _load_progress(self) -> UserProgress:
        """Load user progress from file or create new."""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    return UserProgress(**data)
            except:
                return UserProgress()
        return UserProgress()
    
    def save_progress(self):
        """Save current progress to file."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w') as f:
            json.dump(self.progress.model_dump(), f, indent=2, default=str)
    
    def add_points(self, points: int, reason: str = "") -> Dict:
        """
        Add points and return result with level up info.
        """
        old_level = self.progress.current_level
        leveled_up = self.progress.add_points(points)
        
        # Update activity date for streak tracking
        today = date.today()
        if self.progress.last_activity_date:
            if (today - self.progress.last_activity_date).days == 1:
                # Consecutive day
                self.progress.current_streak += 1
                if self.progress.current_streak > self.progress.longest_streak:
                    self.progress.longest_streak = self.progress.current_streak
                    
                # Check for streak achievements
                if self.progress.current_streak == 7:
                    self._award_achievement("consistency_week", "Consistency King/Queen", 
                                          "Maintained a 7-day study streak!", "🔥", "consistency")
                elif self.progress.current_streak == 30:
                    self._award_achievement("consistency_month", "Marathon Master", 
                                          "Studied for 30 consecutive days!", "🏆", "consistency")
            elif (today - self.progress.last_activity_date).days > 1:
                # Streak broken
                self.progress.current_streak = 1
        else:
            self.progress.current_streak = 1
            
        self.progress.last_activity_date = today
        self.save_progress()
        
        return {
            "points_added": points,
            "total_points": self.progress.total_points,
            "leveled_up": leveled_up,
            "old_level": old_level,
            "new_level": self.progress.current_level,
            "level_name": self.progress.get_level_name(),
            "streak": self.progress.current_streak,
            "reason": reason
        }
    
    def _award_achievement(self, achievement_id: str, name: str, description: str, 
                          icon: str, category: str):
        """Award an achievement if not already earned."""
        # Check if already has this achievement
        if any(a.id == achievement_id for a in self.progress.achievements):
            return False
            
        achievement = Achievement(
            id=achievement_id,
            name=name,
            description=description,
            icon=icon,
            category=category
        )
        self.progress.achievements.append(achievement)
        return True
    
    def check_and_award_achievements(self):
        """Check for new achievements based on current progress."""
        new_achievements = []
        
        # Pomodoro achievements
        if self.progress.total_pomodoros >= 10:
            if self._award_achievement("pomodoro_novice", "Focus Beginner", 
                                      "Completed 10 Pomodoro sessions", "🍅", "completion"):
                new_achievements.append("Focus Beginner")
                
        if self.progress.total_pomodoros >= 100:
            if self._award_achievement("pomodoro_master", "Focus Master", 
                                      "Completed 100 Pomodoro sessions", "🍅✨", "mastery"):
                new_achievements.append("Focus Master")
        
        # TODO achievements
        if self.progress.total_todos_completed >= 10:
            if self._award_achievement("tasks_beginner", "Task Crusher", 
                                      "Completed 10 tasks", "✅", "completion"):
                new_achievements.append("Task Crusher")
                
        if self.progress.total_todos_completed >= 50:
            if self._award_achievement("tasks_master", "Productivity Pro", 
                                      "Completed 50 tasks", "⚡", "mastery"):
                new_achievements.append("Productivity Pro")
        
        # Study hours
        if self.progress.total_study_hours >= 10:
            if self._award_achievement("hours_10", "Dedicated Learner", 
                                      "Logged 10 hours of study", "📚", "completion"):
                new_achievements.append("Dedicated Learner")
                
        if self.progress.total_study_hours >= 100:
            if self._award_achievement("hours_100", "Study Legend", 
                                      "Logged 100 hours of study", "🌟", "mastery"):
                new_achievements.append("Study Legend")
        
        if new_achievements:
            self.save_progress()
            
        return new_achievements
    
    def record_pomodoro(self, session: PomodoroSession):
        """Record a completed Pomodoro session."""
        self.progress.total_pomodoros += 1
        self.progress.total_study_hours += session.duration_minutes / 60.0
        
        # Award points (2 points per Pomodoro)
        points = 2
        self.add_points(points, f"Completed Pomodoro: {session.subject or 'General'}")
        
        # Check for daily Pomodoro achievements
        # TODO: Track daily Pomodoros if needed
        
        self.check_and_award_achievements()
        self.save_progress()
    
    def record_todo_completion(self, todo: TodoItem):
        """Record a completed TODO item."""
        self.progress.total_todos_completed += 1
        self.add_points(todo.points_earned, f"Completed task: {todo.title}")
        self.check_and_award_achievements()
        self.save_progress()
    
    def get_weekly_summary(self) -> Dict:
        """Get current week's statistics."""
        week_key = datetime.now().strftime("%Y_%W")
        return {
            "week": week_key,
            "points": self.progress.weekly_points.get(week_key, 0),
            "level": self.progress.current_level,
            "level_name": self.progress.get_level_name(),
            "streak": self.progress.current_streak,
            "total_hours": self.progress.total_study_hours,
            "total_pomodoros": self.progress.total_pomodoros
        }
    
    def get_leaderboard_display(self) -> str:
        """Generate ASCII art leaderboard display."""
        progress_bar_length = 30
        level_progress = self.progress.calculate_level_progress()
        filled = int((level_progress / 100) * progress_bar_length)
        bar = "█" * filled + "░" * (progress_bar_length - filled)
        
        # Streak fire emojis
        fire_count = min(self.progress.current_streak, 10)
        streak_display = "🔥" * fire_count
        
        display = f"""
╔════════════════════════════════════════════════════╗
║          🎓 LEARNING PROGRESS DASHBOARD           ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Level: {self.progress.current_level} - {self.progress.get_level_name():<30}  ║
║  Total Points: {self.progress.total_points:<35} ║
║                                                    ║
║  Progress to Level {self.progress.current_level + 1}:                            ║
║  [{bar}] {level_progress:.1f}%           ║
║  {self.progress.total_points}/{self.progress.total_points + self.progress.points_to_next_level} points                                    ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║  📊 STATISTICS                                     ║
╠════════════════════════════════════════════════════╣
║  Current Streak: {streak_display:<30}  ║
║  ({self.progress.current_streak} days)                                      ║
║  Longest Streak: {self.progress.longest_streak} days                           ║
║                                                    ║
║  🍅 Pomodoros: {self.progress.total_pomodoros:<32}  ║
║  ⏱️  Study Hours: {self.progress.total_study_hours:.1f}                           ║
║  ✅ Tasks Done: {self.progress.total_todos_completed:<31}  ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║  🏆 ACHIEVEMENTS ({len(self.progress.achievements)})                            ║
╠════════════════════════════════════════════════════╣
"""
        
        if self.progress.achievements:
            for achievement in self.progress.achievements[-5:]:  # Show last 5
                display += f"║  {achievement.icon} {achievement.name:<42} ║\n"
        else:
            display += "║  No achievements yet. Keep studying!           ║\n"
        
        display += "╚════════════════════════════════════════════════════╝"
        
        return display
    
    def get_motivational_quote(self) -> str:
        """Get a random motivational quote."""
        quotes = [
            "The expert in anything was once a beginner.",
            "Success is the sum of small efforts repeated day in and day out.",
            "Don't watch the clock; do what it does. Keep going.",
            "The secret of getting ahead is getting started.",
            "It's not about perfect. It's about effort.",
            "Focus on being productive instead of busy.",
            "Small progress is still progress.",
            "The only way to do great work is to love what you do.",
            "Believe you can and you're halfway there.",
            "You are capable of amazing things!"
        ]
        import random
        return random.choice(quotes)
