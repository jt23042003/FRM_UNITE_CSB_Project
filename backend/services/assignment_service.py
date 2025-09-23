from models.assignment import Assignment
from models import SessionLocal
from sqlalchemy.orm import Session
from typing import List, Optional

class AssignmentService:
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()

    def create_assignment(self, case_id: int, assigned_to: Optional[str], assigned_by: Optional[str]) -> Assignment:
        assignment = Assignment(
            case_id=case_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_assignments_by_case_id(self, case_id: int) -> List[Assignment]:
        return self.db.query(Assignment).filter(Assignment.case_id == case_id).all()

    def get_assignment_by_id(self, assignment_id: int) -> Optional[Assignment]:
        return self.db.query(Assignment).filter(Assignment.id == assignment_id).first()

    def update_assignment(self, assignment_id: int, **kwargs) -> Optional[Assignment]:
        assignment = self.get_assignment_by_id(assignment_id)
        if not assignment:
            return None
        for key, value in kwargs.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def delete_assignment(self, assignment_id: int) -> bool:
        assignment = self.get_assignment_by_id(assignment_id)
        if not assignment:
            return False
        self.db.delete(assignment)
        self.db.commit()
        return True