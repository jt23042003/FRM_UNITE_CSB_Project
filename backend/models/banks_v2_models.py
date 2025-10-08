from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re
from datetime import datetime


ALLOWED_SUB_CATEGORIES = {
    "E-Wallet Related Fraud",
    "Debit/Credit Card Fraud/Sim Swap Fraud",
    "Debit/Credit Card Fraud/Sim Swap Fraud (VISA, Master Card, Debit Card, American Express, Rupay)",
    "Internet Banking Related Fraud",
    "Demat /Depository Fraud",
    "Business Email Compromise/Email Takeover",
    "Fraud Call /Vishing",
    "UPI Related Frauds",
    "Aadhar Enabled Payment System (AEPS) Related Frauds"
}


class IncidentData(BaseModel):
    amount: str = Field(..., description="Amount with two decimal places e.g. 35.00")
    rrn: str = Field(..., description="Numeric RRN, typically 10-14 digits")
    transaction_date: str = Field(..., description="Date in DD-MM-YYYY")
    transaction_time: Optional[str] = Field(None, description="Time in HH:MM:SS")
    disputed_amount: str = Field(..., description="Amount with two decimal places e.g. 35.00")
    layer: int = Field(..., description="Integer layer, e.g., 0")

    # Card-only fields (optional; required when sub_category is Card Fraud)
    first6digit: Optional[str] = None
    last4digit: Optional[str] = None
    cardlength: Optional[str] = None

    @validator("amount", "disputed_amount")
    def validate_amount_format(cls, v: str) -> str:
        if not re.fullmatch(r"^\d+\.\d{2}$", v):
            raise ValueError("Amount must be in NNNN.NN format")
        return v

    @validator("rrn")
    def validate_rrn(cls, v: str) -> str:
        if not re.fullmatch(r"^\d{10,14}$", v):
            raise ValueError("RRN must be numeric with 10-14 digits")
        return v

    @validator("transaction_date")
    def validate_transaction_date(cls, v: str) -> str:
        try:
            # Expect DD-MM-YYYY
            datetime.strptime(v, "%d-%m-%Y")
        except Exception:
            raise ValueError("transaction_date must be DD-MM-YYYY")
        return v

    @validator("transaction_time")
    def validate_transaction_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not re.fullmatch(r"^\d{2}:\d{2}:\d{2}$", v):
            raise ValueError("transaction_time must be HH:MM:SS (24-hour)")
        return v


class InstrumentData(BaseModel):
    requestor: str
    payer_bank: str
    payer_bank_code: int
    mode_of_payment: str
    payer_mobile_number: str
    payer_account_number: str
    state: str
    district: str
    transaction_type: Optional[str] = None
    wallet: Optional[str] = None

    @validator("payer_mobile_number")
    def validate_mobile(cls, v: str) -> str:
        if not re.fullmatch(r"^\d{10,15}$", v):
            raise ValueError("payer_mobile_number must be 10-15 digits")
        return v

    @validator("payer_account_number")
    def validate_account(cls, v: str) -> str:
        if not re.fullmatch(r"^\d{9,18}$", v):
            raise ValueError("payer_account_number must be 9-18 digits")
        return v


class CaseEntryV2(BaseModel):
    acknowledgement_no: str
    sub_category: str
    instrument: InstrumentData
    incidents: List[IncidentData]

    class Config:
        allow_population_by_field_name = True

    @validator("acknowledgement_no")
    def validate_ack(cls, v: str) -> str:
        if not re.fullmatch(r"^[A-Za-z0-9]{8,20}$", v):
            # Accept common numeric form from sample too
            if not re.fullmatch(r"^\d{8,20}$", v):
                raise ValueError("acknowledgement_no must be 8-20 alphanumeric characters")
        return v

    @validator("sub_category")
    def validate_sub_category(cls, v: str) -> str:
        if v not in ALLOWED_SUB_CATEGORIES:
            raise ValueError("Unsupported sub_category for current implementation phase")
        return v

    @validator("incidents")
    def validate_incidents_non_empty(cls, v: List[IncidentData]) -> List[IncidentData]:
        if not v:
            raise ValueError("incidents must contain at least one item")
        if len(v) > 25:
            # Aligns with response code 04 (Invalid incidents count)
            raise ValueError("incidents count cannot exceed 25")
        return v


