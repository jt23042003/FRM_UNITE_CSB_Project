from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    func,
    Boolean
)
from typing import List, Optional, Dict, Any
from . import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(JSON, nullable=False)  # Store questions as JSON for flexibility
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class TemplateResponse(Base):
    __tablename__ = "template_responses"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case_main.case_id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(String(50), nullable=False)  # User who filled the template
    responses = Column(JSON, nullable=False)  # Store responses as JSON
    status = Column(String(50), default="pending_approval")  # pending_approval, approved, rejected
    department = Column(String(100), nullable=True)  # Department for approval workflow
    approved_by = Column(String(50), nullable=True)  # Supervisor who approved/rejected
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

# CRUD operations for Template
def create_template(db_session, name: str, description: Optional[str], questions: List[Dict[str, Any]]) -> Template:
    template = Template(
        name=name,
        description=description,
        questions=questions
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template

def get_all_active_templates(db_session) -> List[Template]:
    return db_session.query(Template).filter(Template.is_active == True).all()

def get_template_by_id(db_session, template_id: int) -> Optional[Template]:
    return db_session.query(Template).filter(Template.id == template_id).first()

# CRUD operations for TemplateResponse
def create_template_response(db_session, case_id: int, template_id: int, assigned_to: str, 
                           responses: Dict[str, Any], department: Optional[str] = None) -> TemplateResponse:
    template_response = TemplateResponse(
        case_id=case_id,
        template_id=template_id,
        assigned_to=assigned_to,
        responses=responses,
        department=department
    )
    db_session.add(template_response)
    db_session.commit()
    db_session.refresh(template_response)
    return template_response

def get_template_responses_by_case(db_session, case_id: int) -> List[TemplateResponse]:
    return db_session.query(TemplateResponse).filter(TemplateResponse.case_id == case_id).all()

def get_template_response_by_id(db_session, response_id: int) -> Optional[TemplateResponse]:
    return db_session.query(TemplateResponse).filter(TemplateResponse.id == response_id).first()

def update_template_response_status(db_session, response_id: int, status: str, 
                                 approved_by: Optional[str] = None, 
                                 rejection_reason: Optional[str] = None) -> Optional[TemplateResponse]:
    template_response = get_template_response_by_id(db_session, response_id)
    if not template_response:
        return None
    
    template_response.status = status
    if approved_by:
        template_response.approved_by = approved_by
        template_response.approved_at = func.current_timestamp()
    if rejection_reason:
        template_response.rejection_reason = rejection_reason
    
    db_session.commit()
    db_session.refresh(template_response)
    return template_response
