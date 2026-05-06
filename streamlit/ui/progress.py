import streamlit as st
from datetime import datetime
import pandas as pd
import altair as alt
from core.gamification import GamificationManager
from core.models import UserProgress, Achievement

def show_progress_page():
    """
    Display the gamification progress dashboard.
    """
    st.header("🏆 Your Progress")
    
    # Initialize manager
    gm = GamificationManager()
    progress = gm._load_progress()
    
    # --- Top Stats Row ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Level", f"{progress.current_level}", f"{progress.total_points} XP")
    
    with col2:
        st.metric("Total XP", f"{progress.total_points}")
        
    with col3:
        st.metric("Current Streak", f"{progress.current_streak} days")
        
    with col4:
        st.metric("Longest Streak", f"{progress.longest_streak} days")
        
    # --- XP Progress Bar ---
    # xp_for_next is stored in progress.points_to_next_level
    xp_target = progress.points_to_next_level
    current_xp = progress.total_points
    # We want progress WITHIN the level.
    # But total_points is cumulative.
    # For now, let's just show Total / Target
    
    progress_val = min(1.0, current_xp / max(1, xp_target))
    st.progress(progress_val)
    st.caption(f"XP to next level: {xp_target - current_xp}")

    # --- Activity Heatmap (Mock/Real) ---
    st.subheader("Studying Activity")
    
    if progress.weekly_points:
        # Convert history dict to DataFrame
        history_data = [
            {"date": date, "xp": xp} 
            for date, xp in progress.weekly_points.items()
        ]
        df = pd.DataFrame(history_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Plot using Altair or St chart
        st.bar_chart(df.set_index('date')['xp'])
    else:
        st.info("No study activity recorded yet. Complete tasks or study topics to earn XP!")

    # --- Achievements Gallery ---
    st.subheader("🏅 Achievements")
    
    if not progress.achievements:
        st.info("No achievements unlocked yet.")
    
    # Define cols for grid
    cols = st.columns(3)
    for i, achievement in enumerate(progress.achievements):
        with cols[i % 3]:
            with st.container(border=True):
                st.write(f"**{achievement.name}**")
                st.caption(achievement.description)
                st.write(f"📅 {achievement.earned_at.strftime('%Y-%m-%d')}")
                # st.write(f"xp +{achievement.xp_reward}") # Field missing

    # --- Recent Activity Log ---
    # If the model had a log, we'd show it here.
