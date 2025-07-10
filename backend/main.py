# main.py
import urllib3
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import traceback

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from keycloak import KeycloakOpenID

from config import KEYCLOAK_CONFIG

from services.anomaly import AnomalyDetector

from routers import (
    auth,
    case_entry,
    dashboard, # Old dashboard
    decision,
    document,
    i4c_match,
    transaction,
    assignment,
    beneficiary_onboarding,
    suspect_account,
    new_case_list,
    combined_data,
    manual_file_confirm,
    ecb_cases
)

# --- FastAPI App Initialization ---
app = FastAPI(title="UniteHub API")

# --- GLOBAL EXECUTOR SETUP (Managed by app.state) ---
def initialize_executor_threadsafe():
    thread_executor = ThreadPoolExecutor(max_workers=10)
    print("ThreadPoolExecutor initialized.")
    return thread_executor

def shutdown_executor_threadsafe(thread_executor: ThreadPoolExecutor):
    if thread_executor:
        print("Shutting down ThreadPoolExecutor...")
        thread_executor.shutdown(wait=True)
        print("ThreadPoolExecutor shut down.")

@app.on_event("startup")
async def startup_event():
    app.state.executor = await asyncio.get_running_loop().run_in_executor(None, initialize_executor_threadsafe)
    app.state.anomaly_detector = AnomalyDetector()
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    app.state.keycloak_openid = KeycloakOpenID(
        server_url=KEYCLOAK_CONFIG["server_url"],
        realm_name=KEYCLOAK_CONFIG["realm_name"],
        client_id=KEYCLOAK_CONFIG["client_id"],
        client_secret_key=KEYCLOAK_CONFIG["client_secret_key"],
        verify=KEYCLOAK_CONFIG["verify_ssl"]
    )
    print("FastAPI application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, 'executor') and app.state.executor:
        await asyncio.get_running_loop().run_in_executor(None, shutdown_executor_threadsafe, app.state.executor)
    print("FastAPI application shutdown complete.")


# --- CORS Middleware Configuration ---
origins = [
    "http://34.47.219.225:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"]
)

# --- Include Routers ---
app.include_router(auth.router, tags=["Authentication"])
app.include_router(case_entry.router, tags=["Case Entry"])
app.include_router(dashboard.router, tags=["Dashboard & Case List (Old)"])
app.include_router(decision.router, tags=["Decision Console"])
app.include_router(document.router, tags=["Documents & Files"])
app.include_router(i4c_match.router, tags=["I4C Matching & Screening"])
app.include_router(transaction.router, tags=["Transactions & Case Details"])
app.include_router(assignment.router, tags=["Case Assignment"])
app.include_router(beneficiary_onboarding.router, tags=["Beneficiary Onboarding & Screening"])
app.include_router(suspect_account.router, tags=["Suspect Account Screening"])
app.include_router(new_case_list.router, tags=["New Dashboard (Case List)"])
app.include_router(combined_data.router, tags=["Combined Case Data"]) # This now serves all new detail needs
app.include_router(manual_file_confirm.router, tags=["I4C Manual Confirmations"])
app.include_router(ecb_cases.router, tags=["ECB/ECBNT Case Creation"])

# --- This is your existing root endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to UniteHub API!"}
