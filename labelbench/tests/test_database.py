"""Unit tests for database operations."""

import pytest
import os
from storage.database import Database
from models.sample import Sample
from models.annotation import Annotation


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    db = Database(":memory:")
    yield db
    # No cleanup needed for in-memory database


def test_insert_and_retrieve_sample(test_db):
    """Test inserting and retrieving a sample."""
    sample = Sample(
        id="test_1",
        prompt="Test prompt",
        response="Test response",
        metadata={"model": "gpt-4"}
    )
    
    inserted = test_db.insert_samples([sample])
    assert inserted == 1
    
    retrieved = test_db.get_sample("test_1")
    assert retrieved is not None
    assert retrieved.prompt == "Test prompt"
    assert retrieved.metadata["model"] == "gpt-4"


def test_skip_duplicate_samples(test_db):
    """Test that duplicate sample IDs are skipped."""
    sample1 = Sample(id="dup_1", prompt="First", response="First response")
    sample2 = Sample(id="dup_1", prompt="Second", response="Second response")
    
    inserted = test_db.insert_samples([sample1, sample2])
    assert inserted == 1  # Only first should be inserted
    
    retrieved = test_db.get_sample("dup_1")
    assert retrieved.prompt == "First"  # First one wins


def test_get_unannotated_samples(test_db):
    """Test retrieving unannotated samples."""
    # Insert 3 samples
    samples = [
        Sample(id=f"s{i}", prompt=f"Prompt {i}", response=f"Response {i}")
        for i in range(3)
    ]
    test_db.insert_samples(samples)
    
    # Annotate only the first one
    annotation = Annotation(sample_id="s0", is_acceptable=True)
    test_db.insert_annotation(annotation)
    
    # Should get 2 unannotated
    unannotated = test_db.get_unannotated_samples()
    assert len(unannotated) == 2
    assert all(s.id in ["s1", "s2"] for s in unannotated)


def test_annotation_stats(test_db):
    """Test annotation statistics calculation."""
    # Insert samples
    samples = [Sample(id=f"s{i}", prompt="p", response="r") for i in range(10)]
    test_db.insert_samples(samples)
    
    # Annotate: 7 accepted, 3 rejected
    for i in range(7):
        test_db.insert_annotation(Annotation(sample_id=f"s{i}", is_acceptable=True))
    for i in range(7, 10):
        test_db.insert_annotation(Annotation(
            sample_id=f"s{i}",
            is_acceptable=False,
            primary_issue="hallucination"
        ))
    
    stats = test_db.get_annotation_stats()
    assert stats['total_annotated'] == 10
    assert stats['accepted'] == 7
    assert stats['rejected'] == 3
    assert stats['acceptance_rate'] == 70.0


def test_error_distribution(test_db):
    """Test error distribution aggregation."""
    # Insert samples
    samples = [Sample(id=f"s{i}", prompt="p", response="r") for i in range(5)]
    test_db.insert_samples(samples)
    
    # Create annotations with different issues
    issues = ["hallucination", "hallucination", "incomplete", "hallucination", "wrong_format"]
    for i, issue in enumerate(issues):
        test_db.insert_annotation(Annotation(
            sample_id=f"s{i}",
            is_acceptable=False,
            primary_issue=issue
        ))
    
    distribution = test_db.get_error_distribution()
    assert distribution["hallucination"] == 3
    assert distribution["incomplete"] == 1
    assert distribution["wrong_format"] == 1


def test_get_samples_by_issue(test_db):
    """Test filtering samples by issue type."""
    # Insert samples
    samples = [Sample(id=f"s{i}", prompt=f"Prompt {i}", response=f"Response {i}") 
               for i in range(3)]
    test_db.insert_samples(samples)
    
    # Annotate with different issues
    test_db.insert_annotation(Annotation(
        sample_id="s0",
        is_acceptable=False,
        primary_issue="hallucination",
        notes="Note 0"
    ))
    test_db.insert_annotation(Annotation(
        sample_id="s1",
        is_acceptable=False,
        primary_issue="hallucination",
        notes="Note 1"
    ))
    test_db.insert_annotation(Annotation(
        sample_id="s2",
        is_acceptable=False,
        primary_issue="incomplete"
    ))
    
    # Get only hallucinations
    results = test_db.get_samples_by_issue("hallucination")
    assert len(results) == 2
    
    # Verify structure
    sample, annotation = results[0]
    assert isinstance(sample, Sample)
    assert isinstance(annotation, Annotation)
    assert annotation.primary_issue == "hallucination"


