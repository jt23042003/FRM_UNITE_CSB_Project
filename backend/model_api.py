# model_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any

# Import the prediction function from your predict.py file
from predict import make_prediction

# 1. --- Initialize a new, separate FastAPI app ---
app = FastAPI()

# 2. --- Define the Pydantic models for the request body ---
# These define the structure of the JSON you will send
class ML_Customer(BaseModel):
    cust_id: str
    acc_num: int
    aqb: float = Field(None)
    tenure_days: int = Field(None)
    customer_joining_date: Any = Field(None)
    acc_status: Any = Field(None)
    rel_type: Any = Field(None)
    last_txn_date: Any = Field(None)
    branch_code: Any = Field(None)
    lien: Any = Field(None)
    od_limit: Any = Field(None)
    credit_score: Any = Field(None)
    gender: Any = Field(None)
    occupation: Any = Field(None)
    seg: Any = Field(None)
    risk_prof: Any = Field(None)
    kyc_status: Any = Field(None)
    dob: Any = Field(None)
    age: Any = Field(None)
    txn_count_last_month: Any = Field(None)
    total_txn_value: Any = Field(None)
    multi_account_holder: Any = Field(None)

class ML_Transaction(BaseModel):
    txn_ref: str
    txn_date: str
    txn_time: str
    amount: float
    acct_num: int
    txn_type: Any = Field(None)
    currency: Any = Field(None)
    descr: Any = Field(None)
    fee: Any = Field(None)
    exch_rate: Any = Field(None)
    bene_name: Any = Field(None)
    bene_acct_num: Any = Field(None)
    pay_ref: Any = Field(None)
    auth_code: Any = Field(None)
    channel: Any = Field(None)
    pay_method: Any = Field(None)

class PredictionRequest(BaseModel):
    customer_details: ML_Customer
    transaction_details: List[ML_Transaction]


# 3. --- Create the API endpoint for prediction ---
@app.post("/predict")
async def predict_endpoint(request: PredictionRequest):
    """
    This endpoint receives customer and transaction data, runs the model,
    and returns the prediction as a direct JSON response.
    """
    try:
        print(f"Prediction request received for customer: {request.customer_details.cust_id}")
        
        # Prepare data for the model
        cust_dict = request.customer_details.dict()
        trans_list_of_dicts = [t.dict() for t in request.transaction_details]

        # Call the prediction function
        label = make_prediction(cust_dict, trans_list_of_dicts)
        
        print(f"Model prediction: {label}")

        # Return the result directly
        return {
            "customer_id": request.customer_details.cust_id,
            "model_prediction": label,
            "status": "completed"
        }

    except Exception as e:
        print(f"ERROR during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

@app.get("/")
def root():
    return {"message": "Model Prediction API is running"}