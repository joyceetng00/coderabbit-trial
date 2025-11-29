"""Streamlit page for importing data."""

import streamlit as st
import tempfile
from pathlib import Path

from storage.import_export import import_csv, import_json


def show_import_page():
    """Display the import data page."""
    st.title("Import Data")
    
    st.markdown("""
    Upload a CSV or JSON file containing prompt-response pairs to annotate.
    
    **Required fields:** `id`, `prompt`, `response`  
    **Optional fields:** Any additional columns will be stored as metadata (e.g., `model`, `task_type`)
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'json'],
        help="Upload a CSV or JSON file with your samples"
    )
    
    if uploaded_file is not None:
        # Determine file type
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Import based on file type
            if file_extension == '.csv':
                samples = import_csv(tmp_path)
            elif file_extension == '.json':
                samples = import_json(tmp_path)
            else:
                st.error(f"Unsupported file type: {file_extension}")
                return
            
            st.success(f"Successfully parsed {len(samples)} samples")
            
            # Preview samples
            st.subheader("Preview (first 5 samples)")
            for i, sample in enumerate(samples[:5]):
                with st.expander(f"Sample {i+1}: {sample.id}"):
                    st.text(f"Prompt: {sample.prompt}")
                    st.text(f"Response: {sample.response}")
                    if sample.metadata:
                        st.json(sample.metadata)
            
            # Confirm import
            if st.button("Import to Database", type="primary"):
                db = st.session_state.db
                inserted = db.insert_samples(samples)
                
                if inserted == len(samples):
                    st.success(f"Imported all {inserted} samples successfully!")
                else:
                    st.warning(
                        f"Imported {inserted} out of {len(samples)} samples. "
                        f"{len(samples) - inserted} duplicates were skipped."
                    )
                
                # Clear any cached annotation state
                if 'samples_to_annotate' in st.session_state:
                    del st.session_state.samples_to_annotate
                    del st.session_state.current_index
                
                st.info("Navigate to Annotate to start annotating samples.")
        
        except Exception as e:
            st.error(f"Error importing file: {str(e)}")
        
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)
    
    # Show current database stats
    st.divider()
    st.subheader("Current Database")
    
    db = st.session_state.db
    total_samples = db.get_total_samples()
    stats = db.get_annotation_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Samples", total_samples)
    col2.metric("Annotated", stats['total_annotated'])
    col3.metric("Remaining", total_samples - stats['total_annotated'])

