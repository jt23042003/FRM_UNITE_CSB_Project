# models/base_models.py
from pydantic import BaseModel, Field, root_validator, validator
from typing import List, Optional, Union
from datetime import date

# --- Login Request Model ---
class LoginRequest(BaseModel):
    username: str
    password: str

# NEW MODEL: CaseMainUpdateData for updating cases in case_main table
class CaseMainUpdateData(BaseModel):
    # These fields correspond to columns in case_main that can be updated
    caseType: Optional[str] = None
    sourceAckNo: Optional[str] = None
    sourceBeneAccno: Optional[str] = None
    accNum: Optional[str] = None
    custId: Optional[str] = None
    isOperational: Optional[bool] = None
    status: Optional[str] = None
    decision: Optional[str] = None
    remarks: Optional[str] = None
    assignedTo: Optional[str] = None # Assuming assigned_to will be updated via this API as well
    assignedBy: Optional[str] = None
    reassignedFrom: Optional[str] = None
    reassignmentCount: Optional[int] = None
    # Add new fields short_dn, long_dn, decision_type added to case_main
    shortDn: Optional[str] = None
    longDn: Optional[str] = None
    decisionType: Optional[str] = None
    # No creation_date/time as they are not typically updated

# --- Decision Data Model ---
class DecisionData(BaseModel):
    riskScore: Optional[str] = None
    triggeringRules: Optional[str] = None
    comments: Optional[str] = None
    decisionAction: Optional[str] = None
    caseManagement: Optional[str] = None
    assignedEmployee: Optional[str] = None
    auditTrail: Optional[str] = None
    systemRecommendation: Optional[str] = None
    systemExplanation: Optional[str] = None

# --- I4C Data (Complex Input) Model ---
class I4CData(BaseModel):
    complaintref: str; incidentDateTime: str; complaintType: str; victimName: str; victimContact: str
    victimEmail: str; victimAccountNumber: str; victimBankName: str; transactionId: str; ifsc: str
    victimRelativeName: str; victimAddress: str; victimState: str; victimCity: str; victimPincode: str
    fraudAmount: str; lienAmount: str; beneficiaryAccountNumber: str; beneficiaryMobile: str
    beneficiaryEmail: str; beneficiaryUPI: str; beneficiaryIp: str; beneficiaryInfo: str
    evidence: List[str]; urls: str; actionRequested: str; policeName: str; policeDesignation: str
    policeMobile: str; policeEmail: str; additionalInfo: str
    subCategory: Optional[str] = None; complaintDate: Optional[str] = None; incidentLocation: Optional[str] = None
    suspectIdType: Optional[str] = None; suspectIdNo: Optional[str] = None; txnSno: Optional[int] = None
    txnEntity: Optional[str] = None; txnAcctWallet: Optional[str] = None; txnAmount: Optional[str] = None
    txnDate: Optional[str] = None; txnComplaintDate: Optional[str] = None; txnRemarks: Optional[str] = None
    reportedState: Optional[str] = None; forwardedTo: Optional[str] = None; incidentUrlId: Optional[str] = None

