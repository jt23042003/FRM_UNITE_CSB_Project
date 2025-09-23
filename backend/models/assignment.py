from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Time,
    ForeignKey,
    func,
    Text,
    Boolean
)
from typing import List, Optional
from . import Base

class Assignment(Base):
    __tablename__ = "assignment"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case_main.case_id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(String(50))
    assigned_by = Column(String(50))
    assign_date = Column(Date, server_default=func.current_date())
    assign_time = Column(Time, server_default=func.current_time())
    comment = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    assignment_type = Column(String(50), default='manual')
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)  # New field for template assignment

# CRUD operations

def create_assignment(db_session, case_id: int, assigned_to: Optional[str], assigned_by: Optional[str], 
                     comment: Optional[str] = None, template_id: Optional[int] = None) -> Assignment:
    assignment = Assignment(
        case_id=case_id,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
        comment=comment,
        template_id=template_id
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

def get_assignments_by_case_id(db_session, case_id: int) -> List[Assignment]:
    return db_session.query(Assignment).filter(Assignment.case_id == case_id).all()

def update_assignment(db_session, assignment_id: int, **kwargs) -> Optional[Assignment]:
    assignment = db_session.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return None
    for key, value in kwargs.items():
        if hasattr(assignment, key):
            setattr(assignment, key, value)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

def delete_assignment(db_session, assignment_id: int) -> bool:
    assignment = db_session.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return False
    db_session.delete(assignment)
    db_session.commit()
    return True

# Example usage (remove or comment out in production)
if __name__ == "__main__":
    from . import create_tables
    create_tables() 