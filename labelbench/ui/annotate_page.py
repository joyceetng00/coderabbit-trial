"""Streamlit page for annotating samples."""

import streamlit as st

from models.annotation import Annotation


def show_annotate_page():
    """Display the annotation interface."""
    # Custom CSS for button colors
    st.markdown("""
    <style>
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"] {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
        color: white !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background-color: #c82333 !important;
        border-color: #bd2130 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Annotate Samples")
    
    db = st.session_state.db
    
    # Get all samples for navigation
    all_samples = db.get_all_samples()
    total_samples = len(all_samples)
    stats = db.get_annotation_stats()
    
    # Check if there are any samples
    if not all_samples:
        st.info("No samples to annotate. Import data to get started.")
        return
    
    # Get current sample with bounds checking
    current_idx = st.session_state.get('current_index', 0)
    
    # Validate and clamp bounds to ensure we always have a valid index
    if current_idx < 0:
        current_idx = 0
    elif current_idx >= len(all_samples):
        current_idx = max(0, len(all_samples) - 1)
    
    # Update session state with clamped index
    st.session_state.current_index = current_idx
    
    # Get the sample at the current index
    sample = all_samples[current_idx]
    
    # Check if sample has existing annotation
    existing_annotation = db.get_annotation(sample.id)
    
    # Progress indicator - show actual annotation progress
    if total_samples > 0:
        progress = stats['total_annotated'] / total_samples
        st.progress(progress)
        st.caption(f"Progress: {stats['total_annotated']} of {total_samples} samples annotated ({progress*100:.1f}%)")
    
    # Show current sample info with annotation status
    annotation_status = ""
    if existing_annotation:
        status_text = "✅ ACCEPTED" if existing_annotation.is_acceptable else "❌ REJECTED"
        annotation_status = f" | Status: {status_text}"
    else:
        annotation_status = " | Status: ⚪ NOT ANNOTATED"
    
    st.caption(f"📝 Sample ID: {sample.id} | Position: {current_idx + 1} of {total_samples}{annotation_status}")
    
    # Display metadata
    if sample.metadata:
        metadata_cols = st.columns(len(sample.metadata))
        for i, (key, value) in enumerate(sample.metadata.items()):
            metadata_cols[i].metric(key, value)
    
    st.divider()
    
    # Display prompt
    st.subheader("Prompt")
    st.text_area(
        "Prompt",
        value=sample.prompt,
        height=100,
        disabled=True,
        label_visibility="collapsed",
        key=f"prompt_display_{sample.id}"
    )
    
    # Display response
    st.subheader("Response")
    st.text_area(
        "Response",
        value=sample.response,
        height=150,
        disabled=True,
        label_visibility="collapsed",
        key=f"response_display_{sample.id}"
    )
    
    st.divider()
    
    # Annotation form
    st.subheader("Quality Assessment")
    
    # Show current annotation if it exists
    if existing_annotation:
        current_decision = "ACCEPTED" if existing_annotation.is_acceptable else "REJECTED"
        st.info(f"Current annotation: {current_decision} (click below to change)")
        if existing_annotation.primary_issue:
            st.caption(f"Issue: {existing_annotation.primary_issue}")
        if existing_annotation.notes:
            st.caption(f"Notes: {existing_annotation.notes}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Reject", use_container_width=True, type="secondary"):
            st.session_state.show_rejection_form = True
            st.rerun()
    
    with col2:
        if st.button("Accept", use_container_width=True, type="primary"):
            # Create or update annotation
            annotation = Annotation(
                sample_id=sample.id,
                is_acceptable=True
            )
            # If updating existing annotation, keep the same ID
            if existing_annotation:
                annotation.id = existing_annotation.id
            
            db.insert_annotation(annotation)
            st.success("Sample accepted!")
            st.rerun()
    
    # Show rejection form if reject was clicked
    if st.session_state.get('show_rejection_form', False):
        st.divider()
        st.subheader("Rejection Details")
        
        with st.form("rejection_form"):
            # Pre-fill form if editing existing rejection
            default_issue = None
            default_notes = ""
            if existing_annotation and not existing_annotation.is_acceptable:
                default_issue = existing_annotation.primary_issue
                default_notes = existing_annotation.notes or ""
            
            issue_options = [
                "hallucination",
                "incomplete",
                "wrong_format",
                "off_topic",
                "inappropriate_tone",
                "refusal",
                "other"
            ]
            
            default_index = 0
            if default_issue and default_issue in issue_options:
                default_index = issue_options.index(default_issue)
            
            primary_issue = st.selectbox(
                "Primary Issue",
                issue_options,
                index=default_index,
                help="Select the main reason for rejecting this response"
            )
            
            notes = st.text_area(
                "Notes *",
                value=default_notes,
                placeholder="Provide additional context about why this response was rejected...",
                height=100,
                help="Required: Please explain why this response was rejected"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("Submit Annotation", type="primary", use_container_width=True)
            
            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            
            if submitted:
                # Validate notes are provided
                if not notes or not notes.strip():
                    st.error("⚠️ Notes are required when rejecting a sample. Please provide an explanation.")
                else:
                    # Create or update annotation
                    annotation = Annotation(
                        sample_id=sample.id,
                        is_acceptable=False,
                        primary_issue=primary_issue,
                        notes=notes.strip()
                    )
                    # If updating existing annotation, keep the same ID
                    if existing_annotation:
                        annotation.id = existing_annotation.id
                    
                    db.insert_annotation(annotation)
                    
                    # Clear form state
                    st.session_state.show_rejection_form = False
                    st.success("Sample rejected!")
                    st.rerun()
            
            if cancelled:
                st.session_state.show_rejection_form = False
                st.rerun()
    
    # Navigation
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Previous", disabled=(current_idx == 0)):
            st.session_state.current_index -= 1
            st.session_state.show_rejection_form = False
            st.rerun()
    
    with col2:
        jump_to = st.number_input(
            "Jump to sample",
            min_value=1,
            max_value=total_samples,
            value=current_idx + 1,
            key=f"jump_input_{total_samples}_{current_idx}"
        )
        if st.button("Go", use_container_width=True):
            if 1 <= jump_to <= total_samples:
                st.session_state.current_index = jump_to - 1
                st.session_state.show_rejection_form = False
                st.rerun()
    
    with col3:
        if st.button("Next →", disabled=(current_idx == len(all_samples) - 1)):
            st.session_state.current_index += 1
            st.session_state.show_rejection_form = False
            st.rerun()


def _move_to_next_sample():
    """Helper to move to next sample and handle end of list."""
    db = st.session_state.db
    
    # Always reload fresh unannotated samples from database
    new_samples = db.get_unannotated_samples()
    
    if not new_samples:
        # All samples annotated - reset to show completion message
        st.session_state.samples_to_annotate = []
        st.session_state.current_index = 0
    else:
        # Update with fresh list
        st.session_state.samples_to_annotate = new_samples
        current_idx = st.session_state.get('current_index', 0)
        
        # Move to next if not at end, otherwise stay at current
        if current_idx < len(new_samples) - 1:
            st.session_state.current_index = current_idx + 1
        else:
            # At end of current list, but more might exist - reload
            st.session_state.current_index = 0
    
    st.rerun()

