from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from models.assignment import Assignment
from models import SessionLocal
from services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["assignments"])

def get_service():
    db = SessionLocal()
    try:
        yield AssignmentService(db)
    finally:
        db.close()

def serialize_assignment(assignment: Assignment) -> dict:
    """Convert SQLAlchemy Assignment object to serializable dict"""
    return {
        "id": assignment.id,
        "case_id": assignment.case_id,
        "assigned_to": assignment.assigned_to,
        "assigned_by": assignment.assigned_by,
        "assign_date": assignment.assign_date.isoformat() if assignment.assign_date else None,
        "assign_time": assignment.assign_time.isoformat() if assignment.assign_time else None
    }

@router.post("/", response_model=dict)
def create_assignment(assignment: dict, service: AssignmentService = Depends(get_service)):
    created = service.create_assignment(**assignment)
    return {"id": created.id}

@router.get("/case/{case_id}", response_model=List[dict])
def get_assignments_by_case_id(case_id: int, service: AssignmentService = Depends(get_service)):
    assignments = service.get_assignments_by_case_id(case_id)
    return [serialize_assignment(a) for a in assignments]

@router.get("/{assignment_id}", response_model=dict)
def get_assignment(assignment_id: int, service: AssignmentService = Depends(get_service)):
    assignment = service.get_assignment_by_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return serialize_assignment(assignment)

@router.put("/{assignment_id}", response_model=dict)
def update_assignment(assignment_id: int, updates: dict, service: AssignmentService = Depends(get_service)):
    updated = service.update_assignment(assignment_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return serialize_assignment(updated)

@router.delete("/{assignment_id}", response_model=dict)
def delete_assignment(assignment_id: int, service: AssignmentService = Depends(get_service)):
    success = service.delete_assignment(assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"deleted": True}