"""
Visualization utilities for the Streamlit app.
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import difflib
from typing import List, Dict, Tuple
from core.models import AnalyzedQuestion
import re

def clean_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def get_similarity(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return difflib.SequenceMatcher(None, clean_text(s1), clean_text(s2)).ratio()

def cluster_similar_questions(questions: List[AnalyzedQuestion], threshold: float = 0.8) -> List[Dict]:
    """
    Cluster questions that are similar to find repeats.
    Returns a list of clusters. Each cluster has 'main_question', 'count', 'years', 'marks'.
    """
    clusters = []
    processed_ids = set()
    
    # Sort by length to use longer questions as potential "main" representatives or just stable order
    sorted_qs = sorted(questions, key=lambda q: len(q.text), reverse=True)
    
    for i, q1 in enumerate(sorted_qs):
        if q1.id in processed_ids:
            continue
            
        current_cluster = {
            "text": q1.text,
            "questions": [q1],
            "years": {q1.year} if q1.year else set(),
            "total_marks": q1.marks,
            "modules": {q1.module} if q1.module else set()
        }
        processed_ids.add(q1.id)
        
        for j, q2 in enumerate(sorted_qs):
            if i == j or q2.id in processed_ids:
                continue
                
            sim = get_similarity(q1.text, q2.text)
            if sim >= threshold:
                current_cluster["questions"].append(q2)
                if q2.year:
                    current_cluster["years"].add(q2.year)
                current_cluster["total_marks"] += q2.marks
                if q2.module:
                    current_cluster["modules"].add(q2.module)
                processed_ids.add(q2.id)
        
        clusters.append(current_cluster)
        
    return clusters

def plot_questions_per_module(questions: List[AnalyzedQuestion]):
    """
    Plots the number of questions and total marks per module.
    """
    if not questions:
        st.info("No data to visualize.")
        return

    # Convert to DataFrame
    data = []
    for q in questions:
        data.append({
            "Module": q.module if q.module else "Unknown",
            "Marks": q.marks,
            "Count": 1
        })
    
    df = pd.DataFrame(data)
    
    # Group by Module
    grouped = df.groupby("Module").sum().reset_index()
    
    st.subheader("📊 Question Bank Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Questions per Module**")
        fig1, ax1 = plt.subplots()
        ax1.bar(grouped["Module"], grouped["Count"], color='skyblue')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig1)
        
    with col2:
        st.markdown("**Total Marks per Module**")
        fig2, ax2 = plt.subplots()
        ax2.bar(grouped["Module"], grouped["Marks"], color='salmon')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig2)

def plot_marks_distribution(questions: List[AnalyzedQuestion]):
    """
    Plots the distribution of marks across years if available.
    """
    if not questions:
        return
        
    data = []
    for q in questions:
        if q.year and q.year != "Unknown":
            data.append({
                "Year": q.year,
                "Marks": q.marks,
                "Module": q.module
            })
            
    if not data:
        return
        
    df = pd.DataFrame(data)
    
    st.subheader("📈 Marks Trend by Year")
    
    # Pivot for Stacked Bar Chart: Year vs Marks, colored by Module
    pivot = df.pivot_table(index="Year", columns="Module", values="Marks", aggfunc="sum", fill_value=0)
    
    st.bar_chart(pivot)

def analyze_repeated_questions(questions: List[AnalyzedQuestion]):
    """
    Analyze and display repeated questions to identify high-yield topics.
    """
    st.subheader("🔄 High-Yield / Repeated Questions")
    st.info("These questions have appeared in multiple years or are significantly similar. Prioritize these concepts!")
    
    clusters = cluster_similar_questions(questions, threshold=0.8)
    
    # Filter for clusters with more than 1 occurrence AND appearing in more than 1 year (or just high frequency)
    # The user complained about "same year" repeats being shown as if they are high yield.
    # True "High Yield" implies predictability across papers (years).
    # So we prefer len(years) > 1.
    
    repeats = []
    for c in clusters:
        # Condition: More than 1 question in cluster AND (More than 1 unique year OR Count > 2)
        # We enforce distinct years to avoid "Part A + Part B" of same year being flagged as "Recurring".
        if len(c["questions"]) > 1 and len(c["years"]) > 1:
            repeats.append(c)
            
    # Sort by frequency (count) then total marks
    repeats.sort(key=lambda c: (len(c["questions"]), c["total_marks"]), reverse=True)
    
    if not repeats:
        st.warning("No repeated questions found across different years.")
        return

    for cluster in repeats:
        count = len(cluster["questions"])
        years = ", ".join(sorted(list(cluster["years"])))
        modules = ", ".join(list(cluster["modules"]))
        
        with st.expander(f"🔥 {count} Occurrences: {cluster['text'][:80]}..."):
            st.markdown(f"**Modules:** {modules}")
            st.markdown(f"**Years Appeared:** {years}")
            st.markdown(f"**Total Marks Accumulation:** {cluster['total_marks']}")
            st.markdown("**Variations:**")
            for q in cluster["questions"]:
                st.markdown(f"- ({q.year}) {q.text} *[{q.marks} Marks]*")