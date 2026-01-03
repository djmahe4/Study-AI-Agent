"""
Streamlit app for the AI Learning Engine.
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import KnowledgeBase, Topic, Question, create_acronym_mnemonic, get_example_difference
from visual import MindMapGenerator
import json

def main():
    # Page configuration
    st.set_page_config(
        page_title="AI Learning Engine",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'kb' not in st.session_state:
        st.session_state.kb = KnowledgeBase()
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = False
    if 'current_question_idx' not in st.session_state:
        st.session_state.current_question_idx = 0

    st.title("🧠 AI Learning Engine")

    st.markdown("*Learn with mind maps, animations, and structured knowledge*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["📚 Topics", "🗺️ Mind Map", "❓ Quiz Mode", "📊 Differences", "🎬 Animations", "➕ Add Content", "⚙️ Settings"]
    )
    
    if page == "📚 Topics":
        show_topics_page()
    elif page == "🗺️ Mind Map":
        show_mindmap_page()
    elif page == "❓ Quiz Mode":
        show_quiz_page()
    elif page == "📊 Differences":
        show_differences_page()
    elif page == "🎬 Animations":
        show_animations_page()
    elif page == "➕ Add Content":
        show_add_content_page()
    elif page == "⚙️ Settings":
        show_settings_page()


def get_current_subject():
    try:
        if Path("data/.current_subject").exists():
            with open("data/.current_subject", "r") as f:
                return f.read().strip()
    except:
        pass
    return None

def get_mermaid_content(topic_name):
    """Finds the mermaid markdown file for a topic."""
    subject = get_current_subject()
    if not subject:
        return None
        
    safe_name = "".join([c for c in topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
    search_pattern = f"*{safe_name}_mermaid.md"
    
    subject_dir = Path(f"data/subjects/{subject}/notes")
    if not subject_dir.exists():
        return None
        
    found = list(subject_dir.rglob(search_pattern))
    if found:
        try:
            with open(found[0], "r", encoding="utf-8") as f:
                return f.read()
        except:
            return None
    return None

def get_animation_content(topic_name):
    """Finds the animation GIF/Video for a topic."""
    subject = get_current_subject()
    if not subject:
        return None
        
    safe_name = "".join([c for c in topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
    search_pattern = f"*{safe_name}_anim.gif" # Prefer GIF
    
    subject_dir = Path(f"data/subjects/{subject}/notes")
    if not subject_dir.exists():
        return None
        
    found = list(subject_dir.rglob(search_pattern))
    if found:
        return str(found[0])
        
    # Check for mp4
    search_pattern = f"*{safe_name}_anim.mp4"
    found = list(subject_dir.rglob(search_pattern))
    if found:
        return str(found[0])
        
    return None

def generate_topic_animation(topic_name, summary):
    """Generates an animation script using Gemini and renders it."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from core.models import AnimationScript
        from visual.animate import render_animation_from_script
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("GOOGLE_API_KEY not found in environment.")
            return None

        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        structured_llm = llm.with_structured_output(AnimationScript)
        
        with st.spinner(f"Planning animation for '{topic_name}'..."):
            prompt = f"""
            Create an educational animation script for the topic: "{topic_name}".
            Summary: {summary}
            
            The animation should visualize the concept clearly using simple shapes (circles, rectangles, arrows, text).
            Plan a sequence of frames that build up the concept step-by-step.
            Duration should be reasonable (e.g. 5-10 seconds total).
            """
            script = structured_llm.invoke(prompt)
        
        if not script:
            st.error("Failed to generate animation script.")
            return None
            
        # Determine output path
        subject = get_current_subject()
        safe_name = "".join([c for c in topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
        
        # We need to find the topic directory. Heuristic: look for existing note or mermaid file
        subject_dir = Path(f"data/subjects/{subject}/notes")
        # Try to find where the topic note is
        found_notes = list(subject_dir.rglob(f"*{safe_name}.md"))
        
        if found_notes:
            output_dir = found_notes[0].parent
        else:
            output_dir = subject_dir # Fallback
            
        output_path = output_dir / f"{safe_name}_anim.gif"
        
        with st.spinner("Rendering animation frames..."):
            render_animation_from_script(script, str(output_path))
            
        return str(output_path)

    except Exception as e:
        st.error(f"Animation generation failed: {e}")
        return None

def show_settings_page():
    st.header("⚙️ Schema & Data Management")
    
    subjects_path = Path("data/subjects/subjects.json")
    if not subjects_path.exists():
        st.error("No subjects found.")
        return
        
    with open(subjects_path, "r") as f:
        subjects_data = json.load(f)
        
    subject_names = [s["name"] for s in subjects_data]
    selected_subject_name = st.selectbox("Select Subject to Edit", subject_names)
    
    if selected_subject_name:
        subject_info = next(s for s in subjects_data if s["name"] == selected_subject_name)
        syllabus_path = Path(subject_info["syllabus_path"])
        
        if syllabus_path.exists():
            with open(syllabus_path, "r", encoding="utf-8") as f:
                try:
                    syllabus = json.load(f)
                except json.JSONDecodeError:
                    st.error("Failed to load syllabus JSON.")
                    return

            st.subheader(f"Edit Syllabus: {selected_subject_name}")
            
            # --- General Info ---
            with st.expander("Subject Details", expanded=True):
                new_title = st.text_input("Title", syllabus.get("title", ""))
                new_desc = st.text_area("Description", syllabus.get("description", ""))
                
                syllabus["title"] = new_title
                syllabus["description"] = new_desc

            # --- Modules ---
            st.markdown("### Modules")
            
            # Helper to delete module
            if "delete_module_idx" not in st.session_state:
                st.session_state.delete_module_idx = None

            modules = syllabus.get("modules", [])
            
            for i, module in enumerate(modules):
                with st.expander(f"Module {i+1}: {module.get('name', 'Untitled')}"):
                    # Module Edit Form
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_mod_name = st.text_input(f"Name (Mod {i+1})", module.get("name", ""), key=f"mod_name_{i}")
                        module["name"] = new_mod_name
                    with col2:
                        if st.button("🗑️ Delete Module", key=f"del_mod_{i}"):
                            st.session_state.delete_module_idx = i
                            st.rerun()

                    new_mod_desc = st.text_area(f"Description (Mod {i+1})", module.get("description", ""), key=f"mod_desc_{i}")
                    module["description"] = new_mod_desc
                    
                    # Topics in Module
                    st.markdown("#### Topics")
                    topics = module.get("topics", [])
                    
                    # Helper to delete topic
                    if f"delete_topic_{i}_idx" not in st.session_state:
                        st.session_state[f"delete_topic_{i}_idx"] = None

                    for j, topic in enumerate(topics):
                        with st.container():
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                new_topic_name = st.text_input(f"Topic {j+1}", topic.get("name", ""), key=f"t_name_{i}_{j}")
                                topic["name"] = new_topic_name
                            with c2:
                                if st.button("🗑️", key=f"del_t_{i}_{j}"):
                                    st.session_state[f"delete_topic_{i}_idx"] = j
                                    st.rerun()
                            
                            with st.expander("Topic Details"):
                                new_t_summary = st.text_area("Summary", topic.get("summary", ""), key=f"t_sum_{i}_{j}")
                                topic["summary"] = new_t_summary
                                
                                # Key Points (Comma separated for simplicity)
                                current_kps = ", ".join(topic.get("key_points", []))
                                new_kps = st.text_area("Key Points (comma separated)", current_kps, key=f"t_kp_{i}_{j}")
                                topic["key_points"] = [k.strip() for k in new_kps.split(",") if k.strip()]

                    # Handle Topic Deletion
                    if st.session_state[f"delete_topic_{i}_idx"] is not None:
                        del topics[st.session_state[f"delete_topic_{i}_idx"]]
                        st.session_state[f"delete_topic_{i}_idx"] = None
                        st.rerun()

                    # Add Topic
                    if st.button("➕ Add Topic", key=f"add_t_{i}"):
                        topics.append({
                            "name": "New Topic",
                            "summary": "",
                            "key_points": []
                        })
                        st.rerun()

            # Handle Module Deletion
            if st.session_state.delete_module_idx is not None:
                del modules[st.session_state.delete_module_idx]
                st.session_state.delete_module_idx = None
                st.rerun()

            # Add Module
            if st.button("➕ Add New Module"):
                modules.append({
                    "name": "New Module",
                    "description": "",
                    "topics": []
                })
                st.rerun()

            st.divider()
            
            # Save Changes
            if st.button("💾 Save Changes", type="primary"):
                try:
                    with open(syllabus_path, "w", encoding="utf-8") as f:
                        json.dump(syllabus, f, indent=2)
                    st.success("Syllabus updated successfully!")
                    # TODO: Trigger re-generation of markdown notes if needed? 
                    # For now just saving JSON source of truth.
                except Exception as e:
                    st.error(f"Error saving file: {e}")

def get_pyq_content(topic_name, module_id=None):
    """Finds the PYQ Solutions markdown for the module containing this topic."""
    subject = get_current_subject()
    if not subject:
        return None
    
    # Heuristic: We need to find the module folder.
    # Since we don't have direct module link in flat topic list easily without loading syllabus again,
    # let's try to find the topic file and look in its parent folder for PYQ_Solutions.md
    
    safe_name = "".join([c for c in topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
    search_pattern = f"*{safe_name}.md"
    
    subject_dir = Path(f"data/subjects/{subject}/notes")
    if not subject_dir.exists():
        return None
        
    found_notes = list(subject_dir.rglob(search_pattern))
    if found_notes:
        # Check if PYQ_Solutions.md exists in the same directory (Module directory)
        module_dir = found_notes[0].parent
        pyq_file = module_dir / "PYQ_Solutions.md"
        if pyq_file.exists():
            try:
                with open(pyq_file, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return None
    return None

def show_topics_page():
    st.header("📚 Learning Topics")
    
    topics = st.session_state.kb.get_topics()
    
    if not topics:
        st.warning("No topics found. Add some topics to get started!")
        return
    
    # Display topics as cards
    for topic in topics:
        with st.expander(f"📖 {topic.name}"):
            st.markdown(f"**Summary:** {topic.summary}")
            
            if topic.key_points:
                st.markdown("**Key Points:**")
                for point in topic.key_points:
                    st.markdown(f"- {point}")
            
            if topic.mnemonics:
                st.markdown("**Mnemonics:**")
                for mnemonic in topic.mnemonics:
                    st.info(mnemonic)
            
            if topic.subtopics:
                st.markdown(f"**Subtopics:** {', '.join(topic.subtopics)}")
            
            # Show Mermaid Diagram if available
            mermaid_content = get_mermaid_content(topic.name)
            if mermaid_content:
                st.markdown("### 🧠 Mind Map")
                st.markdown(mermaid_content)

            # Show Animation if available
            anim_path = get_animation_content(topic.name)
            if anim_path:
                st.markdown("### 🎬 Animation")
                # st.image(anim_path) if anim_path.endswith('.gif') else st.video(anim_path)
                anim_path = str(anim_path)
                if anim_path.endswith(".gif"):
                    st.image(anim_path)
                else:
                    st.video(anim_path)
            # Show PYQ Solutions if available (Linked to Module)
            pyq_content = get_pyq_content(topic.name)
            if pyq_content:
                with st.expander("📝 Previous Year Questions (Module Level)"):
                     st.markdown(pyq_content)

            # Actions
            col1, col2 = st.columns(2)
            with col1:
                # Generate mnemonic button
                if topic.key_points and len(topic.key_points) > 0:
                    if st.button(f"Generate Mnemonic", key=f"mnemonic_{topic.id}"):
                        mnemonic = create_acronym_mnemonic(topic.name, topic.key_points)
                        st.success(f"**{mnemonic.content}** - {mnemonic.explanation}")
            
            with col2:
                # Generate Animation Button
                if not anim_path:
                    if st.button(f"Generate Animation", key=f"anim_{topic.id}"):
                        new_anim_path = generate_topic_animation(topic.name, topic.summary)
                        if new_anim_path:
                            st.success(f"Animation created at {new_anim_path}")
                            st.rerun()


def show_mindmap_page():
    st.header("🗺️ Mind Map Explorer")
    
    topics = st.session_state.kb.get_topics()
    
    if not topics:
        st.warning("No topics found. Add some topics first!")
        return
    
    # Generate mind map
    generator = MindMapGenerator()
    generator.add_topics_from_syllabus(topics, root_name="My Learning Path")
    
    graph_data = generator.get_graph_data()
    
    st.markdown("### Topic Relationships")
    
    # Display as a simple tree structure
    st.markdown("**Root: My Learning Path**")
    for topic in topics:
        st.markdown(f"  - {topic.name}")
        for subtopic in topic.subtopics:
            st.markdown(f"    - {subtopic}")
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export as JSON"):
            try:
                generator.export_to_json("data/mindmap.json")
                st.success("Mind map exported to data/mindmap.json")
                
                # Check if file exists before reading
                if Path("data/mindmap.json").exists():
                    with open("data/mindmap.json", "r") as f:
                        st.download_button(
                            label="Download JSON",
                            data=f.read(),
                            file_name="mindmap.json",
                            mime="application/json"
                        )
                else:
                    st.error("Export file not found")
            except Exception as e:
                st.error(f"Error exporting mind map: {e}")


def show_quiz_page():
    st.header("❓ Quiz Mode")
    
    topics = st.session_state.kb.get_topics()
    
    if not topics:
        st.warning("No topics found. Add some topics first!")
        return
    
    # Topic selection
    topic_names = [topic.name for topic in topics]
    selected_topic = st.selectbox("Select a topic:", ["All Topics"] + topic_names)
    
    # Get questions
    if selected_topic == "All Topics":
        questions = st.session_state.kb.get_questions()
    else:
        questions = st.session_state.kb.get_questions(selected_topic)
    
    if not questions:
        st.info("No questions available for this topic yet.")
        return
    
    # Quiz interface
    if st.session_state.current_question_idx < len(questions):
        q = questions[st.session_state.current_question_idx]
        
        st.markdown(f"### Question {st.session_state.current_question_idx + 1} of {len(questions)}")
        st.markdown(f"**Topic:** {q.topic}")
        st.markdown(f"**Difficulty:** {q.difficulty}")
        st.markdown(f"**Question:** {q.question}")
        
        # Answer input
        user_answer = st.text_area("Your answer:", key=f"answer_{st.session_state.current_question_idx}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Show Answer"):
                st.success(f"**Correct Answer:** {q.answer}")
        
        with col2:
            if st.button("Next Question"):
                st.session_state.current_question_idx += 1
                st.rerun()
    else:
        st.success("Quiz completed! 🎉")
        if st.button("Restart Quiz"):
            st.session_state.current_question_idx = 0
            st.rerun()


def show_differences_page():
    st.header("📊 Learning with Contrasts")
    
    st.markdown("Compare and contrast concepts to understand them better!")
    
    # Show example differences
    examples = ["tcp_vs_udp", "stack_vs_queue"]
    selected_example = st.selectbox("Select an example:", examples)
    
    diff = get_example_difference(selected_example)
    
    if diff:
        st.markdown(f"### {diff.concept_a} vs {diff.concept_b}")
        
        # Create a comparison table
        import pandas as pd
        
        data = []
        for item in diff.differences:
            data.append({
                "Aspect": item["aspect"],
                diff.concept_a: item["concept_a_value"],
                diff.concept_b: item["concept_b_value"]
            })
        
        df = pd.DataFrame(data)
        st.table(df)


def show_animations_page():
    st.header("🎬 Educational Animations")
    
    st.markdown("Visual learning through animations!")
    
    animation_type = st.selectbox(
        "Select animation type:",
        ["TCP 3-Way Handshake", "Stack Operations"]
    )
    
    if st.button("Generate Animation"):
        with st.spinner("Creating animation..."):
            try:
                if animation_type == "TCP 3-Way Handshake":
                    from visual import create_tcp_handshake_animation
                    output_path = create_tcp_handshake_animation()
                    st.success(f"Animation created at {output_path}")
                elif animation_type == "Stack Operations":
                    from visual import create_stack_animation
                    output_path = create_stack_animation()
                    st.success(f"Animation created at {output_path}")
                
                st.info("Animation saved! You can find it in the data/animations directory.")
            except Exception as e:
                st.error(f"Error creating animation: {e}")


def show_add_content_page():
    st.header("➕ Add New Content")
    
    content_type = st.radio("What would you like to add?", ["Topic", "Question"])
    
    if content_type == "Topic":
        with st.form("add_topic_form"):
            name = st.text_input("Topic Name*")
            summary = st.text_area("Summary*")
            key_points = st.text_area("Key Points (one per line)")
            subtopics = st.text_input("Subtopics (comma-separated)")
            
            submitted = st.form_submit_button("Add Topic")
            
            if submitted:
                if name and summary:
                    topic = Topic(
                        name=name,
                        summary=summary,
                        key_points=[kp.strip() for kp in key_points.split("\n") if kp.strip()],
                        subtopics=[st.strip() for st in subtopics.split(",") if st.strip()]
                    )
                    st.session_state.kb.save_topic(topic)
                    st.success(f"Topic '{name}' added successfully!")
                else:
                    st.error("Please fill in all required fields (*)")
    
    elif content_type == "Question":
        topics = st.session_state.kb.get_topics()
        topic_names = [topic.name for topic in topics]
        
        if not topic_names:
            st.warning("Please add some topics first!")
            return
        
        with st.form("add_question_form"):
            topic = st.selectbox("Topic*", topic_names)
            question = st.text_area("Question*")
            answer = st.text_area("Answer*")
            difficulty = st.select_slider("Difficulty", options=["easy", "medium", "hard"])
            
            submitted = st.form_submit_button("Add Question")
            
            if submitted:
                if topic and question and answer:
                    q = Question(
                        topic=topic,
                        question=question,
                        answer=answer,
                        difficulty=difficulty
                    )
                    st.session_state.kb.save_question(q)
                    st.success("Question added successfully!")
                else:
                    st.error("Please fill in all required fields (*)")


if __name__ == "__main__":
    main()
