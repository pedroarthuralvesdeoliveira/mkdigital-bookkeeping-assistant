from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from bookkeeping.application.use_cases import BookkeepingWorkflowUseCase
from bookkeeping.domain.models import (
    AccountingDocument,
    Currency,
    DocumentState,
    Jurisdiction,
)
from bookkeeping.infrastructure.repositories import InMemoryBankFeedRepository

app = FastAPI(
    title="MKdigital — AI Bookkeeping Assistant API",
    description="Clean-architecture backend service for Swiss (CH) and Brazilian (BR) automated bookkeeping.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AccountingDocumentRequest(BaseModel):
    doc_id: str = Field(..., min_length=3)
    jurisdiction: Jurisdiction
    vendor_name: str
    tax_id: str
    issue_date: date
    currency: Currency
    gross_amount: Decimal = Field(..., gt=Decimal("0.00"))
    tax_rate_percent: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    description: str
    payment_reference: str
    extraction_confidence: Decimal = Field(default=Decimal("0.98"), ge=Decimal("0.00"), le=Decimal("1.00"))


class LedgerLineResponse(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


class ReconciliationResponse(BaseModel):
    doc_id: str
    jurisdiction: Jurisdiction
    currency: Currency
    state: DocumentState
    state_history: List[DocumentState]
    net_amount: Decimal
    tax_amount: Decimal
    gross_amount: Decimal
    chart_of_accounts_label: str
    ledger_lines: List[LedgerLineResponse]
    matched_bank_tx_id: Optional[str]
    audit_log: List[str]


def get_use_case() -> BookkeepingWorkflowUseCase:
    return BookkeepingWorkflowUseCase(bank_repository=InMemoryBankFeedRepository())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "mkdigital-bookkeeping-assistant"}


@app.post("/api/v1/bookkeeping/reconcile", response_model=ReconciliationResponse)
def reconcile(
    payload: AccountingDocumentRequest,
    use_case: BookkeepingWorkflowUseCase = Depends(get_use_case),
) -> ReconciliationResponse:
    domain_doc = AccountingDocument(
        doc_id=payload.doc_id,
        jurisdiction=payload.jurisdiction,
        vendor_name=payload.vendor_name,
        tax_id=payload.tax_id,
        issue_date=payload.issue_date,
        currency=payload.currency,
        gross_amount=payload.gross_amount,
        tax_rate_percent=payload.tax_rate_percent,
        description=payload.description,
        payment_reference=payload.payment_reference,
        extraction_confidence=payload.extraction_confidence,
    )
    report = use_case.execute(domain_doc)
    return ReconciliationResponse(
        doc_id=report.doc_id,
        jurisdiction=report.jurisdiction,
        currency=report.currency,
        state=report.state,
        state_history=list(report.state_history),
        net_amount=report.net_amount,
        tax_amount=report.tax_amount,
        gross_amount=report.gross_amount,
        chart_of_accounts_label=report.chart_of_accounts_label,
        ledger_lines=[
            LedgerLineResponse(
                account_code=line.account_code,
                account_name=line.account_name,
                debit=line.debit,
                credit=line.credit,
            )
            for line in report.ledger_lines
        ],
        matched_bank_tx_id=report.matched_bank_tx_id,
        audit_log=list(report.audit_log),
    )
