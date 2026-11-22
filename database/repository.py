"""Repository layer: the only place the rest of the app touches the database.

The service layer / UI should call these functions and never use ORM models directly
for queries. Functions return plain dicts so callers don't depend on SQLAlchemy.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import delete, func, select

from database.db import get_session
from database.models import AssessmentSession, Feedback, Result, SymptomInput


# ---------- helpers ----------
def _session_to_dict(s: AssessmentSession) -> dict[str, Any]:
    return {
        "id": s.id,
        "created_at": s.created_at,
        "age_group": s.age_group,
        "sex": s.sex,
        "kb_version": s.kb_version,
        "model_version": s.model_version,
        "red_flag_triggered": s.red_flag_triggered,
        "symptoms": [
            {
                "symptom_id": x.symptom_id,
                "present": x.present,
                "severity": x.severity,
                "duration_days": x.duration_days,
            }
            for x in s.symptoms
        ],
        "results": [
            {
                "rank": r.rank,
                "disease_id": r.disease_id,
                "disease_name": r.disease_name,
                "expert_score": r.expert_score,
                "math_score": r.math_score,
                "ml_score": r.ml_score,
                "final_score": r.final_score,
                "confidence": r.confidence,
                "explanation": r.explanation,
                "advice": r.advice,
            }
            for r in s.results
        ],
    }


# ---------- create ----------
def create_session(
    age_group: Optional[str] = None,
    sex: Optional[str] = None,
    kb_version: Optional[str] = None,
    model_version: Optional[str] = None,
) -> str:
    """Start a new anonymous assessment session and return its id."""
    with get_session() as db:
        s = AssessmentSession(
            age_group=age_group, sex=sex, kb_version=kb_version, model_version=model_version
        )
        db.add(s)
        db.flush()
        return s.id


def save_symptoms(session_id: str, symptoms: list[dict[str, Any]]) -> None:
    """Replace the stored symptoms for a session.

    Each item: {"symptom_id": str, "present": bool|None, "severity": int|None,
                "duration_days": int|None}
    """
    with get_session() as db:
        _require_session(db, session_id)
        db.execute(delete(SymptomInput).where(SymptomInput.session_id == session_id))
        for item in symptoms:
            sev = item.get("severity")
            if sev is not None and not 1 <= sev <= 10:
                raise ValueError(f"severity must be 1-10, got {sev}")
            db.add(
                SymptomInput(
                    session_id=session_id,
                    symptom_id=item["symptom_id"],
                    present=item.get("present"),
                    severity=sev,
                    duration_days=item.get("duration_days"),
                )
            )


def save_results(
    session_id: str, results: list[dict[str, Any]], red_flag_triggered: bool = False
) -> None:
    """Replace the stored ranked results for a session.

    Each item needs: disease_id, disease_name, final_score. Optional: expert_score,
    math_score, ml_score, confidence, explanation (dict), advice. Rank is assigned
    from the list order (first item = rank 1).
    """
    with get_session() as db:
        s = _require_session(db, session_id)
        s.red_flag_triggered = red_flag_triggered
        db.execute(delete(Result).where(Result.session_id == session_id))
        for rank, item in enumerate(results, start=1):
            db.add(
                Result(
                    session_id=session_id,
                    rank=rank,
                    disease_id=item["disease_id"],
                    disease_name=item["disease_name"],
                    expert_score=item.get("expert_score"),
                    math_score=item.get("math_score"),
                    ml_score=item.get("ml_score"),
                    final_score=item["final_score"],
                    confidence=item.get("confidence"),
                    explanation=item.get("explanation"),
                    advice=item.get("advice"),
                )
            )


def add_feedback(session_id: str, rating: int, comment: Optional[str] = None) -> None:
    if not 1 <= rating <= 5:
        raise ValueError("rating must be between 1 and 5")
    with get_session() as db:
        _require_session(db, session_id)
        db.add(Feedback(session_id=session_id, rating=rating, comment=comment))


# ---------- read ----------
def get_session_data(session_id: str) -> Optional[dict[str, Any]]:
    with get_session() as db:
        s = db.get(AssessmentSession, session_id)
        return _session_to_dict(s) if s else None


def list_sessions(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Newest first. Used by the History page."""
    with get_session() as db:
        rows = db.scalars(
            select(AssessmentSession)
            .order_by(AssessmentSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return [_session_to_dict(s) for s in rows]


def get_stats() -> dict[str, Any]:
    """Aggregate numbers for the dashboard Insights page."""
    with get_session() as db:
        total = db.scalar(select(func.count(AssessmentSession.id))) or 0
        red_flags = (
            db.scalar(
                select(func.count(AssessmentSession.id)).where(
                    AssessmentSession.red_flag_triggered.is_(True)
                )
            )
            or 0
        )
        avg_rating = db.scalar(select(func.avg(Feedback.rating)))
        top = db.execute(
            select(Result.disease_name, func.count(Result.id).label("n"))
            .where(Result.rank == 1)
            .group_by(Result.disease_name)
            .order_by(func.count(Result.id).desc())
            .limit(10)
        ).all()
        return {
            "total_sessions": total,
            "red_flag_sessions": red_flags,
            "average_rating": float(avg_rating) if avg_rating is not None else None,
            "top_conditions": [{"disease_name": n, "count": c} for n, c in top],
        }


# ---------- delete ----------
def delete_session(session_id: str) -> bool:
    """Delete a session and everything attached to it (privacy: right to delete)."""
    with get_session() as db:
        s = db.get(AssessmentSession, session_id)
        if s is None:
            return False
        db.delete(s)
        return True


def delete_all_data() -> None:
    with get_session() as db:
        db.execute(delete(AssessmentSession))


# ---------- internal ----------
def _require_session(db, session_id: str) -> AssessmentSession:
    s = db.get(AssessmentSession, session_id)
    if s is None:
        raise LookupError(f"Session {session_id} not found")
    return s