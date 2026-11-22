"""Pydantic schema for the ClinixAI knowledge base."""

from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    title: str
    publisher: str
    url: str
    year: int


class SymptomWeight(BaseModel):
    symptom_id: str
    weight: float = Field(ge=0.0, le=1.0)
    specificity: str | None = None


class RedFlag(BaseModel):
    id: str
    description: str
    required_symptom_ids: list[str]
    urgency: str
    minimum_severity: int | None = Field(default=None, ge=1, le=10)


class Disease(BaseModel):
    id: str
    name: str
    description: str
    prior_probability: float
    severity: Literal["low", "moderate", "high", "critical"]
    symptoms: list[SymptomWeight]
    risk_factors: list[str]
    next_step: Literal["self_care", "see_clinician", "urgent_care", "emergency"]
    advice: str
    source_ids: list[str]
    illustrative: bool


class Symptom(BaseModel):
    id: str
    display_name: str
    question: str
    synonyms: list[str] | None = None


class KnowledgeBase(BaseModel):
    version: str
    symptoms: list[Symptom]
    diseases: list[Disease]
    red_flags: list[RedFlag]
    sources: list[Source]
