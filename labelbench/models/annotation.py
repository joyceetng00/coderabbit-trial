"""Annotation data model for human feedback."""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Literal
import uuid


class Annotation(BaseModel):
    """Represents human feedback on a sample.
    
    Attributes:
        id: Unique identifier for the annotation
        sample_id: Foreign key reference to the Sample being annotated
        annotator_id: Identifier for the person annotating (default for single-user)
        is_acceptable: Binary quality decision (True = Accept, False = Reject)
        primary_issue: Main reason for rejection (only set if is_acceptable=False)
        notes: Free-form text explanation or additional context
        annotated_at: Timestamp when annotation was created
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sample_id: str = Field(..., description="Foreign key to Sample")
    annotator_id: str = Field(
        default="default",
        description="For future multi-annotator support"
    )
    
    # Core judgment
    is_acceptable: bool = Field(..., description="Binary quality decision")
    
    # Structured feedback (only required if rejected)
    primary_issue: Optional[Literal[
        "hallucination",
        "factually_incorrect",
        "incomplete",
        "wrong_format",
        "off_topic",
        "inappropriate_tone",
        "refusal",
        "other"
    ]] = Field(None, description="Main reason for rejection")
    
    # Free-form notes
    notes: Optional[str] = Field(None, description="Detailed explanation")
    
    # Metadata
    annotated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": "sample_001",
                "is_acceptable": False,
                "primary_issue": "hallucination",
                "notes": "The response claims free shipping to Alaska, but we charge $15."
            }
        }

