from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    func,
    TIMESTAMP
)

from typing import List, Optional
from . import Base

class CaseHistory(Base):
    __tablename__ = "case_history"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case_main.case_id", ondelete="CASCADE"), nullable=False)
    remarks = Column(Text)
    updated_by = Column(String(50))
    created_time = Column(TIMESTAMP, server_default=func.now())
    file_path = Column(Text)
    file_descr = Column(String(255))

# CRUD operations

def create_case_history(db_session, case_id: int, remarks: Optional[str], updated_by: Optional[str]) -> CaseHistory:
    case_history = CaseHistory(
        case_id=case_id,
        remarks=remarks,
        updated_by=updated_by
    )
    db_session.add(case_history)
    db_session.commit()
    db_session.refresh(case_history)
    return case_history

def get_case_history_by_case_id(db_session, case_id: int) -> List[CaseHistory]:
    return db_session.query(CaseHistory).filter(CaseHistory.case_id == case_id).all()

def update_case_history(db_session, history_id: int, **kwargs) -> Optional[CaseHistory]:
    case_history = db_session.query(CaseHistory).filter(CaseHistory.id == history_id).first()
    if not case_history:
        return None
    for key, value in kwargs.items():
        if hasattr(case_history, key):
            setattr(case_history, key, value)
    db_session.commit()
    db_session.refresh(case_history)
    return case_history

def delete_case_history(db_session, history_id: int) -> bool:
    case_history = db_session.query(CaseHistory).filter(CaseHistory.id == history_id).first()
    if not case_history:
        return False
    db_session.delete(case_history)
    db_session.commit()
    return True

if __name__ == "__main__":
    from . import create_tables
    create_tables()