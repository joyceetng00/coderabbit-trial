"""Streamlit page for annotating samples with free navigation."""

import streamlit as st

from models.annotation import Annotation


def show_annotate_page():
    """Display the annotation interface with free navigation between all samples."""
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
    .finalized-banner {
        background-color: #e6f3ff;
        border: 2px solid #0066cc;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        color: #0066cc;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Annotate Samples")
    
    db = st.session_state.db
    
    # Get all samples and annotation summary
    all_samples = db.get_all_samples()
    summary = db.get_annotation_summary()
    all_finalized = db.are_all_annotations_final()
    
    if not all_samples:
        st.info("No samples to annotate. Import data to get started.")
        return
    
    total_samples = len(all_samples)
    
    # Show finalization banner if annotations are finalized
    if all_finalized and summary['draft_annotations'] == 0:
        st.markdown("""
        <div class="finalized-banner">
        🔒 All annotations have been finalized and cannot be edited. 
        To make changes, go to Settings and reset annotations.
        </div>
        """, unsafe_allow_html=True)
    
    # Progress overview
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Samples", summary['total_samples'])
    col2.metric("Draft Annotations", summary['draft_annotations'], delta=None if all_finalized else f"{summary['draft_annotations']}/{total_samples}")
    col3.metric("Unannotated", summary['unannotated'])
    col4.metric("Progress", f"{((summary['draft_annotations'] + summary['final_annotations']) / total_samples * 100):.0f}%")
    
    # Sample navigation
    st.divider()
    st.subheader("Sample Navigation")
    
    # Get current sample index (1-based for user display)
    current_sample_num = st.session_state.get('current_sample_num', 1)
    
    # Clamp to valid range
    if current_sample_num < 1:
        current_sample_num = 1
    elif current_sample_num > total_samples:
        current_sample_num = total_samples
    
    # Update session state
    st.session_state.current_sample_num = current_sample_num
    
    # Navigation controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Previous", disabled=(current_sample_num == 1)):
            st.session_state.current_sample_num -= 1
            st.session_state.show_rejection_form = False
            st.rerun()
    
    with col2:
        # Sample selector
        new_sample_num = st.number_input(
            f"Sample (1 to {total_samples})",
            min_value=1,
            max_value=total_samples,
            value=current_sample_num,
            step=1,
            key=f"sample_selector_{total_samples}"
        )
        if new_sample_num != current_sample_num:
            st.session_state.current_sample_num = new_sample_num
            st.session_state.show_rejection_form = False
            st.rerun()
    
    with col3:
        if st.button("Next →", disabled=(current_sample_num == total_samples)):
            st.session_state.current_sample_num += 1
            st.session_state.show_rejection_form = False
            st.rerun()
    
    # Quick navigation buttons
    if total_samples <= 20:  # Only show for reasonable number of samples
        st.caption("Quick jump:")
        quick_nav_cols = st.columns(min(total_samples, 10))
        for i in range(min(total_samples, 10)):
            sample_idx = i + 1
            with quick_nav_cols[i]:
                # Get annotation status for this sample
                sample = all_samples[sample_idx - 1]
                annotation = db.get_annotation(sample.id)
                
                if annotation:
                    if annotation.status == "final":
                        button_type = "primary" if annotation.is_acceptable else "secondary"
                        label = f"{'✅' if annotation.is_acceptable else '❌'} {sample_idx}"
                    else:  # draft
                        button_type = "primary" if annotation.is_acceptable else "secondary" 
                        label = f"{'📝✅' if annotation.is_acceptable else '📝❌'} {sample_idx}"
                else:
                    button_type = None
                    label = f"⚪ {sample_idx}"
                
                # Don't pass type=None to button
                if button_type:
                    clicked = st.button(label, key=f"quick_nav_{sample_idx}", type=button_type, use_container_width=True)
                else:
                    clicked = st.button(label, key=f"quick_nav_{sample_idx}", use_container_width=True)
                
                if clicked:
                    st.session_state.current_sample_num = sample_idx
                    st.session_state.show_rejection_form = False
                    st.rerun()
    
    # Show remaining samples if more than 10
    if total_samples > 10:
        remaining_start = 11
        st.caption(f"Samples {remaining_start} to {total_samples} - use the number input above to navigate")
    
    # Current sample display
    st.divider()
    
    # Get the current sample
    current_sample = all_samples[current_sample_num - 1]
    existing_annotation = db.get_annotation(current_sample.id)
    
    # Sample header with status
    if existing_annotation:
        if existing_annotation.status == "final":
            status_emoji = "🔒"
            status_text = f"FINALIZED - {'ACCEPTED' if existing_annotation.is_acceptable else 'REJECTED'}"
            status_color = "green" if existing_annotation.is_acceptable else "red"
        else:  # draft
            status_emoji = "📝"
            status_text = f"DRAFT - {'ACCEPTED' if existing_annotation.is_acceptable else 'REJECTED'}"
            status_color = "blue"
    else:
        status_emoji = "⚪"
        status_text = "NOT ANNOTATED"
        status_color = "gray"
    
    st.markdown(f"""
    ### {status_emoji} Sample {current_sample_num} of {total_samples}
    **ID:** `{current_sample.id}` | **Status:** <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
    """, unsafe_allow_html=True)
    
    # Display metadata
    if current_sample.metadata:
        metadata_cols = st.columns(len(current_sample.metadata))
        for i, (key, value) in enumerate(current_sample.metadata.items()):
            metadata_cols[i].metric(key, value)
    
    st.divider()
    
    # Display prompt and response
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Prompt")
        st.text_area(
            "Prompt",
            value=current_sample.prompt,
            height=200,
            disabled=True,
            label_visibility="collapsed",
            key=f"prompt_display_{current_sample.id}"
        )
    
    with col2:
        st.subheader("Response")
        st.text_area(
            "Response",
            value=current_sample.response,
            height=200,
            disabled=True,
            label_visibility="collapsed",
            key=f"response_display_{current_sample.id}"
        )
    
    st.divider()
    
    # Annotation interface
    if all_finalized:
        st.info("🔒 Annotations are finalized and cannot be edited.")
        if existing_annotation:
            _show_read_only_annotation(existing_annotation)
    else:
        _show_annotation_interface(current_sample, existing_annotation, db)
    
    # Master submission section
    if not all_finalized:
        st.divider()
        _show_submission_interface(summary, db)


def _show_read_only_annotation(annotation: Annotation):
    """Show annotation in read-only mode."""
    st.subheader("Current Annotation (Read-Only)")
    
    col1, col2 = st.columns(2)
    with col1:
        decision = "✅ ACCEPTED" if annotation.is_acceptable else "❌ REJECTED"
        st.metric("Decision", decision)
    
    if not annotation.is_acceptable:
        with col2:
            st.metric("Primary Issue", annotation.primary_issue or "Not specified")
        
        if annotation.notes:
            st.text_area(
                "Notes",
                value=annotation.notes,
                disabled=True,
                height=100
            )


def _show_annotation_interface(sample, existing_annotation, db):
    """Show the editable annotation interface."""
    st.subheader("Quality Assessment")
    
    # Show current annotation if exists
    if existing_annotation:
        st.info(f"📝 Current annotation: {'ACCEPTED' if existing_annotation.is_acceptable else 'REJECTED'} (draft - can be edited)")
        if existing_annotation.primary_issue:
            st.caption(f"Issue: {existing_annotation.primary_issue}")
        if existing_annotation.notes:
            st.caption(f"Notes: {existing_annotation.notes}")
    
    # Annotation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Reject", use_container_width=True, type="secondary"):
            st.session_state.show_rejection_form = True
            st.rerun()
    
    with col2:
        if st.button("✅ Accept", use_container_width=True, type="primary"):
            # Create or update annotation
            annotation = Annotation(
                sample_id=sample.id,
                is_acceptable=True,
                status="draft"
            )
            # If updating existing annotation, keep the same ID
            if existing_annotation:
                annotation.id = existing_annotation.id
            
            db.insert_annotation(annotation)
            st.success("Sample accepted! (Draft saved)")
            st.rerun()
    
    # Show rejection form if reject was clicked
    if st.session_state.get('show_rejection_form', False):
        st.divider()
        st.subheader("Rejection Details")
        
        with st.form("rejection_form"):
            # Pre-fill if editing existing rejection
            default_issue = existing_annotation.primary_issue if existing_annotation and not existing_annotation.is_acceptable else None
            default_notes = existing_annotation.notes if existing_annotation and not existing_annotation.is_acceptable else ""
            
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
                index=0 if not default_issue else [
                    "hallucination",
                    "incomplete",
                    "wrong_format", 
                    "off_topic",
                    "inappropriate_tone",
                    "refusal",
                    "other"
                ].index(default_issue),
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
                submitted = st.form_submit_button("Save Rejection", type="primary", use_container_width=True)
            
            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            
            if submitted:
                if not notes or not notes.strip():
                    st.error("⚠️ Notes are required when rejecting a sample.")
                else:
                    # Create or update annotation
                    annotation = Annotation(
                        sample_id=sample.id,
                        is_acceptable=False,
                        primary_issue=primary_issue,
                        notes=notes.strip(),
                        status="draft"
                    )
                    # If updating existing annotation, keep the same ID
                    if existing_annotation:
                        annotation.id = existing_annotation.id
                    
                    db.insert_annotation(annotation)
                    st.session_state.show_rejection_form = False
                    st.success("Sample rejected! (Draft saved)")
                    st.rerun()
            
            if cancelled:
                st.session_state.show_rejection_form = False
                st.rerun()


def _show_submission_interface(summary, db):
    """Show the master save/submit interface."""
    st.subheader("Submit Annotations")
    
    total_annotated = summary['draft_annotations'] + summary['final_annotations'] 
    total_samples = summary['total_samples']
    
    if summary['unannotated'] > 0:
        st.warning(f"⚠️ {summary['unannotated']} samples still need annotations before submission.")
        
        # Show progress bar
        progress = total_annotated / total_samples if total_samples > 0 else 0
        st.progress(progress, text=f"Progress: {total_annotated}/{total_samples} samples annotated ({progress*100:.0f}%)")
        
        # Show which samples are missing
        if summary['unannotated'] <= 10:
            all_samples = db.get_all_samples()
            missing_samples = []
            for i, sample in enumerate(all_samples):
                if db.get_annotation(sample.id) is None:
                    missing_samples.append(str(i + 1))
            if missing_samples:
                st.caption(f"Missing annotations for samples: {', '.join(missing_samples)}")
    else:
        st.success("✅ All samples have been annotated!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Draft", use_container_width=True, help="Save current annotations as drafts (can still be edited)"):
                st.success(f"✅ Saved {summary['draft_annotations']} draft annotations!")
        
        with col2:
            if st.button("🔒 Finalize & Submit All", type="primary", use_container_width=True, help="Lock all annotations - cannot be edited after this!"):
                # Confirmation dialog
                if not st.session_state.get('confirm_finalize', False):
                    st.session_state.confirm_finalize = True
                    st.rerun()
    
    # Finalization confirmation
    if st.session_state.get('confirm_finalize', False):
        st.warning("⚠️ **CONFIRM FINALIZATION**")
        st.write("This will permanently lock all annotations. You will not be able to edit them afterward.")
        st.write("Are you sure you want to finalize and submit all annotations?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔒 Yes, Finalize All", type="primary", use_container_width=True):
                finalized_count = db.finalize_all_annotations()
                st.session_state.confirm_finalize = False
                st.success(f"🔒 Finalized {finalized_count} annotations! All submissions are now locked.")
                st.rerun()
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_finalize = False
                st.rerun()