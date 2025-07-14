# routers/case_entry.py
from fastapi import APIRouter, HTTPException, Depends, Request, Form, File, UploadFile, status # Added status for HTTP status codes
from typing import Annotated, Optional, Dict, List, Union
from datetime import date
from fastapi.exceptions import RequestValidationError # Import RequestValidationError
# pydantic.ValidationError not needed if RequestValidationError catches it
import psycopg2 # For specific database error handling
import traceback

from models.base_models import CaseEntryData # Import the Pydantic model
from db.matcher import CaseEntryMatcher # Import the matcher class
from services.error_handler import ErrorHelper # Import ErrorHelper

router = APIRouter()

# Dependency to get the CaseEntryMatcher instance
def get_case_entry_matcher(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

# Dependency for ErrorHelper
def get_error_helper_dependency(request: Request) -> ErrorHelper:
    return ErrorHelper(executor=request.app.state.executor)

@router.post("/api/case-entry")
async def new_case_entry_api(
    ackNo: Annotated[str, Form()],
    customerName: Annotated[str, Form()], 
    subCategory: Annotated[str, Form()],
    transactionDate: Annotated[date, Form()],
    complaintDate: Annotated[date, Form()],
    reportDateTime: Annotated[str, Form()],
    state: Annotated[str, Form()],
    district: Annotated[str, Form()],
    policestation: Annotated[str, Form()],
    paymentMode: Annotated[str, Form()],
    accountNumber: Annotated[Optional[Union[int, str]], Form()],
    cardNumber: Annotated[Optional[Union[int, str]], Form()],
    transactionId: Annotated[Union[int, str], Form()],
    layers: Annotated[str, Form()],
    transactionAmount: Annotated[float, Form()],
    disputedAmount: Annotated[float, Form()],
    action: Annotated[Optional[str], Form()],
    toBank: Annotated[str, Form()], 
    toAccount: Annotated[Optional[Union[int, str]], Form()],
    ifsc: Annotated[Optional[str], Form()],
    toTransactionId: Annotated[str, Form()], 
    toUpiId: Annotated[Optional[str], Form()],
    toAmount: Annotated[float, Form()], 
    actionTakenDate: Annotated[date, Form()], 
    #lienAmount: Annotated[Optional[float], Form()],
    #additionalInfo: Annotated[Optional[str], Form()],
    #evidence_file: Annotated[Optional[UploadFile], File()],
    
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_entry_matcher)],
    error_helper: Annotated[ErrorHelper, Depends(get_error_helper_dependency)]
):
    """
    Handles the submission of a new case entry, providing robust server-side validation
    and structured error responses from error_master.
    """
    form_data_dict = {
        "ackNo": ackNo, "customerName": customerName, "subCategory": subCategory, "transactionDate": transactionDate,
        "complaintDate": complaintDate, "reportDateTime": reportDateTime, "state": state, "district": district,
        "policestation": policestation, "paymentMode": paymentMode, "accountNumber": accountNumber,
        "cardNumber": cardNumber, "transactionId": transactionId, "layers": layers, "transactionAmount": transactionAmount,
        "disputedAmount": disputedAmount, "action": action, "toBank": toBank, "toAccount": toAccount,
        "ifsc": ifsc, "toTransactionId": toTransactionId, "toUpiId": toUpiId, "toAmount": toAmount,
        "actionTakenDate": actionTakenDate
    }

    try:
        case_data_instance = CaseEntryData(**form_data_dict)
        
        result = await matcher.match_data(case_data_instance)
        return {"result": result}

    except RequestValidationError as e: # Catches Pydantic's built-in validation errors
        print(f"❌ Frontend Validation Error (Pydantic): {e.errors()}", flush=True)
        await error_helper.get_error_response(
            error_code='3001', # Use the 'Validation Error' code from error_master
            http_status_code=status.HTTP_400_BAD_REQUEST,
            detail_override="One or more fields failed validation.",
            validation_errors=e.errors() # Include Pydantic's detailed errors
        )
    except ValueError as e: # Catches custom ValueErrors from matcher methods (e.g., validate_numeric_field)
        print(f"❌ Backend Logic Validation Error: {e}", flush=True)
        await error_helper.get_error_response(
            error_code='3001', # Use the 'Validation Error' code
            http_status_code=status.HTTP_400_BAD_REQUEST,
            detail_override=f"Details: {str(e)}"
        )
    except psycopg2.Error as e: # Catches database specific errors (e.g., UndefinedColumn, UniqueViolation)
        print(f"❌ Database Error in new_case_entry_api: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        if isinstance(e, psycopg2.errors.UniqueViolation):
            await error_helper.get_error_response(
                error_code='3101', # Assuming '3101' is for UniqueViolation/ACK Exists
                http_status_code=status.HTTP_409_CONFLICT, # 409 Conflict for duplicate resource
                detail_override=f"The Acknowledgement Number you provided might already exist. Details: {str(e)}"
            )
        else:
            await error_helper.get_error_response(
                error_code='2001', # Generic Database Error
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail_override=f"A database error occurred. Details: {str(e)}"
            )
    except Exception as e: # Catch any other unexpected server errors
        print(f"UNEXPECTED ERROR in new_case_entry_api: {e}", flush=True)
        import traceback
        traceback.print_exc()
        await error_helper.get_error_response(
            error_code='5000', # Generic Unexpected Server Error
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail_override=f"An unexpected server error occurred. Details: {str(e)}"
        )
