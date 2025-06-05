from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
import psycopg2
from matcher import DatabaseMatcher
from config import conn_params
from fastapi import Query
from fastapi.responses import JSONResponse
from typing import List, Optional

print("✅ LIVE match_api.py LOADED from /home/ubuntu")

router = APIRouter()
# FastAPI app
app = FastAPI()
app.include_router(router)

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://34.47.219.225:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DatabaseMatcher:
    def __init__(self, conn_params):
        self.conn = psycopg2.connect(**conn_params)
        self.cur = self.conn.cursor()

    def close_connection(self):
        self.cur.close()
        self.conn.close()

    def insert_cyber_complaint(self, data):
        # Avoid duplicate ack_no
        self.cur.execute("SELECT ack_no FROM cyber_complaints WHERE ack_no = %s", (data.complaintRef,))
        existing = self.cur.fetchone()
        if existing:
            return None

        self.cur.execute("""
            INSERT INTO cyber_complaints (
                ack_no, category, sub_category, complaint_date,
                incident_location, incident_url_id,
                suspect_name, ip_address, suspect_id_type, suspect_id_no,
                suspect_bank_acct, suspect_upi_mobile,
                comp_full_name, comp_mobile, comp_relation_name, comp_email,
                comp_address, comp_state, comp_district_ps, comp_relation_with_victim,
                complaint_ps_name, complaint_ps_desig, complaint_ps_mobile, complaint_ps_email,
                fraud_amount, txn_sno, txn_entity, txn_acct_wallet, txn_amount,
                txn_ref_no, txn_date, txn_complaint_date, txn_remarks,
                reported_state, forwarded_to
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
        """, (
            data.complaintRef,
            data.complaintType,
            data.subCategory,
            data.complaintDate or date.today(),
            data.incidentLocation,
            data.incidentUrlId,
            data.beneficiaryInfo,
            data.beneficiaryIp,
            data.suspectIdType,
            data.suspectIdNo,
            data.beneficiaryAccountNumber,
            data.beneficiaryMobile,
            data.victimName,
            data.victimContact,
            data.victimRelativeName,
            data.victimEmail,
            data.victimAddress,
            data.victimState,
            None,  # comp_district_ps
            "Relative",
            data.policeName,
            data.policeDesignation,
            data.policeMobile,
            data.policeEmail,
            data.fraudAmount,
            data.txnSno,
            data.txnEntity,
            data.txnAcctWallet,
            data.txnAmount,
            data.transactionId,
            data.txnDate,
            data.txnComplaintDate,
            data.txnRemarks,
            data.reportedState,
            data.forwardedTo
        ))
        self.conn.commit()
        return data.complaintRef

    def fetch_customer_data(self):
        self.cur.execute("SELECT cust_id, fname, mname, lname, mobile, email, pan, nat_id FROM customer")
        return self.cur.fetchall()

    def insert_case_master(self, ack_no, cust_id, match_type):
        today = date.today()
        self.cur.execute("""
            INSERT INTO case_master (ack_no, cust_id, match_type, status, created_on, closed_on, decision, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING case_id
        """, (ack_no, cust_id, match_type, 'New', today, None, '', ''))
        case_id = self.cur.fetchone()[0]
        self.conn.commit()
        return case_id

    def insert_case_details(self, case_id, cust_id, complaint_date, mobile, email, pan, nat_id, card_num, acct_num, txn_ref_id):
        self.cur.execute("""
            INSERT INTO case_detail (case_id, cust_id, comp_date, mobile, email, pan, aadhar, card, acct, txn_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (case_id, cust_id, complaint_date, mobile, email, pan, nat_id, card_num or '', acct_num or '', txn_ref_id or ''))
        self.conn.commit()
    def match_data_from_dict(self, i4c_data: dict):
        # Step 1: Insert complaint
        ack_no = self.insert_cyber_complaint(i4c_data)

        if ack_no is None:
            return f"⚠️ Duplicate ack_no '{i4c_data['ack_no']}' already exists. Skipping insert."

        # Step 2: Try matching with customer table
        customers = self.fetch_customer_data()
        for cust in customers:
            cust_id, fname, mname, lname, mobile, email, pan, nat_id = cust
            full_name = f"{fname} {mname} {lname}".strip().lower()

            i4c_name_fields = [
                i4c_data["beneficiaryInfo"].lower(),
                i4c_data["victimName"].lower(),
                i4c_data["complaint_ps_name"].lower()
            ]
            i4c_mobiles = [
                i4c_data["victimContact"],
                i4c_data["complaint_ps_mobile"],
                i4c_data["beneficiaryMobile"]
            ]

            matched = False
            match_type = ''

            if full_name in i4c_name_fields:
                matched = True
                match_type = 'Suspect' if full_name == i4c_data["beneficiaryInfo"].lower() else 'Victim'

            if (
                mobile in i4c_mobiles or
                email == i4c_data["victimEmail"] or
                pan == i4c_data["transactionId"] or
                nat_id == i4c_data["transactionId"]
            ):
                matched = True
                match_type = 'Suspect' if full_name == i4c_data["beneficiaryInfo"].lower() else 'Victim'

            if matched:
                case_id = self.insert_case_master(ack_no, cust_id, match_type)
                self.insert_case_details(
                    case_id=case_id,
                    cust_id=cust_id,
                    complaint_date=date.today(),
                    mobile=mobile,
                    email=email,
                    pan=pan,
                    nat_id=nat_id,
                    card_num=None,
                    acct_num=i4c_data["beneficiaryAccountNumber"],
                    txn_ref_id=i4c_data["transactionId"]
                )
                return f"✅ Match found: inserted into case_master with ack_no {ack_no}"

        return f"ℹ️ Inserted complaint to cyber_complaints, but no customer match found (ack_no: {ack_no})"


    def close_connection(self):
        self.cur.close()
        self.conn.close()


# DB connection parameters
conn_params = {
    'host': '34.47.219.225',
    'dbname': 'unitedb',
    'user': 'unitedb_user',
    'password': 'password123',
    'port': '5432'
}

from pydantic import BaseModel
from typing import List, Optional

class I4CData(BaseModel):
    complaintref: str
    incidentDateTime: str
    complaintType: str
    victimName: str
    victimContact: str
    victimEmail: str
    victimAccountNumber: str
    victimBankName: str
    transactionId: str
    ifsc: str
    victimRelativeName: str
    victimAddress: str
    victimState: str
    victimCity: str
    victimPincode: str
    fraudAmount: str
    lienAmount: str
    beneficiaryAccountNumber: str
    beneficiaryMobile: str
    beneficiaryEmail: str
    beneficiaryUPI: str
    beneficiaryIp: str
    beneficiaryInfo: str
    evidence: List[str]
    urls: str
    actionRequested: str
    policeName: str
    policeDesignation: str
    policeMobile: str
    policeEmail: str
    additionalInfo: str

    # Backend-only optional fields (not present in frontend payload)
    subCategory: Optional[str] = None
    complaintDate: Optional[str] = None
    incidentLocation: Optional[str] = None
    suspectIdType: Optional[str] = None
    suspectIdNo: Optional[str] = None
    txnSno: Optional[int] = None
    txnEntity: Optional[str] = None
    txnAcctWallet: Optional[str] = None
    txnAmount: Optional[str] = None
    txnDate: Optional[str] = None
    txnComplaintDate: Optional[str] = None
    txnRemarks: Optional[str] = None
    reportedState: Optional[str] = None
    forwardedTo: Optional[str] = None
    incidentUrlId: Optional[str] = None

#New match-i4c-data api endpoint
from typing import Union
class CaseEntryData(BaseModel):
    ackNo: str
    subCategory: str
    transactionDate: str
    complaintDate: str
    reportDateTime: str
    state: str
    district: str
    policestation: str
    paymentMode: str
    accountNumber: Union[int, str]
    cardNumber: Union[int, str]
    transactionId: Union[int, str]
    layers: str
    transactionAmount: float
    disputedAmount: float
    action: str
    toBank: float
    toAccount: Union[int, str]
    ifsc: str
    toTransactionId: Union[int, str]
    toAmount: float
    actionTakenDate: str
    lienAmount: Optional[float] = None
    evidence: Optional[str] = None
    evidenceName: str
    additionalInfo: str

from datetime import date
import psycopg2

class CaseEntryMatcher:
    def __init__(self, conn_params):
        self.conn = psycopg2.connect(**conn_params)
        self.cur = self.conn.cursor()

    def fetch_customer_data(self):
        self.cur.execute("SELECT cust_id, fname, mname, lname, mobile, email, pan, nat_id FROM customer")
        return self.cur.fetchall()

    def insert_case_master(self, ack_no, cust_id, match_type):
        today = date.today()
        self.cur.execute("""
            INSERT INTO case_master (ack_no, cust_id, match_type, status, created_on, closed_on, decision, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING case_id
        """, (ack_no, cust_id, match_type, 'New', today, None, '', ''))
        case_id = self.cur.fetchone()[0]
        self.conn.commit()
        return case_id

    def insert_case_details(self, case_id, cust_id, complaint_date, mobile, email, pan, nat_id, card_num, acct_num, txn_ref_id):
        self.cur.execute("""
            INSERT INTO case_detail (case_id, cust_id, comp_date, mobile, email, pan, aadhar, card, acct, txn_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (case_id, cust_id, complaint_date, mobile, email, pan, nat_id,
              card_num or '', acct_num or '', txn_ref_id or ''))
        self.conn.commit()

    def match_data(self, data):
        customers = self.fetch_customer_data()

        for cust in customers:
            cust_id, fname, mname, lname, mobile, email, pan, nat_id = cust
            full_name = f"{fname} {mname} {lname}".strip().lower()

            frontend_name_fields = [
                data.additionalInfo.lower(),     # victimName (text area)
                data.policestation.lower()       # policeName
            ]

            frontend_mobiles = [
                data.accountNumber,
                data.toTransactionId,
                ""  # no policeMobile in frontend
            ]

            matched = False
            match_type = ''

            if full_name in frontend_name_fields:
                matched = True
                match_type = 'Suspect' if full_name == data.toBank.lower() else 'Victim'

            if (
                mobile in frontend_mobiles or
                email == "" or                       # victimEmail not in form
                pan == data.transactionId or
                nat_id == data.transactionId
            ):
                matched = True
                match_type = 'Suspect' if full_name == data.toBank.lower() else 'Victim'

            if matched:
                case_id = self.insert_case_master(data.ackNo, cust_id, match_type)
                self.insert_case_details(
                    case_id=case_id,
                    cust_id=cust_id,
                    complaint_date=date.today(),
                    mobile=mobile,
                    email=email,
                    pan=pan,
                    nat_id=nat_id,
                    card_num=data.cardNumber,
                    acct_num=data.toAccount,
                    txn_ref_id=data.transactionId
                )
                return f"✅ Match found: inserted into case_master with ack_no {data.ackNo}"

        return f"ℹ️ Inserted form data but no customer match found (ack_no: {data.ackNo})"

    def close_connection(self):
        self.cur.close()
        self.conn.close()

@app.post("/api/case-entry")
def new_case_entry(data: CaseEntryData):
    matcher = CaseEntryMatcher(conn_params)
    result = matcher.match_data(data)
    matcher.close_connection()
    return {"result": result}


# API endpoint
@app.post("/api/match-i4c-data")
def match_i4c(i4c_data: I4CData):
    try:
        matcher = DatabaseMatcher(conn_params)
        result = matcher.match_data(i4c_data)
        matcher.close_connection()
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/case-list")
def get_case_list():
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        # Updated query to include new fields
        cur.execute("""
            SELECT
                ack_no,
                complaint_type,
                source,
                match_type,
                location,
                transaction_amount,
                status
            FROM case_master
            ORDER BY created_on DESC
            LIMIT 25
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        cases = [
            {
                "ack_no": row[0],
                "complaint_type": row[1],
                "source": row[2],
                "match_type": row[3],
                "location": row[4],
                "transaction_amount": row[5],
                "status": row[6]
            }
            for row in rows
        ]

        return JSONResponse(content={"cases": cases})

    except Exception as e:
        print("ERROR in /api/case-list:", str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/all-cases")
def list_cases(status: Optional[str] = None):
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        if status:
            cur.execute("""
                SELECT case_id, ack_no, match_type, status, created_on, assigned_to
                FROM case_master
                WHERE status = %s
                ORDER BY created_on DESC
            """, (status,))
        else:
            cur.execute("""
                SELECT case_id, ack_no, match_type, status, created_on, assigned_to
                FROM case_master
                ORDER BY created_on DESC
            """)
        rows = cur.fetchall()
        cases = [
            {
                "case_id": row[0],
                "ack_no": row[1],
                "match_type": row[2],
                "status": row[3],
                "created_on": row[4],
                "assigned_to": row[5]
            }
            for row in rows
        ]
        cur.close()
        conn.close()
        return {"cases": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/case/{ack_no}")
def get_case_details(ack_no: str):
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        # Step 1: Get master using ack_no
        cur.execute("""
            SELECT case_id, ack_no, match_type, status, created_on, closed_on, decision, remarks, assigned_to
            FROM case_master
            WHERE ack_no = %s
        """, (ack_no,))
        master = cur.fetchone()

        if not master:
            raise HTTPException(status_code=404, detail="Case not found")

        case_id = master[0]

        # Step 2: Get detail using case_id
        cur.execute("""
            SELECT mobile, email, pan, aadhar, card, acct, txn_id, comp_date
            FROM case_detail
            WHERE case_id = %s
        """, (case_id,))
        detail = cur.fetchone()

        cur.close()
        conn.close()

        return {
            "case_id": master[0],
            "ack_no": master[1],
            "match_type": master[2],
            "status": master[3],
            "created_on": master[4],
            "closed_on": master[5],
            "decision": master[6],
            "remarks": master[7],
            "assigned_to": master[8],
            "details": {
                "mobile": detail[0] if detail else None,
                "email": detail[1] if detail else None,
                "pan": detail[2] if detail else None,
                "aadhar": detail[3] if detail else None,
                "card": detail[4] if detail else None,
                "acct": detail[5] if detail else None,
                "txn_id": detail[6] if detail else None,
                "comp_date": detail[7] if detail else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CaseActionRequest(BaseModel):
    case_id: int
    action: str       # "approve", "reject", "assign"
    assigned_to: Optional[str] = None
    remarks: Optional[str] = None

@app.post("/api/case/action")
def case_action(data: CaseActionRequest):
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        if data.action == "approve":
            cur.execute("""
                UPDATE case_master SET status = 'Approved', decision = 'Approved', remarks = %s, closed_on = CURRENT_DATE
                WHERE case_id = %s
            """, (data.remarks or '', data.case_id))
        elif data.action == "reject":
            cur.execute("""
                UPDATE case_master SET status = 'Rejected', decision = 'Rejected', remarks = %s, closed_on = CURRENT_DATE
                WHERE case_id = %s
            """, (data.remarks or '', data.case_id))
        elif data.action == "assign":
            if not data.assigned_to:
                raise HTTPException(status_code=400, detail="assigned_to is required for assignment")
            cur.execute("""
                UPDATE case_master SET status = 'Assigned', assigned_to = %s, remarks = %s
                WHERE case_id = %s
            """, (data.assigned_to, data.remarks or '', data.case_id))
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        conn.commit()
        cur.close()
        conn.close()
        return {"message": f"Case {data.action} successful"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dropdown/status-list")
def get_status_list():
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT status FROM case_master ORDER BY status ASC")
        statuses = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dropdown/assigned-to-list")
def get_assigned_users():
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT assigned_to FROM case_master WHERE assigned_to IS NOT NULL ORDER BY assigned_to ASC")
        users = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Query
from typing import Optional

@app.get("/api/dashboard-cases")
def get_dashboard_cases(user_id: str = Query(...)):
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        cur.execute("""
            SELECT case_id, ack_no, match_type, status, created_on, assigned_to
            FROM case_master
            WHERE
                status = 'New'
                OR (status = 'Assigned' AND assigned_to = %s)
            ORDER BY created_on DESC
        """, (user_id,))

        rows = cur.fetchall()
        cases = [
            {
                "case_id": row[0],
                "ack_no": row[1],
                "match_type": row[2],
                "status": row[3],
                "created_on": row[4],
                "assigned_to": row[5]
            }
            for row in rows
        ]

        cur.close()
        conn.close()
        return {"cases": cases}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class NewCustomer(BaseModel):
    customerId: str
    fullName: str
    aadhar: str
    pan: str
    mobile: str
    dob: str

class NewCustomerRequest(BaseModel):
    customers: List[NewCustomer]

@app.post("/api/screen-new-customers")
def screen_new_customers(payload: NewCustomerRequest):
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    clean_count = 0
    suspicious_count = 0

    for customer in payload.customers:
        matched = False
        matched_fields = []

        # Check in cyber_complaints
        cur.execute("""
            SELECT ack_no FROM cyber_complaints
            WHERE comp_mobile = %s
               OR aadhar = %s
               OR pan = %s
        """, (customer.mobile, customer.aadhar, customer.pan))
        cyber_result = cur.fetchone()
        if cyber_result:
            matched = True
            matched_fields.append("cyber_complaints")

        # Check in suspect_entries
        cur.execute("""
            SELECT id FROM suspect_entries
            WHERE mobile = %s
               OR aadhar = %s
               OR pan = %s
        """, (customer.mobile, customer.aadhar, customer.pan))
        suspect_result = cur.fetchone()
        if suspect_result:
            matched = True
            matched_fields.append("suspect_entries")

        if matched:
            suspicious_count += 1
            cur.execute("""
                INSERT INTO flagged_customers (
                    customer_id, full_name, mobile, aadhar, pan,
                    matched_on, match_type, matched_ack_no
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                customer.customerId, customer.fullName, customer.mobile,
                customer.aadhar, customer.pan,
                customer.fullName, ", ".join(matched_fields),
                cyber_result[0] if cyber_result else None
            ))
            conn.commit()

            print(f"⚠️ [SUSPICIOUS] Customer ID: {customer.customerId}, Name: {customer.fullName}, Match on: {matched_fields}")
        else:
            clean_count += 1
            print(f"✅ [CLEAN] Customer ID: {customer.customerId}, Name: {customer.fullName}")

    cur.close()
    conn.close()

    return {
        "message": f"Screening completed. {clean_count} clean, {suspicious_count} suspicious."
    }

# Define input model
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

@app.post("/api/verify-beneficiary")
def verify_beneficiary(data: BeneficiaryData):
    matched = False
    match_type = "none"
    matched_fields = []

    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    # Match against cyber_complaints (original logic)
    cur.execute("""
        SELECT ack_no, ifsc FROM cyber_complaints
        WHERE suspect_bank_acct = %s
           OR suspect_upi_mobile = %s
           OR comp_email = %s
    """, (data.beneficiaryAccountNumber, data.beneficiaryMobile, data.beneficiaryEmail))
    cyber_result = cur.fetchone()
    if cyber_result:
        matched = True
        cyber_ifsc = cyber_result[1]
        if cyber_ifsc and cyber_ifsc == data.beneficiaryIFSC:
            match_type = "full"
        elif match_type != "full":
            match_type = "partial"
        matched_fields.append("cyber_complaints")

    # Match against suspect_entries (original logic extended)
    cur.execute("""
        SELECT id, ifsc FROM suspect_entries
        WHERE bank_account_number = %s
           OR mobile = %s
           OR email_id = %s
           OR pan = %s
           OR aadhar = %s
           OR upi_id = %s
    """, (
        data.beneficiaryAccountNumber, data.beneficiaryMobile,
        data.beneficiaryEmail, data.beneficiaryPAN,
        data.beneficiaryAadhar, data.beneficiaryUPI
    ))
    suspect_result = cur.fetchone()
    if suspect_result:
        matched = True
        suspect_ifsc = suspect_result[1]
        if suspect_ifsc and suspect_ifsc == data.beneficiaryIFSC:
            match_type = "full"
        elif match_type != "full":
            match_type = "partial"
        matched_fields.append("suspect_entries")

    if matched:
        cur.execute("""
            INSERT INTO flagged_customers (customer_id, full_name, mobile, aadhar, pan,
                                           matched_on, match_type, matched_ack_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.customerId, data.customerName, '', '', '',
            data.beneficiaryName,
            match_type,
            cyber_result[0] if cyber_result else ''
        ))
        conn.commit()

        print(f"⚠️ WARNING: Beneficiary '{data.beneficiaryName}' flagged (matched on {', '.join(matched_fields)}).")

    else:
        print(f"✅ Beneficiary '{data.beneficiaryName}' is clean. No matches found.")

    cur.close()
    conn.close()

    return {
        "status": "processed",
        "matched": matched,
        "match_type": match_type,
        "matched_fields": matched_fields
    }
