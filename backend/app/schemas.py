
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    target_role: str = Field(..., min_length=2, max_length=150)
    current_skills: list[str] = Field(..., min_length=1)


class UserProfileResponse(BaseModel):
    id: int
    name: str
    target_role: str
    current_skills: list[str]


class LearningProgressUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]
    notes: str = Field(default="", max_length=1000)


class MarketSkillObservationCreate(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=150)
    skill: str = Field(..., min_length=1, max_length=150)
    posting_count: int = Field(..., ge=0)
    total_postings: int = Field(..., gt=0)
    source: str = Field(..., min_length=2, max_length=200)

    @model_validator(mode="after")
    def validate_posting_counts(self):
        if self.posting_count > self.total_postings:
            raise ValueError(
                "posting_count cannot exceed total_postings"
            )
        return self
