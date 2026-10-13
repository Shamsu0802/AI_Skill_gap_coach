
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    target_role = Column(String(150), nullable=False)
    current_skills = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

    roadmaps = relationship(
        "LearningRoadmap",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    title = Column(String(200), nullable=False)
    roadmap_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "UserProfile",
        back_populates="roadmaps"
    )

    progress_items = relationship(
        "LearningProgress",
        back_populates="roadmap",
        cascade="all, delete-orphan"
    )


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(
        Integer,
        ForeignKey("learning_roadmaps.id"),
        nullable=False
    )
    week = Column(Integer, nullable=False)
    skill = Column(String(150), nullable=False)
    status = Column(
        String(30),
        nullable=False,
        default="not_started"
    )
    notes = Column(Text, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    roadmap = relationship(
        "LearningRoadmap",
        back_populates="progress_items"
    )


class MarketSkillObservation(Base):
    __tablename__ = "market_skill_observations"

    id = Column(Integer, primary_key=True, index=True)

    target_role = Column(String(150), nullable=False, index=True)
    skill = Column(String(150), nullable=False, index=True)

    # Number of job postings in which this skill was observed
    posting_count = Column(Integer, nullable=False, default=1)

    # Total job postings examined in this observation batch
    total_postings = Column(Integer, nullable=False, default=1)

    # Percentage of examined postings mentioning this skill
    demand_percentage = Column(Float, nullable=False, default=0.0)

    # Source of the observation, such as a dataset or job board
    source = Column(String(200), nullable=False)

    observed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
