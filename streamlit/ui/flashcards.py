import streamlit as st
from core.flashcards import FlashcardManager

def show_flashcards_page():
    st.header("🎴 Flashcards")
    
    fm = FlashcardManager()
    decks = fm.list_decks()

    # --- Sidebar: Deck Selection / Creation ---
    with st.sidebar:
        st.subheader("Decks")
        
        # Determine context
        current_subject = None
        try: 
            with open("data/.current_subject", "r") as f:
                current_subject = f.read().strip()
                if current_subject:
                    st.info(f"Context: {current_subject}")
        except: pass

        if st.toggle("Show all subjects", value=False):
            filtered_decks = decks
        else:
            if current_subject:
                filtered_decks = [d for d in decks if d.subject == current_subject]
            else:
                filtered_decks = decks

        # Deck options
        deck_names = [d.name for d in filtered_decks]
        if deck_names:
            selected_deck_name = st.selectbox("Select Deck", deck_names)
        else:
            selected_deck_name = None
            st.warning("No decks found.")

        st.divider()
        st.write("Create New Deck")
        new_deck_name = st.text_input("Deck Name")
        if st.button("Create Deck"):
            if new_deck_name:
                fm.create_deck(new_deck_name, subject=current_subject)
                st.success("Created!")
                st.rerun()

    # --- Main Content: Study Mode or stats ---
    if not selected_deck_name:
        st.info("Select or create a deck to start.")
        return

    # Find selected deck object
    deck = next((d for d in decks if d.name == selected_deck_name), None)
    if not deck: return

    st.subheader(f"Studying: {deck.name}")
    st.caption(f"{len(deck.cards)} cards | Subject: {deck.subject}")

    # Add Card UI
    with st.expander("Add New Card"):
        with st.form("add_card"):
            front = st.text_area("Front")
            back = st.text_area("Back")
            tag = st.text_input("Tag (optional)")
            if st.form_submit_button("Add Card"):
                fm.add_card(deck.id, front, back, tags=[tag] if tag else [])
                st.success("Card added!")
                st.rerun()

    if not deck.cards:
        st.info("Empty deck. Add some cards!")
        return

    # Study State
    if 'fc_index' not in st.session_state:
        st.session_state.fc_index = 0
    if 'fc_flipped' not in st.session_state:
        st.session_state.fc_flipped = False
    
    idx = st.session_state.fc_index
    if idx >= len(deck.cards):
        st.session_state.fc_index = 0
        idx = 0
        
    card = deck.cards[idx]
    
    # Card Display
    st.divider()
    
    # CSS for card
    st.markdown("""
    <style>
    .flashcard {
        padding: 50px;
        border-radius: 10px;
        background-color: #f0f2f6;
        color: #31333F;
        text-align: center;
        font-size: 24px;
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .dark-mode .flashcard {
        background-color: #262730;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    content = card.back if st.session_state.fc_flipped else card.front
    
    st.markdown(f'<div class="flashcard">{content}</div>', unsafe_allow_html=True)
    
    st.write("")
    
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c2:
        if st.button("🔄 Flip Card", use_container_width=True):
            st.session_state.fc_flipped = not st.session_state.fc_flipped
            st.rerun()
            
    with c1:
        if st.button("⬅️ Prev", disabled=(idx==0), use_container_width=True):
            st.session_state.fc_index -= 1
            st.session_state.fc_flipped = False
            st.rerun()
            
    with c3:
        if st.button("Next ➡️", disabled=(idx>=len(deck.cards)-1), use_container_width=True):
            st.session_state.fc_index += 1
            st.session_state.fc_flipped = False
            st.rerun()
