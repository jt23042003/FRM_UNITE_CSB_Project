from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Any, Dict, List, Optional, Set
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, validator

from db.connection import get_db_connection, get_db_cursor
from db.matcher import CaseEntryMatcher

router = APIRouter()


def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor


def get_case_matcher_instance(
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)


class PiiRecordPayload(BaseModel):
    record_id: Optional[int] = Field(None, alias="pii_record_id")
    body_mobile_numbers: List[str] = Field(default_factory=list)
    attachment_mobile_numbers: List[str] = Field(default_factory=list)
    body_account_numbers: List[str] = Field(default_factory=list)
    attachment_account_numbers: List[str] = Field(default_factory=list)

    @validator(
        "body_mobile_numbers",
        "attachment_mobile_numbers",
        "body_account_numbers",
        "attachment_account_numbers",
        pre=True,
    )
    def _coerce_list(cls, value):  # type: ignore[override]
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [
                str(item).strip()
                for item in value
                if item is not None and str(item).strip()
            ]
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        return []

    class Config:
        allow_population_by_field_name = True

    def unique_mobiles(self) -> List[str]:
        return list(dict.fromkeys(self.body_mobile_numbers + self.attachment_mobile_numbers))

    @staticmethod
    def _normalize_account(value: str) -> Optional[str]:
        if not value:
            return None
        digits_only = re.sub(r'\D', '', value)
        return digits_only if digits_only else None

    def unique_accounts(self) -> List[str]:
        normalized_accounts: List[str] = []
        seen: Set[str] = set()
        for account in self.body_account_numbers + self.attachment_account_numbers:
            normalized = self._normalize_account(account)
            if normalized and normalized not in seen:
                seen.add(normalized)
                normalized_accounts.append(normalized)
        return normalized_accounts


@router.post("/api/pii/process", tags=["PII Processing"])
async def process_pii_record(
    payload: PiiRecordPayload,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
) -> Dict[str, Any]:
    """
    Trigger PSA/ECB case creation when new PII data (mobiles/accounts) is detected from emails.
    """
    if not payload.unique_mobiles() and not payload.unique_accounts():
        raise HTTPException(status_code=400, detail="No mobile or account numbers provided.")

    results: Dict[str, Any] = {"psa_cases": [], "ecb_cases": []}
    processed_customers: Set[str] = set()

    # Process mobile numbers first
    for mobile in payload.unique_mobiles():
        customer = await _find_customer_by_mobile(matcher, mobile)
        if not customer:
            continue
        cust_id = customer["cust_id"]
        if cust_id in processed_customers:
            continue

        psa_result = await _create_psa_case_from_customer(
            matcher=matcher,
            customer=customer,
            source_detail=f"Mobile {mobile}",
            fallback_account=None,
        )
        if psa_result:
            results["psa_cases"].append(psa_result)

        ecb_result = await matcher._create_ecb_cases_for_customer(
            cust_id=cust_id,
            customer_full_name=_compose_customer_name(customer),
            created_by_user="EmailSystem"
        )
        if ecb_result and ecb_result.get("ecb_cases_created"):
            results["ecb_cases"].append(ecb_result)

        processed_customers.add(cust_id)

    # Process standalone account numbers (mobiles may have already covered some customers)
    for account_number in payload.unique_accounts():
        customer = await _find_customer_by_account(matcher, account_number)
        if not customer:
            continue
        cust_id = customer["cust_id"]
        if cust_id in processed_customers:
            continue

        psa_result = await _create_psa_case_from_customer(
            matcher=matcher,
            customer=customer,
            source_detail=f"Account {account_number}",
            fallback_account=account_number,
        )
        if psa_result:
            results["psa_cases"].append(psa_result)

        ecb_result = await matcher._create_ecb_cases_for_customer(
            cust_id=cust_id,
            customer_full_name=_compose_customer_name(customer),
            created_by_user="EmailSystem"
        )
        if ecb_result and ecb_result.get("ecb_cases_created"):
            results["ecb_cases"].append(ecb_result)

        processed_customers.add(cust_id)

    if not results["psa_cases"] and not results["ecb_cases"]:
        results["message"] = "No matching customers found in core tables."

    return results


async def _find_customer_by_mobile(
    matcher: CaseEntryMatcher, mobile: str
) -> Optional[Dict[str, Any]]:
    mobile_clean = mobile.strip()
    if not mobile_clean:
        return None

    def _sync_lookup():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        cust_id,
                        fname,
                        mname,
                        lname,
                        mobile,
                        email,
                        pan,
                        nat_id AS aadhar
                    FROM customer
                    WHERE mobile = %s
                    LIMIT 1
                    """,
                    (mobile_clean,),
                )
                return cur.fetchone()

    return await matcher._execute_sync_db_op(_sync_lookup)


async def _find_customer_by_account(
    matcher: CaseEntryMatcher, account_number: str
) -> Optional[Dict[str, Any]]:
    account_clean = account_number.strip()
    if not account_clean:
        return None

    def _sync_lookup():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        c.cust_id,
                        c.fname,
                        c.mname,
                        c.lname,
                        c.mobile,
                        c.email,
                        c.pan,
                        c.nat_id AS aadhar
                    FROM account_customer ac
                    JOIN customer c ON c.cust_id = ac.cust_id
                    WHERE ac.acc_num = %s
                    LIMIT 1
                    """,
                    (account_clean,),
                )
                return cur.fetchone()

    return await matcher._execute_sync_db_op(_sync_lookup)


async def _create_psa_case_from_customer(
    matcher: CaseEntryMatcher,
    customer: Dict[str, Any],
    source_detail: str,
    fallback_account: Optional[str],
) -> Optional[Dict[str, Any]]:
    cust_id = customer["cust_id"]
    accounts = await matcher._get_customer_accounts(cust_id)
    account_number = fallback_account
    if accounts:
        account_number = accounts[0].get("acc_num") or account_number

    remarks = (
        f"PSA case auto-created from email ingestion match ({source_detail}) "
        f"for customer {cust_id}."
    )

    return await matcher.create_psa_case_from_email(
        customer_id=cust_id,
        customer_name=_compose_customer_name(customer),
        account_number=account_number,
        mobile_number=customer.get("mobile"),
        remarks=remarks,
        created_by_user="EmailSystem",
    )


def _compose_customer_name(customer: Dict[str, Any]) -> Optional[str]:
    parts = [customer.get("fname"), customer.get("mname"), customer.get("lname")]
    name = " ".join([p for p in parts if p])
    return name.strip() or None

