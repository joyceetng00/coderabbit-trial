"""LabelBench - Main Streamlit application."""

import streamlit as st

from storage.database import Database
from ui.annotate_page import show_annotate_page
from ui.analysis_page import show_analysis_page
from ui.import_page import show_import_page


# Page configuration
st.set_page_config(
    page_title="LabelBench",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database in session state
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Sidebar navigation
with st.sidebar:
    st.title("LabelBench")
    st.caption("Annotation tool for LLM evaluation datasets")
    
    st.divider()
    
    page = st.radio(
        "Navigation",
        ["Annotate", "Error Analysis", "Import Data"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Quick stats in sidebar
    db = st.session_state.db
    total_samples = db.get_total_samples()
    stats = db.get_annotation_stats()
    
    st.metric("Total Samples", total_samples)
    st.metric("Annotated", stats['total_annotated'])
    
    if stats['total_annotated'] > 0:
        st.metric("Acceptance Rate", f"{stats['acceptance_rate']:.1f}%")

# Route to appropriate page
if page == "Annotate":
    show_annotate_page()
elif page == "Error Analysis":
    show_analysis_page()
elif page == "Import Data":
    show_import_page()

