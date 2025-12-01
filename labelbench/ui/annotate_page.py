"""Streamlit page for annotating samples."""

import streamlit as st

from models.annotation import Annotation


def show_annotate_page():
    """
    Render the annotation UI and manage per-sample annotation state.
    
    Displays the current unannotated sample (prompt, response, metadata), progress, and controls for accepting or rejecting a sample. Loads fresh annotation data from the database via st.session_state.db, updates session state keys (e.g., samples_to_annotate, current_index, show_rejection_form), inserts annotations on accept/reject, and advances or refreshes the UI as needed (may trigger st.rerun()). When rejecting, requires explanatory notes and a selected primary issue before saving.
    """
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
    
    # Always reload unannotated samples to ensure freshness
    unannotated_samples = db.get_unannotated_samples()
    total_samples = db.get_total_samples()
    stats = db.get_annotation_stats()
    
    # Check if all samples are annotated
    if total_samples > 0 and stats['total_annotated'] >= total_samples:
        st.info("All samples have been annotated!")
        st.metric("Completed Annotations", stats['total_annotated'])
        st.metric("Total Samples", total_samples)
        st.success("✅ Annotation complete! All samples have been reviewed.")
        return
    
    # Check if there are samples to annotate
    if not unannotated_samples:
        st.info("No samples to annotate. Import data to get started.")
        
        # Show stats
        if stats['total_annotated'] > 0:
            st.metric("Completed Annotations", stats['total_annotated'])
            st.metric("Total Samples", total_samples)
        
        return
    
    # Update session state with fresh unannotated samples
    st.session_state.samples_to_annotate = unannotated_samples
    
    # Get current sample with bounds checking
    current_idx = st.session_state.get('current_index', 0)
    
    # Validate bounds
    if current_idx < 0:
        current_idx = 0
        st.session_state.current_index = 0
    elif current_idx >= len(unannotated_samples):
        current_idx = max(0, len(unannotated_samples) - 1)
        st.session_state.current_index = current_idx
    
    if not unannotated_samples or current_idx >= len(unannotated_samples):
        st.warning("No samples available. Please import data first.")
        return
    
    sample = unannotated_samples[current_idx]
    
    # Verify this sample hasn't been annotated (double-check)
    existing_annotation = db.get_annotation(sample.id)
    if existing_annotation is not None:
        # This sample was already annotated, reload and skip
        st.session_state.samples_to_annotate = db.get_unannotated_samples()
        st.session_state.current_index = 0
        st.rerun()
        return
    
    # Progress indicator
    progress = (current_idx + 1) / len(unannotated_samples)
    st.progress(progress)
    st.caption(f"Sample {current_idx + 1} of {len(unannotated_samples)} | ID: {sample.id}")
    
    # Show annotation status
    remaining = len(unannotated_samples) - (current_idx + 1)
    if remaining > 0:
        st.caption(f"📊 {stats['total_annotated']} annotated | {remaining} remaining")
    
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
        if st.button("❌ Reject", use_container_width=True, type="secondary"):
            st.session_state.show_rejection_form = True
            st.rerun()
    
    with col2:
        if st.button("✅ Accept", use_container_width=True, type="primary"):
            # Double-check sample hasn't been annotated
            if db.get_annotation(sample.id) is None:
                # Save acceptance annotation
                annotation = Annotation(
                    sample_id=sample.id,
                    is_acceptable=True
                )
                db.insert_annotation(annotation)
                
                # Reload unannotated samples and move to next
                _move_to_next_sample()
            else:
                st.warning("This sample was already annotated. Refreshing...")
                st.session_state.samples_to_annotate = db.get_unannotated_samples()
                st.session_state.current_index = 0
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
                "Notes *",
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
                    # Double-check sample hasn't been annotated
                    if db.get_annotation(sample.id) is None:
                        # Save rejection annotation
                        annotation = Annotation(
                            sample_id=sample.id,
                            is_acceptable=False,
                            primary_issue=primary_issue,
                            notes=notes.strip()
                        )
                        db.insert_annotation(annotation)
                        
                        # Clear form state
                        st.session_state.show_rejection_form = False
                        
                        # Move to next sample
                        _move_to_next_sample()
                    else:
                        st.warning("This sample was already annotated. Refreshing...")
                        st.session_state.show_rejection_form = False
                        st.session_state.samples_to_annotate = db.get_unannotated_samples()
                        st.session_state.current_index = 0
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
            max_value=len(unannotated_samples),
            value=current_idx + 1,
            key="jump_input"
        )
        if st.button("Go", use_container_width=True):
            # Validate jump_to index
            target_idx = max(0, min(jump_to - 1, len(unannotated_samples) - 1))
            st.session_state.current_index = target_idx
            st.session_state.show_rejection_form = False
            st.rerun()
    
    with col3:
        if st.button("Next →", disabled=(current_idx == len(unannotated_samples) - 1)):
            st.session_state.current_index += 1
            st.session_state.show_rejection_form = False
            st.rerun()


def _move_to_next_sample():
    """
    Advance the session to the next unannotated sample and refresh the UI.
    
    Reloads the current list of unannotated samples from the database and updates session state accordingly. If no unannotated samples remain, clears the session list and resets the current index to 0. If there are samples, increments the current index when not at the end of the list; if at the end, resets the index to 0 to allow reloading. Triggers a Streamlit rerun to refresh the page.
    
    Side effects:
    - Updates st.session_state.samples_to_annotate and st.session_state.current_index.
    - Calls st.rerun() to refresh the app.
    """
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