# --- Case Entry Data (from your form) Model ---
class CaseEntryData(BaseModel):
    ackNo: str
    customerName: str 
    subCategory: str
    transactionDate: date
    complaintDate: date
    reportDateTime: str
    state: str
    district: str
    policestation: str
    paymentMode: str
    accountNumber: Optional[Union[int, str]] = None
    cardNumber: Optional[Union[int, str]] = None
    transactionId: str # FIX: Changed to str to allow alphanumeric
    layers: str
    transactionAmount: float
    disputedAmount: float

    action: Optional[str] = None
    toBank: str 
    toAccount: Optional[Union[int, str]] = None
    ifsc: Optional[str] = None
    toTransactionId: Optional[str] = None # FIX: Changed to Optional[str] to allow alphanumeric and optional
    toUpiId: Optional[str] = None
    toAmount: float
    actionTakenDate: date 
    lienAmount: Optional[float] = None
    additionalInfo: Optional[str] = None

    @root_validator(pre=True)
    def check_conditional_fields(cls, values):
        payment_mode = values.get('paymentMode')
        non_mandatory_rules = { 
            'UPI': ['cardNumber', 'toAccount', 'ifsc'],
            'Net Banking / Internet Banking': ['cardNumber', 'toUpiId'],
            'Credit Card': ['accountNumber', 'toUpiId'],
            'Debit Card': ['toUpiId'],
            'Digital Wallets / Mobile Wallets': ['accountNumber', 'toUpiId'],
            'Cheque': ['toUpiId'],
            'IMPS': ['cardNumber', 'toUpiId'],
            'NEFT': ['cardNumber', 'toUpiId'],
            'RTGS': ['cardNumber', 'toUpiId'],
            'AEPS': ['cardNumber', 'toUpiId'],
            'POS Terminals': ['accountNumber', 'toBank', 'toUpiId', 'toAccount', 'ifsc']
        }
        
        potentially_required_fields = { 
            'ackNo': 'Acknowledgement No.', 'customerName': 'Customer Name', 
            'subCategory': 'Sub Category of Complaint', 'transactionDate': 'Transaction Date',
            'complaintDate': 'Complaint Date', 'reportDateTime': 'Date & Time of Reporting / Escalation', 'state': 'State',
            'district': 'District', 'policestation': 'Policestation', 'paymentMode': 'Mode of Payment',
            'transactionId': 'Transaction Id / UTR Number', # This is now alphanumeric
            'layers': 'Layers', 'transactionAmount': 'Transaction Amount',
            'disputedAmount': 'Disputed Amount', 'toAmount': 'Money transfer TO Amount', 'actionTakenDate': 'Action Taken Date',
            'toBank': 'Money transfer TO Bank', 'toTransactionId': 'Money transfer TO Transaction Id / UTR Number' # This is now alphanumeric
        }
        
        for field_name, display_name in potentially_required_fields.items():
            is_non_mandatory_by_rule = field_name in non_mandatory_rules.get(payment_mode, [])

            if not is_non_mandatory_by_rule and field_name in potentially_required_fields:
                if values.get(field_name) is None or str(values.get(field_name)).strip() == '':
                    raise ValueError(f'{display_name} is required for the selected payment mode.')

        return values


# --- Case Action Request Model ---
class CaseActionRequest(BaseModel):
    case_id: int
    action: str
    assigned_to: Optional[str] = None
    remarks: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str

# --- New Customer Request Model (for screening) ---
class NewCustomer(BaseModel):
    customerId: str
    fullName: str
    aadhar: str
    pan: str
    mobile: str
    dob: str

class NewCustomerRequest(BaseModel):
    customers: List[NewCustomer]

# --- Beneficiary Verification Data Model ---
class BeneficiaryData(BaseModel):
    customerId: str
    customerName: str
    beneficiaryName: str
    beneficiaryMobile: str
    beneficiaryAccountNumber: str
    beneficiaryEmail: str
    beneficiaryUPI: str
    beneficiaryPAN: Optional[str] = None
    beneficiaryAadhar: Optional[str] = None
    beneficiaryIFSC: Optional[str] = None

# --- Transaction Data for Classification API ---
class TransactionData(BaseModel):
    acct_num: Union[int, str]
    amount: Union[float, str]
    txn_ref: Optional[str] = None
    descr: Optional[str] = None

# NEW MODEL: PotentialSuspectAccountData for PSA case creation
class PotentialSuspectAccountData(BaseModel):
    customerId: str
    customerName: Optional[str] = None
    accountNumber: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    pan: Optional[str] = None
    aadhar: Optional[str] = None
    upiId: Optional[str] = None
    ifsc: Optional[str] = None
    suspiciousActivityDescription: Optional[str] = None
    transactionAmount: Optional[float] = None

class I4CManualFileConfirmationData(BaseModel):
    case_id: int # The case_id for which documents are being confirmed
    checked_documents: List[str] # List of document names (strings) that were checked/confirmed
    proof_of_upload_ref: str # The reference number for this batch of confirmations
    status: str # The status of this action (e.g., 'saved', 'submitted')

# NEW MODEL: ECBCaseData for creating ECBT/ECBNT cases (Stage 2 Internal Cases)
class ECBCaseData(BaseModel):
    # This payload should contain enough info to create a case based on beneficiary
    sourceAckNo: str # Original ACK no from data entry, or new generated if none
    customerId: Optional[str] = None # Customer ID (if found during matching)
    beneficiaryAccountNumber: str # Key detail for ECBT/ECBNT
    beneficiaryMobile: Optional[str] = None
    beneficiaryEmail: Optional[str] = None
    beneficiaryPAN: Optional[str] = None
    beneficiaryAadhar: Optional[str] = None
    beneficiaryUPI: Optional[str] = None
    hasTransaction: bool # True if it's an ECBT, False if ECBNT
    remarks: Optional[str] = None
    # Add any other fields needed for case_main

