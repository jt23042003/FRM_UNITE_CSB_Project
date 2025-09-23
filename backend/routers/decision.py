# routers/decision.py
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import Optional, Any, Dict, List, Annotated
import asyncio
import traceback
import functools # For functools.partial in classification

from fastapi import APIRouter, HTTPException, Query, Depends, Request, Body
from concurrent.futures import ThreadPoolExecutor

from db.matcher import save_or_update_decision, get_decision, CaseEntryMatcher, CaseNotFoundError
from services.anomaly import AnomalyDetector
from models.base_models import TransactionData # For classify_transaction_api if it's kept public

router = APIRouter()

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

def get_anomaly_detector_dependency(request: Request) -> AnomalyDetector:
    return request.app.state.anomaly_detector


# Internal helper function for classification logic
async def _perform_transaction_classification(
    transaction_input_for_model: Dict[str, Any],
    executor: ThreadPoolExecutor,
    detector: AnomalyDetector
) -> Dict[str, Any]:
    try:
        classification_result = await asyncio.get_running_loop().run_in_executor(
            executor,
            detector.classify_transaction,
            transaction_input_for_model
        )
        if "error" in classification_result:
            raise ValueError(f"Model returned an error: {classification_result['error']}")
        return classification_result
    except Exception as e:
        print(f"Error during _perform_transaction_classification: {e}", flush=True)
        traceback.print_exc()
        raise


# PUBLIC API Endpoint for classification (if still needed)
@router.post("/api/classify-transaction")
async def classify_transaction_api(
    transaction: TransactionData,
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    detector: Annotated[AnomalyDetector, Depends(get_anomaly_detector_dependency)]
) -> Dict[str, Any]:
    """
    Receives a single transaction as JSON and classifies it as normal or anomaly.
    """
    try:
        transaction_dict = transaction.dict()
        
        classification_result = await _perform_transaction_classification(
            transaction_dict, executor, detector
        )
        
        return {
            "input_transaction": transaction_dict,
            "classification_result": classification_result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in /api/classify-transaction endpoint: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred during classification: {e}")


# This endpoint handles saving/updating a decision (ONLY case_history)
@router.post("/api/case/{ack_no}/decision")
async def save_decision_api(
    ack_no: str,
    data: Dict[str, Any],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)] # Needed to fetch case_id
) -> Dict[str, Any]:
    """
    Saves or updates the decision console data for a case, converting ack_no to case_id.
    """
    # FIX: Get integer case_id from case_main using ack_no
    try:
        case_main_record = await matcher.fetch_single_case_details_from_case_main_by_ack_no(ack_no)
        if not case_main_record or not case_main_record.get('case_id'):
            raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system.")
        integer_case_id = case_main_record.get('case_id')
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system. Error: {e}")
    except Exception as e:
        print(f"ERROR: Failed to fetch case_id for ACK No {ack_no} during decision save: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error fetching case details: {e}")

    try:
        # Pass the integer case_id to save_or_update_decision
        updated_record = await save_or_update_decision(executor, integer_case_id, data)
        return {"success": True, "message": "Decision submitted successfully.", "data": updated_record}

    except Exception as e:
        print(f"Error saving decision for ACK No {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to save decision.")

# This endpoint handles fetching a decision and calling the model if needed
@router.get("/api/case/{ack_no}/decision")
async def get_decision_api(
    ack_no: str,
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    detector: Annotated[AnomalyDetector, Depends(get_anomaly_detector_dependency)]
) -> Dict[str, Any]:
    """
    Retrieves decision data for a case, converting ack_no to case_id for database queries.
    If no decision is stored, calls the classification model and stores its output.
    """
    # FIX: Get integer case_id from case_main using ack_no
    try:
        case_main_record = await matcher.fetch_single_case_details_from_case_main_by_ack_no(ack_no)
        if not case_main_record or not case_main_record.get('case_id'):
            raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system.")
        integer_case_id = case_main_record.get('case_id')
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system. Error: {e}")
    except Exception as e:
        print(f"ERROR: Failed to fetch case_id for ACK No {ack_no} during decision fetch: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error fetching case details: {e}")

    try:
        # FIX: Pass the integer case_id to get_decision
        decision_data = await get_decision(executor, integer_case_id)

        if not decision_data: # If no decision is stored in DB, call the model
            print(f"No stored decision found for ACK No {ack_no}. Calling classification model...", flush=True)

            # Case details needed for model input (from case_main_record)
            transaction_input_for_model = {
                "acct_num": str(case_main_record.get("acc_num") or ""),
                "amount": float(case_main_record.get("transaction_amount") or 0.0), # Assuming transaction_amount is in case_main
                "txn_ref": case_main_record.get("source_ack_no") or "", # Use source_ack_no as txn_ref
                "descr": case_main_record.get("remarks") or "No description"
            }
            transaction_input_for_model = {k: v for k, v in transaction_input_for_model.items() if v != "" and v is not None}
            
            try:
                classification_result = await _perform_transaction_classification(
                    transaction_input_for_model, executor, detector
                )

                system_recommendation = classification_result.get("classification")
                system_explanation = classification_result.get("reason")

                print(f"Model classified: {system_recommendation} - {system_explanation}", flush=True)

                decision_data_to_save = {
                    "riskScore": system_recommendation, # Mapping to riskScore
                    "systemRecommendation": system_recommendation, # For consistency, also map to this
                    "systemExplanation": system_explanation, # For consistency
                    "comments": "Auto-generated by classification model.",
                    "decisionAction": system_recommendation, # Map decisionAction to recommendation
                    "assignedEmployee": None, # Initial, not assigned by model
                    "auditTrail": "Model classification on first fetch."
                }
                
                # FIX: Pass the integer case_id to save_or_update_decision
                updated_record = await save_or_update_decision(executor, integer_case_id, decision_data_to_save)
                
                return {"success": True, "data": updated_record}

            except HTTPException:
                raise
            except Exception as model_err:
                print(f"Unexpected error during model call or processing: {model_err}", flush=True)
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Failed to get model recommendation: {model_err}")
            
        else:
            return {"success": True, "data": decision_data}

    except Exception as e:
        print(f"Error fetching decision for ACK No {ack_no}: {e}", flush=True)
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An internal server error occurred while retrieving decision: {e}")
