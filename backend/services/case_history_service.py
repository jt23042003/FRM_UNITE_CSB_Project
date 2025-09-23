from models.case_history import CaseHistory
from models import SessionLocal
from sqlalchemy.orm import Session
from typing import List, Optional

class CaseHistoryService:
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()

    def create_case_history(self, case_id: int, remarks: Optional[str], updated_by: Optional[str], file_path: Optional[str] = None, file_descr: Optional[str] = None) -> CaseHistory:
        case_history = CaseHistory(
            case_id=case_id,
            remarks=remarks,
            updated_by=updated_by,
            file_path=file_path,
            file_descr=file_descr
        )
        self.db.add(case_history)
        self.db.commit()
        self.db.refresh(case_history)
        return case_history

    def get_case_history_by_case_id(self, case_id: int) -> List[CaseHistory]:
        return self.db.query(CaseHistory).filter(CaseHistory.case_id == case_id).all()

    def get_case_history_by_id(self, history_id: int) -> Optional[CaseHistory]:
        return self.db.query(CaseHistory).filter(CaseHistory.id == history_id).first()

    def list_case_histories(self) -> List[CaseHistory]:
        return self.db.query(CaseHistory).all()

    def update_case_history(self, case_history_id: int, **kwargs) -> Optional[CaseHistory]:
        case_history = self.db.query(CaseHistory).filter(CaseHistory.id == case_history_id).first()
        if not case_history:
            return None
        for key, value in kwargs.items():
            if hasattr(case_history, key):
                setattr(case_history, key, value)
        self.db.commit()
        self.db.refresh(case_history)
        return case_history

    def delete_case_history(self, case_history_id: int) -> bool:
        case_history = self.db.query(CaseHistory).filter(CaseHistory.id == case_history_id).first()
        if not case_history:
            return False
        self.db.delete(case_history)
        self.db.commit()
        return True