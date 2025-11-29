"""Streamlit page for error analysis dashboard."""

import streamlit as st
import plotly.express as px
import pandas as pd
import json


def show_analysis_page():
    """Display the error analysis dashboard."""
    st.title("Error Analysis")
    
    db = st.session_state.db
    stats = db.get_annotation_stats()
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Annotated", stats['total_annotated'])
    col2.metric("Acceptance Rate", f"{stats['acceptance_rate']:.1f}%")
    col3.metric("Rejected", stats['rejected'])
    
    # Check if there are any annotations
    if stats['total_annotated'] == 0:
        st.info("No annotations yet. Start annotating samples to see error analysis.")
        return
    
    # Check if there are any rejections
    if stats['rejected'] == 0:
        st.success("All annotated samples were accepted! No errors to analyze.")
        return
    
    st.divider()
    
    # Error distribution section
    st.subheader("What's Breaking?")
    st.caption("Click on a bar to see all samples with that issue")
    
    error_dist = db.get_error_distribution()
    
    if not error_dist:
        st.warning("No error types captured yet. Make sure to select a primary issue when rejecting samples.")
        return
    
    # Create dataframe for plotting
    df_errors = pd.DataFrame({
        'Issue Type': list(error_dist.keys()),
        'Count': list(error_dist.values())
    })
    
    # Calculate percentages
    total_errors = df_errors['Count'].sum()
    df_errors['Percentage'] = (df_errors['Count'] / total_errors * 100).round(1)
    df_errors = df_errors.sort_values('Count', ascending=False)
    
    # Create interactive Plotly chart
    fig = px.bar(
        df_errors,
        x='Issue Type',
        y='Count',
        text='Count',
        title=f"Error Distribution ({stats['rejected']} rejected samples)",
        hover_data=['Percentage'],
        color='Count',
        color_continuous_scale='Reds'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_title="Issue Type",
        yaxis_title="Number of Samples"
    )
    
    # Display chart with click handling
    selected_points = st.plotly_chart(
        fig,
        on_select="rerun",
        key="error_chart",
        use_container_width=True
    )
    
    # Handle bar click selection
    if selected_points and selected_points.selection and selected_points.selection.points:
        selected_issue = selected_points.selection.points[0].x
        
        st.divider()
        st.subheader(f"Samples with '{selected_issue}'")
        
        # Get filtered samples
        samples_with_issue = db.get_samples_by_issue(selected_issue)
        
        st.caption(f"Showing {len(samples_with_issue)} samples")
        
        # Display samples
        for sample, annotation in samples_with_issue:
            with st.expander(f"Sample: {sample.id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Prompt:**")
                    st.text(sample.prompt)
                    
                    if sample.metadata:
                        st.markdown("**Metadata:**")
                        st.json(sample.metadata)
                
                with col2:
                    st.markdown("**Response:**")
                    st.text(sample.response)
                    
                    if annotation.notes:
                        st.markdown("**Notes:**")
                        st.info(annotation.notes)
        
        # Export filtered samples
        st.divider()
        
        if st.button(f"Export these {len(samples_with_issue)} samples as CSV"):
            # Convert to dataframe
            export_data = []
            for sample, annotation in samples_with_issue:
                row = {
                    'id': sample.id,
                    'prompt': sample.prompt,
                    'response': sample.response,
                    'primary_issue': annotation.primary_issue,
                    'notes': annotation.notes,
                    **sample.metadata
                }
                export_data.append(row)
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"rejected_{selected_issue}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.divider()
    
    # Metadata breakdown section
    st.subheader("Breakdown by Metadata")
    
    # Get all samples with annotations
    with db._get_connection() as conn:
        df_all = pd.read_sql_query("""
            SELECT s.metadata, a.is_acceptable
            FROM samples s
            JOIN annotations a ON s.id = a.sample_id
        """, conn)
    
    if df_all.empty:
        st.info("No annotated samples with metadata to analyze.")
        return
    
    # Parse metadata JSON with error handling
    def safe_json_loads(x):
        if not x or x.strip() == '':
            return {}
        try:
            return json.loads(x)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    try:
        metadata_records = df_all['metadata'].apply(safe_json_loads)
        
        # Check if any metadata exists
        if not any(metadata_records.apply(bool)):
            st.info("No metadata fields found in samples.")
            return
        
        # Convert to dataframe
        metadata_df = pd.DataFrame(metadata_records.tolist())
        metadata_df['is_acceptable'] = df_all['is_acceptable'].values
        
        # Show breakdown for each metadata field
        for col in metadata_df.columns:
            if col != 'is_acceptable' and metadata_df[col].notna().any():
                st.markdown(f"**Acceptance rate by {col}:**")
                
                # Group and calculate acceptance rates
                breakdown = metadata_df.groupby(col)['is_acceptable'].agg(['sum', 'count'])
                breakdown['acceptance_rate'] = (breakdown['sum'] / breakdown['count'] * 100).round(1)
                breakdown = breakdown.sort_values('count', ascending=False)
                
                # Display as metrics in columns
                n_values = len(breakdown)
                cols = st.columns(min(n_values, 4))
                
                for i, (idx, row) in enumerate(breakdown.iterrows()):
                    col_idx = i % len(cols)
                    cols[col_idx].metric(
                        str(idx),
                        f"{row['acceptance_rate']:.1f}%",
                        f"{int(row['count'])} samples"
                    )
                
                st.divider()
    
    except Exception as e:
        st.error(f"Error parsing metadata: {str(e)}")

