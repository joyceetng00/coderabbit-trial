"""Unit tests for data models."""

import pytest
from models.sample import Sample
from models.annotation import Annotation


def test_sample_creation():
    """Test creating a Sample with required fields."""
    sample = Sample(
        id="test_1",
        prompt="What is 2+2?",
        response="4",
        metadata={"model": "gpt-4"}
    )
    
    assert sample.id == "test_1"
    assert sample.prompt == "What is 2+2?"
    assert sample.metadata["model"] == "gpt-4"


def test_sample_without_metadata():
    """Test creating a Sample without metadata."""
    sample = Sample(
        id="test_2",
        prompt="Test prompt",
        response="Test response"
    )
    
    assert sample.metadata == {}


def test_annotation_accepted():
    """Test creating an accepted annotation."""
    annotation = Annotation(
        sample_id="test_1",
        is_acceptable=True
    )
    
    assert annotation.is_acceptable is True
    assert annotation.primary_issue is None
    assert annotation.notes is None


def test_annotation_rejected():
    """Test creating a rejected annotation with feedback."""
    annotation = Annotation(
        sample_id="test_1",
        is_acceptable=False,
        primary_issue="hallucination",
        notes="Incorrect information provided"
    )
    
    assert annotation.is_acceptable is False
    assert annotation.primary_issue == "hallucination"
    assert annotation.notes == "Incorrect information provided"


def test_annotation_auto_id():
    """Test that annotations get auto-generated IDs."""
    ann1 = Annotation(sample_id="test_1", is_acceptable=True)
    ann2 = Annotation(sample_id="test_1", is_acceptable=True)
    
    assert ann1.id != ann2.id
    assert len(ann1.id) == 36  # UUID4 format

