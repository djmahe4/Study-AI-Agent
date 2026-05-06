import streamlit as st
import time
from datetime import datetime, timedelta
from core.pomodoro import PomodoroTimer

def show_pomodoro_page():
    st.header("🍅 Pomodoro Timer")
    
    # Initialize timer
    if 'pomodoro' not in st.session_state:
        st.session_state.pomodoro = PomodoroTimer()
    
    timer = st.session_state.pomodoro
    
    # Layout props
    col_timer, col_stats = st.columns([1, 1])
    
    with col_timer:
        st.subheader("Focus Timer")
        
        # Determine current subject context
        current_subject = "General"
        try: 
            with open("data/.current_subject", "r") as f:
                current_subject = f.read().strip()
        except: pass
        
        # Timer Display
        status = "Ready"
        remaining = 25 * 60
        
        if timer.current_session and timer.current_session.end_time:
            # Check if active
            remaining = (timer.current_session.end_time - datetime.now()).total_seconds()
            if remaining > 0:
                status = "Focusing..."
            else:
                status = "Finished!"
                remaining = 0
                # Auto-complete logic could go here or require user button
        
        # Display large timer
        mins, secs = divmod(int(remaining), 60)
        st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        st.info(f"Status: **{status}** | Subject: **{current_subject}**")
        
        # Controls
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Start 25m Focus", disabled=(remaining > 0), type="primary"):
                timer.start_session(duration_minutes=25, subject=current_subject)
                st.rerun()
                
        with c2:
            if st.button("Stop / Reset"):
                timer.current_session = None # Force reset
                st.rerun()
                
        with c3:
            if st.button("Complete & Log"):
                if timer.current_session:
                    timer.complete_session(notes="Completed via Streamlit")
                    st.success("Session logged! +XP earned")
                    time.sleep(1)
                    st.rerun()

        # Auto-refresh if running
        if remaining > 0:
            time.sleep(1)
            st.rerun()

    with col_stats:
        st.subheader("Session History")
        stats = timer.get_stats()
        
        st.write(f"**Today:** {stats['daily_count']} sessions ({stats['daily_minutes']} mins)")
        st.write(f"**Total:** {stats['total_count']} sessions")
        
        # List recent
        sessions = timer._load_sessions()
        if sessions:
            df = []
            for s in sessions[-10:][::-1]:
                df.append({
                    "Date": s.start_time.strftime("%m-%d %H:%M"),
                    "Subject": s.subject,
                    "Duration": f"{s.duration_minutes}m"
                })
            st.table(df)
