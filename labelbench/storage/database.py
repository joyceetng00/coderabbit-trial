"""Database operations for LabelBench using SQLite."""

import sqlite3
import json
import logging
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from models.sample import Sample
from models.annotation import Annotation

logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for samples and annotations.
    
    This class provides CRUD operations for storing and retrieving
    prompt-response samples and their annotations.
    """
    
    def __init__(self, db_path: str = "labelbench.db"):
        """Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with automatic transaction management.
        
        Yields:
            SQLite connection object
            
        Usage:
            with self._get_connection() as conn:
                conn.execute(...)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _parse_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Safely parse metadata JSON string.
        
        Args:
            metadata_str: JSON string or None
            
        Returns:
            Parsed metadata dictionary, empty dict if invalid or empty
        """
        if not metadata_str or metadata_str.strip() == '':
            return {}
        try:
            return json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Invalid metadata JSON: {metadata_str[:100] if metadata_str else 'None'}... Error: {e}")
            return {}
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            # Create samples table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    metadata TEXT,
                    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_samples_imported 
                ON samples(imported_at)
            """)
            
            # Create annotations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    sample_id TEXT NOT NULL,
                    annotator_id TEXT DEFAULT 'default',
                    is_acceptable BOOLEAN NOT NULL,
                    primary_issue TEXT,
                    notes TEXT,
                    annotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sample_id) REFERENCES samples(id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_sample 
                ON annotations(sample_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_acceptable 
                ON annotations(is_acceptable)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_issue 
                ON annotations(primary_issue)
            """)
    
    def insert_samples(self, samples: List[Sample]) -> int:
        """Insert samples into database, skipping duplicates.
        
        Args:
            samples: List of Sample objects to insert
            
        Returns:
            Number of samples successfully inserted
        """
        inserted = 0
        with self._get_connection() as conn:
            for sample in samples:
                try:
                    conn.execute(
                        """INSERT INTO samples (id, prompt, response, metadata, imported_at) 
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            sample.id,
                            sample.prompt,
                            sample.response,
                            json.dumps(sample.metadata),
                            sample.imported_at
                        )
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    # Skip duplicate IDs
                    continue
        return inserted
    
    def get_sample(self, sample_id: str) -> Optional[Sample]:
        """Retrieve a single sample by ID.
        
        Args:
            sample_id: Unique identifier of the sample
            
        Returns:
            Sample object if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM samples WHERE id = ?",
                (sample_id,)
            )
            row = cursor.fetchone()
        
        if row:
            return Sample(
                id=row['id'],
                prompt=row['prompt'],
                response=row['response'],
                metadata=self._parse_metadata(row['metadata']),
                imported_at=row['imported_at']
            )
        return None
    
    def get_all_samples(self) -> List[Sample]:
        """Retrieve all samples from database.
        
        Returns:
            List of all Sample objects
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM samples ORDER BY imported_at")
            rows = cursor.fetchall()
        
        return [
            Sample(
                id=row['id'],
                prompt=row['prompt'],
                response=row['response'],
                metadata=self._parse_metadata(row['metadata']),
                imported_at=row['imported_at']
            )
            for row in rows
        ]
    
    def get_unannotated_samples(self) -> List[Sample]:
        """Get samples that haven't been annotated yet.
        
        Returns:
            List of Sample objects without annotations
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.* FROM samples s
                LEFT JOIN annotations a ON s.id = a.sample_id
                WHERE a.id IS NULL
                ORDER BY s.imported_at
            """)
            rows = cursor.fetchall()
        
        return [
            Sample(
                id=row['id'],
                prompt=row['prompt'],
                response=row['response'],
                metadata=self._parse_metadata(row['metadata']),
                imported_at=row['imported_at']
            )
            for row in rows
        ]
    
    def insert_annotation(self, annotation: Annotation):
        """Save an annotation to the database.
        
        Args:
            annotation: Annotation object to save
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO annotations 
                (id, sample_id, annotator_id, is_acceptable, primary_issue, notes, annotated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                annotation.id,
                annotation.sample_id,
                annotation.annotator_id,
                annotation.is_acceptable,
                annotation.primary_issue,
                annotation.notes,
                annotation.annotated_at
            ))
    
    def get_annotation(self, sample_id: str) -> Optional[Annotation]:
        """Get annotation for a specific sample.
        
        Args:
            sample_id: ID of the sample
            
        Returns:
            Annotation object if exists, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM annotations WHERE sample_id = ?",
                (sample_id,)
            )
            row = cursor.fetchone()
        
        if row:
            return Annotation(
                id=row['id'],
                sample_id=row['sample_id'],
                annotator_id=row['annotator_id'],
                is_acceptable=bool(row['is_acceptable']),
                primary_issue=row['primary_issue'],
                notes=row['notes'],
                annotated_at=row['annotated_at']
            )
        return None
    
    def get_annotation_stats(self) -> Dict[str, Any]:
        """Get summary statistics about annotations.
        
        Returns:
            Dictionary with keys: total_annotated, accepted, rejected, acceptance_rate
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_annotated,
                    SUM(CASE WHEN is_acceptable = 1 THEN 1 ELSE 0 END) as accepted,
                    SUM(CASE WHEN is_acceptable = 0 THEN 1 ELSE 0 END) as rejected
                FROM annotations
            """)
            row = cursor.fetchone()
        
        total = row['total_annotated'] or 0
        accepted = row['accepted'] or 0
        rejected = row['rejected'] or 0
        
        return {
            "total_annotated": total,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": (accepted / total * 100) if total > 0 else 0
        }
    
    def get_error_distribution(self) -> Dict[str, int]:
        """Get count of each error type.
        
        Returns:
            Dictionary mapping primary_issue to count
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT primary_issue, COUNT(*) as count
                FROM annotations
                WHERE is_acceptable = 0 AND primary_issue IS NOT NULL
                GROUP BY primary_issue
                ORDER BY count DESC
            """)
            rows = cursor.fetchall()
        
        return {row['primary_issue']: row['count'] for row in rows}
    
    def get_samples_by_issue(self, issue_type: str) -> List[Tuple[Sample, Annotation]]:
        """Get all samples with a specific issue type.
        
        Args:
            issue_type: The primary_issue value to filter by
            
        Returns:
            List of (Sample, Annotation) tuples
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    s.id, s.prompt, s.response, s.metadata, s.imported_at,
                    a.id as ann_id, a.sample_id, a.annotator_id, a.is_acceptable,
                    a.primary_issue, a.notes, a.annotated_at
                FROM samples s
                JOIN annotations a ON s.id = a.sample_id
                WHERE a.primary_issue = ?
                ORDER BY a.annotated_at DESC
            """, (issue_type,))
            rows = cursor.fetchall()
        
        results = []
        for row in rows:
            sample = Sample(
                id=row['id'],
                prompt=row['prompt'],
                response=row['response'],
                metadata=self._parse_metadata(row['metadata']),
                imported_at=row['imported_at']
            )
            annotation = Annotation(
                id=row['ann_id'],
                sample_id=row['sample_id'],
                annotator_id=row['annotator_id'],
                is_acceptable=bool(row['is_acceptable']),
                primary_issue=row['primary_issue'],
                notes=row['notes'],
                annotated_at=row['annotated_at']
            )
            results.append((sample, annotation))
        
        return results
    
    def get_total_samples(self) -> int:
        """
        Return the total number of samples stored in the database.
        
        Returns:
            int: Total number of samples.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM samples")
            row = cursor.fetchone()
        return row['count']
    
    def clear_all_data(self) -> Dict[str, int]:
        """
        Permanently remove all samples and annotations from the database.
        
        Counts records before deletion and deletes all rows from annotations and samples (respecting foreign-key cascade), returning the pre-deletion counts.
        
        Returns:
            result (Dict[str, int]): Dictionary with keys 'samples_deleted' and 'annotations_deleted' containing the number of samples and annotations removed.
        """
        with self._get_connection() as conn:
            # Get counts before deletion for reporting
            cursor = conn.execute("SELECT COUNT(*) as count FROM annotations")
            annotations_count = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM samples")
            samples_count = cursor.fetchone()['count']
            
            # Delete all annotations first (due to foreign key constraint)
            conn.execute("DELETE FROM annotations")
            
            # Delete all samples (cascade will handle any remaining annotations)
            conn.execute("DELETE FROM samples")
        
        return {
            'samples_deleted': samples_count,
            'annotations_deleted': annotations_count
        }
