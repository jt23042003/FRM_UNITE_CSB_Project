from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import SessionLocal
from models.investigation_review_reason_list import InvestigationReviewReasonList
from models.final_closure_reason_list import FinalClosureReasonList
from sqlalchemy import text

router = APIRouter(prefix="/api", tags=["Reason Lists"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/investigation-review", response_model=list[dict])
def get_investigation_review_reasons(db: Session = Depends(get_db)):
    reasons = db.query(InvestigationReviewReasonList).all()
    return [
        {"reason": r.reason, "reason_description": r.reason_description}
        for r in reasons
    ]

@router.get("/final-closure", response_model=list[dict])
def get_final_closure_reasons(db: Session = Depends(get_db)):
    reasons = db.query(FinalClosureReasonList).all()
    return [
        {"reason": r.reason, "reason_description": r.reason_description}
        for r in reasons
    ]

@router.get("/send-back-analysis", response_model=list[dict])
def get_send_back_analysis_reasons(db: Session = Depends(get_db)):
    """
    Returns the list of send back reasons (id, reason, reason_description)
    from table public.send_back_analysis for Others (non-risk) users to select.
    """
    # Using text() for a simple table not mapped to ORM
    rows = db.execute(text("SELECT id, reason, reason_description FROM send_back_analysis ORDER BY id"))
    return [
        {
            "id": row[0],
            "reason": row[1],
            "reason_description": row[2]
        }
        for row in rows
    ]
