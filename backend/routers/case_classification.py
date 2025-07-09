from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Annotated

# Import the new Pydantic request model
from models.base_models import CaseClassificationRequest

# Import the new service
from services.case_classifier import CaseClassifier

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

# Dependency to get the CaseClassifier instance
def get_case_classifier(request: Request) -> CaseClassifier:
    """
    Provides an instance of CaseClassifier, injecting the ThreadPoolExecutor
    from the FastAPI app's state.
    """
    if not hasattr(request.app.state, 'executor') or not request.app.state.executor:
        logging.error("ThreadPoolExecutor not initialized on app.state. Make sure startup event runs.")
        raise HTTPException(status_code=500, detail="Internal server configuration error.")
    
    return CaseClassifier(executor=request.app.state.executor)

@router.post("/api/cases/classify-and-create", tags=["Case Management"])
async def classify_and_create_case_api(
    request_data: CaseClassificationRequest, # Pydantic model for request body
    classifier: Annotated[CaseClassifier, Depends(get_case_classifier)] # Inject our service
):
    """
    API endpoint to classify a case based on 'to_account' and create an entry
    in the case_details_1 table.
    """
    logging.info(f"API call received for classify_and_create_case for to_account: {request_data.to_account}")
    
    try:
        case_result = await classifier.classify_and_create_case(
            to_account=request_data.to_account,
            card_number=request_data.card_number
        )

        if case_result:
            return {
                "message": "Case processed and created successfully",
                "status": "success",
                "case_details": case_result
            }
        else:
            # As per your clarification: "if there's no matching there's nothing that we are doing"
            # Return a 200 OK with a clear message that no case was created.
            return {
                "message": "No matching case scenario found for the provided account number. Case not created.",
                "status": "no_match",
                "to_account": request_data.to_account
            }
    except Exception as e:
        logging.error(f"Error in classify_and_create_case_api for {request_data.to_account}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during case classification and creation.")
