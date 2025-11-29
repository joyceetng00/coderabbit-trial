"""Streamlit page for annotating samples."""

import streamlit as st

from models.annotation import Annotation


def show_annotate_page():
    """Display the annotation interface."""
    st.title("Annotate Samples")
    
    db = st.session_state.db
    
    # Load unannotated samples
    if 'samples_to_annotate' not in st.session_state:
        st.session_state.samples_to_annotate = db.get_unannotated_samples()
        st.session_state.current_index = 0
    
    samples = st.session_state.samples_to_annotate
    
    # Check if there are samples to annotate
    if not samples:
        st.info("No samples to annotate. Import data to get started.")
        
        # Show stats
        stats = db.get_annotation_stats()
        if stats['total_annotated'] > 0:
            st.metric("Completed Annotations", stats['total_annotated'])
            st.success("All samples have been annotated!")
        
        return
    
    # Get current sample with bounds checking
    current_idx = st.session_state.get('current_index', 0)
    
    # Validate bounds
    if current_idx < 0:
        current_idx = 0
        st.session_state.current_index = 0
    elif current_idx >= len(samples):
        current_idx = max(0, len(samples) - 1)
        st.session_state.current_index = current_idx
    
    if not samples or current_idx >= len(samples):
        st.warning("No samples available. Please import data first.")
        return
    
    sample = samples[current_idx]
    
    # Progress indicator
    progress = (current_idx + 1) / len(samples)
    st.progress(progress)
    st.caption(f"Sample {current_idx + 1} of {len(samples)} | ID: {sample.id}")
    
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
        key="prompt_display"
    )
    
    # Display response
    st.subheader("Response")
    st.text_area(
        "Response",
        value=sample.response,
        height=150,
        disabled=True,
        label_visibility="collapsed",
        key="response_display"
    )
    
    st.divider()
    
    # Annotation form
    st.subheader("Quality Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Accept", use_container_width=True, type="primary"):
            # Save acceptance annotation
            annotation = Annotation(
                sample_id=sample.id,
                is_acceptable=True
            )
            db.insert_annotation(annotation)
            
            # Move to next sample
            _move_to_next_sample(samples)
    
    with col2:
        if st.button("Reject", use_container_width=True):
            st.session_state.show_rejection_form = True
            st.rerun()
    
    # Show rejection form if reject was clicked
    if st.session_state.get('show_rejection_form', False):
        st.divider()
        st.subheader("Rejection Details")
        
        with st.form("rejection_form"):
            primary_issue = st.selectbox(
                "Primary Issue",
                [
                    "hallucination",
                    "factually_incorrect",
                    "incomplete",
                    "wrong_format",
                    "off_topic",
                    "inappropriate_tone",
                    "refusal",
                    "other"
                ],
                help="Select the main reason for rejecting this response"
            )
            
            notes = st.text_area(
                "Notes (optional)",
                placeholder="Provide additional context about why this response was rejected...",
                height=100
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("Submit Annotation", type="primary", use_container_width=True)
            
            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            
            if submitted:
                # Save rejection annotation
                annotation = Annotation(
                    sample_id=sample.id,
                    is_acceptable=False,
                    primary_issue=primary_issue,
                    notes=notes if notes.strip() else None
                )
                db.insert_annotation(annotation)
                
                # Clear form state
                st.session_state.show_rejection_form = False
                
                # Move to next sample
                _move_to_next_sample(samples)
            
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
            max_value=len(samples),
            value=current_idx + 1,
            key="jump_input"
        )
        if st.button("Go", use_container_width=True):
            # Validate jump_to index
            target_idx = max(0, min(jump_to - 1, len(samples) - 1))
            st.session_state.current_index = target_idx
            st.session_state.show_rejection_form = False
            st.rerun()
    
    with col3:
        if st.button("Next →", disabled=(current_idx == len(samples) - 1)):
            st.session_state.current_index += 1
            st.session_state.show_rejection_form = False
            st.rerun()


def _move_to_next_sample(samples):
    """Helper to move to next sample and handle end of list."""
    current_idx = st.session_state.get('current_index', 0)
    
    # Validate bounds
    if not samples:
        return
    
    if current_idx < 0:
        current_idx = 0
    elif current_idx >= len(samples):
        current_idx = max(0, len(samples) - 1)
    
    if current_idx < len(samples) - 1:
        st.session_state.current_index = current_idx + 1
    else:
        # Reached end, reload unannotated samples
        db = st.session_state.db
        new_samples = db.get_unannotated_samples()
        if new_samples:
            st.session_state.samples_to_annotate = new_samples
            st.session_state.current_index = 0
        else:
            # No more samples, stay at last position
            st.session_state.current_index = len(samples) - 1
    
    st.rerun()

