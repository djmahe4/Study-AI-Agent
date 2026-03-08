import streamlit as st
from core.todo_manager import TodoManager
from datetime import datetime

def show_todo_page():
    st.header("✅ Task Manager")
    
    tm = TodoManager()
    
    # get context
    current_subject = None
    try: 
        with open("data/.current_subject", "r") as f:
            current_subject = f.read().strip()
    except: pass

    # Add Task Form
    with st.expander("Add New Task", expanded=False):
        with st.form("new_todo"):
            title = st.text_input("Task Title")
            desc = st.text_area("Description")
            priority = st.select_slider("Priority", options=["low", "medium", "high"], value="medium")
            due_date = st.date_input("Due Date", min_value=datetime.today())
            
            if st.form_submit_button("Add Task"):
                tm.add_todo(
                    title=title,
                    description=desc,
                    priority=priority,
                    subject=current_subject,
                    due_date=due_date
                )
                st.success("Task added!")
                st.rerun()
    
    # Filter Controls
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.radio("Status", ["Pending", "Completed"], horizontal=True)
    with col2:
        filter_subject = st.checkbox("Show only current subject", value=True)
        
    # Get Todos
    todos = tm.get_todos(
        status=filter_status.lower(),
        subject=current_subject if filter_subject else None
    )
    
    if not todos:
        st.info("No tasks found.")
        
    for todo in todos:
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.1, 0.7, 0.2])
            
            with c1:
                # Checkbox to complete
                is_done = todo.status == "done"
                if st.checkbox("", value=is_done, key=f"chk_{todo.id}"):
                    if not is_done:
                        tm.complete_todo(todo.id)
                        st.rerun()
                        
            with c2:
                st.markdown(f"**{todo.title}**")
                if todo.description:
                    st.caption(todo.description)
                st.caption(f"📅 Due: {todo.due_date.strftime('%Y-%m-%d') if todo.due_date else 'No date'} | 🏷️ {todo.subject or 'General'}")
                
            with c3:
                 st.badge(todo.priority)
                 if st.button("🗑️", key=f"del_{todo.id}"):
                     tm.delete_todo(todo.id)
                     st.rerun()
