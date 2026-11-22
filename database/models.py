"""SQLAlchemy ORM models for ClinixAI.

All data is anonymous: no names, emails, or other patient identifiers are stored.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class AssessmentSession(Base):
    """One user assessment from start to finish."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    age_group: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g. "18-29"
    sex: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    kb_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    red_flag_triggered: Mapped[bool] = mapped_column(Boolean, default=False)

    symptoms: Mapped[list["SymptomInput"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    results: Mapped[list["Result"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Result.rank"
    )
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SymptomInput(Base):
    """A single symptom answer given during a session."""

    __tablename__ = "symptom_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    symptom_id: Mapped[str] = mapped_column(String(64))
    present: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # None = unknown
    severity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    session: Mapped[AssessmentSession] = relationship(back_populates="symptoms")


class Result(Base):
    """One ranked condition produced for a session."""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    disease_id: Mapped[str] = mapped_column(String(64))
    disease_name: Mapped[str] = mapped_column(String(128))
    expert_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    math_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    explanation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # rules fired, weights
    advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    session: Mapped[AssessmentSession] = relationship(back_populates="results")


class Feedback(Base):
    """Optional user feedback on a session's results."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[AssessmentSession] = relationship(back_populates="feedback")