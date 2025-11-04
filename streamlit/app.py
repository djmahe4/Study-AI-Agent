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


def main():
    st.title("🧠 AI Learning Engine")
    st.markdown("*Learn with mind maps, animations, and structured knowledge*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["📚 Topics", "🗺️ Mind Map", "❓ Quiz Mode", "📊 Differences", "🎬 Animations", "➕ Add Content"]
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
            
            # Generate mnemonic button
            if topic.key_points and len(topic.key_points) > 0:
                if st.button(f"Generate Mnemonic for {topic.name}", key=f"mnemonic_{topic.id}"):
                    mnemonic = create_acronym_mnemonic(topic.name, topic.key_points)
                    st.success(f"**{mnemonic.content}** - {mnemonic.explanation}")


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
            generator.export_to_json("data/mindmap.json")
            st.success("Mind map exported to data/mindmap.json")
            with open("data/mindmap.json", "r") as f:
                st.download_button(
                    label="Download JSON",
                    data=f.read(),
                    file_name="mindmap.json",
                    mime="application/json"
                )


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
