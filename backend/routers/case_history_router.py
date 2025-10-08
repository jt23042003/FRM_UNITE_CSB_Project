from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
from models.case_history import CaseHistory
from models import SessionLocal
from services.case_history_service import CaseHistoryService
from fastapi.responses import FileResponse

router = APIRouter(prefix="/case_history", tags=["case_history"])
UPLOAD_DIR = "/home/ubuntu/fraud_uploads"

def get_service():
    db = SessionLocal()
    try:
        yield CaseHistoryService(db)
    finally:
        db.close()

def serialize_case_history(case_history: CaseHistory) -> dict:
    return {
        "id": case_history.id,
        "case_id": case_history.case_id,
        "remarks": case_history.remarks,
        "updated_by": case_history.updated_by,
        "created_time": case_history.created_time.isoformat() if case_history.created_time else None,
        "file_path": case_history.file_path,
        "file_descr": case_history.file_descr,
    }

@router.post("/", response_model=dict)
async def create_case_history(
    case_id: int = Form(...),
    remarks: str = Form(...),
    updated_by: str = Form(...),
    file_descr: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    service: CaseHistoryService = Depends(get_service)
):
    file_path = None
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    created = service.create_case_history(
        case_id=case_id,
        remarks=remarks,
        updated_by=updated_by,
        file_path=file_path,
        file_descr=file_descr
    )
    return serialize_case_history(created)

@router.get("/case/{case_id}", response_model=List[dict])
def get_case_history_by_case_id(case_id: int, service: CaseHistoryService = Depends(get_service)):
    case_histories = service.get_case_history_by_case_id(case_id)
    return [serialize_case_history(ch) for ch in case_histories]

@router.get("/{history_id}", response_model=dict)
def get_case_history_by_id(history_id: int, service: CaseHistoryService = Depends(get_service)):
    case_history = service.get_case_history_by_id(history_id)
    if not case_history:
        raise HTTPException(status_code=404, detail="Case history not found")
    return serialize_case_history(case_history)

@router.get("/", response_model=List[dict])
def list_case_histories(service: CaseHistoryService = Depends(get_service)):
    case_histories = service.list_case_histories()
    return [serialize_case_history(ch) for ch in case_histories]

@router.put("/{case_history_id}", response_model=dict)
async def update_case_history(
    case_history_id: int,
    remarks: Optional[str] = Form(None),
    updated_by: Optional[str] = Form(None),
    file_descr: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    service: CaseHistoryService = Depends(get_service)
):
    file_path = None
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    update_data = {}
    if remarks is not None:
        update_data["remarks"] = remarks
    if updated_by is not None:
        update_data["updated_by"] = updated_by
    if file_descr is not None:
        update_data["file_descr"] = file_descr
    if file_path is not None:
        update_data["file_path"] = file_path
    updated = service.update_case_history(case_history_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Case history not found")
    return serialize_case_history(updated)

@router.delete("/{case_history_id}", response_model=dict)
def delete_case_history(case_history_id: int, service: CaseHistoryService = Depends(get_service)):
    success = service.delete_case_history(case_history_id)
    if not success:
        raise HTTPException(status_code=404, detail="Case history not found")
    return {"deleted": True}

@router.get("/download/{history_id}")
def download_case_history_file(history_id: int, service: CaseHistoryService = Depends(get_service)):
    case_history = service.get_case_history_by_id(history_id)
    if not case_history or not case_history.file_path:
        raise HTTPException(status_code=404, detail="File not found for this case history")
    file_path = case_history.file_path
    file_name = os.path.basename(file_path)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(path=file_path, filename=file_name)