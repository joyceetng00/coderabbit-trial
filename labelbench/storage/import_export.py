"""Import and export utilities for CSV/JSON data."""

import pandas as pd
import json
import re
from typing import List
from pathlib import Path

from models.sample import Sample


def import_csv(file_path: str) -> List[Sample]:
    """Import samples from CSV file.
    
    Expected columns: id, prompt, response
    Optional columns: Any additional columns treated as metadata
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of Sample objects
        
    Raises:
        ValueError: If required columns are missing
        FileNotFoundError: If file doesn't exist
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Validate required columns
    required = ['id', 'prompt', 'response']
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Convert to Sample objects with validation
    samples = []
    for idx, row in df.iterrows():
        # Validate required fields are not empty
        sample_id = str(row['id']).strip()
        if not sample_id:
            raise ValueError(f"Row {idx + 1}: 'id' cannot be empty")
        
        prompt = str(row['prompt']).strip()
        if not prompt:
            raise ValueError(f"Row {idx + 1}: 'prompt' cannot be empty")
        
        response = str(row['response']).strip()
        if not response:
            raise ValueError(f"Row {idx + 1}: 'response' cannot be empty")
        
        # Validate ID format (no SQL injection risks or special characters)
        if not re.match(r'^[a-zA-Z0-9_-]+$', sample_id):
            raise ValueError(f"Row {idx + 1}: 'id' contains invalid characters. Only letters, numbers, underscores, and hyphens allowed.")
        
        # Truncate extremely long text (prevent UI crashes)
        if len(prompt) > 10000:
            prompt = prompt[:10000]
        if len(response) > 50000:
            response = response[:50000]
        
        # Separate required fields from metadata
        metadata = {}
        for col in df.columns:
            if col not in required and pd.notna(row[col]):
                metadata[col] = row[col]
        
        sample = Sample(
            id=sample_id,
            prompt=prompt,
            response=response,
            metadata=metadata
        )
        samples.append(sample)
    
    return samples


def import_json(file_path: str) -> List[Sample]:
    """Import samples from JSON file.
    
    Expected format:
    {
        "samples": [
            {
                "id": "...",
                "prompt": "...",
                "response": "...",
                "metadata": {...}  # optional
            }
        ]
    }
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of Sample objects
        
    Raises:
        ValueError: If JSON structure is invalid
        FileNotFoundError: If file doesn't exist
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'samples' not in data:
        raise ValueError("JSON must contain 'samples' key with array of sample objects")
    
    samples = []
    for i, item in enumerate(data['samples']):
        # Validate required fields exist
        if 'id' not in item:
            raise ValueError(f"Sample at index {i} missing 'id' field")
        if 'prompt' not in item:
            raise ValueError(f"Sample at index {i} missing 'prompt' field")
        if 'response' not in item:
            raise ValueError(f"Sample at index {i} missing 'response' field")
        
        # Validate required fields are not empty
        sample_id = str(item['id']).strip()
        if not sample_id:
            raise ValueError(f"Sample at index {i}: 'id' cannot be empty")
        
        prompt = str(item['prompt']).strip()
        if not prompt:
            raise ValueError(f"Sample at index {i}: 'prompt' cannot be empty")
        
        response = str(item['response']).strip()
        if not response:
            raise ValueError(f"Sample at index {i}: 'response' cannot be empty")
        
        # Validate ID format
        if not re.match(r'^[a-zA-Z0-9_-]+$', sample_id):
            raise ValueError(f"Sample at index {i}: 'id' contains invalid characters. Only letters, numbers, underscores, and hyphens allowed.")
        
        # Truncate extremely long text (prevent UI crashes)
        if len(prompt) > 10000:
            prompt = prompt[:10000]
        if len(response) > 50000:
            response = response[:50000]
        
        sample = Sample(
            id=sample_id,
            prompt=prompt,
            response=response,
            metadata=item.get('metadata', {})
        )
        samples.append(sample)
    
    return samples


def export_rejected_csv(db, output_path: str) -> int:
    """Export all rejected samples with annotations to CSV.
    
    Args:
        db: Database instance
        output_path: Path for output CSV file
        
    Returns:
        Number of samples exported
    """
    with db._get_connection() as conn:
        df = pd.read_sql_query("""
            SELECT 
                s.id,
                s.prompt,
                s.response,
                s.metadata,
                a.primary_issue,
                a.notes,
                a.annotated_at
            FROM samples s
            JOIN annotations a ON s.id = a.sample_id
            WHERE a.is_acceptable = 0
            ORDER BY a.annotated_at DESC
        """, conn)
    
    if df.empty:
        # Create empty file
        df.to_csv(output_path, index=False)
        return 0
    
    # Parse metadata into separate columns with error handling
    def safe_json_loads(x):
        if not x or x.strip() == '':
            return {}
        try:
            return json.loads(x)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    metadata_df = df['metadata'].apply(safe_json_loads).apply(pd.Series)
    
    # Combine with main dataframe
    df = pd.concat([
        df.drop('metadata', axis=1),
        metadata_df
    ], axis=1)
    
    df.to_csv(output_path, index=False)
    return len(df)


def export_all_annotations_json(db, output_path: str) -> int:
    """Export all samples with annotations to JSON.
    
    Args:
        db: Database instance
        output_path: Path for output JSON file
        
    Returns:
        Number of samples exported
    """
    with db._get_connection() as conn:
        df = pd.read_sql_query("""
            SELECT 
                s.id,
                s.prompt,
                s.response,
                s.metadata,
                a.is_acceptable,
                a.primary_issue,
                a.notes,
                a.annotated_at
            FROM samples s
            JOIN annotations a ON s.id = a.sample_id
            ORDER BY s.id
        """, conn)
    
    if df.empty:
        with open(output_path, 'w') as f:
            json.dump({"samples": []}, f, indent=2)
        return 0
    
    # Convert to list of dictionaries
    samples = []
    for _, row in df.iterrows():
        sample = {
            "id": row['id'],
            "prompt": row['prompt'],
            "response": row['response'],
            "metadata": json.loads(row['metadata']) if row['metadata'] else {},
            "annotation": {
                "is_acceptable": bool(row['is_acceptable']),
                "primary_issue": row['primary_issue'],
                "notes": row['notes'],
                "annotated_at": str(row['annotated_at'])
            }
        }
        samples.append(sample)
    
    with open(output_path, 'w') as f:
        json.dump({"samples": samples}, f, indent=2)
    
    return len(samples)

