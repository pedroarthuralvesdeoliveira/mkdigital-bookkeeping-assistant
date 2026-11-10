from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from bookkeeping.api.app import app
from bookkeeping.domain.models import (
    DocumentState,
    InvalidStateTransitionError,
    transition_state,
)

client = TestClient(app)


def test_explicit_state_machine_blocks_invalid_transition() -> None:
    with pytest.raises(InvalidStateTransitionError):
        transition_state(DocumentState.INGESTED, DocumentState.RECONCILED)


def test_swiss_qr_bill_reconciles_with_exact_decimal_invariants() -> None:
    payload = {
        "doc_id": "CH-INV-2026-089",
        "jurisdiction": "CH",
        "vendor_name": "AlpenCloud AG Zurich",
        "tax_id": "CHE-114.829.301 MWST",
        "issue_date": "2026-11-05",
        "currency": "CHF",
        "gross_amount": "3783.50",
        "tax_rate_percent": "8.10",
        "description": "Autonomous AI GPU Inference Cluster",
        "payment_reference": "CH44 3199 9123 0008 8901 2",
        "extraction_confidence": "0.99",
    }
    response = client.post("/api/v1/bookkeeping/reconcile", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "RECONCILED"
    assert body["state_history"] == [
        "INGESTED",
        "EXTRACTED",
        "VALIDATED",
        "LEDGER_POSTED",
        "RECONCILED",
    ]
    total_debit = sum(Decimal(line["debit"]) for line in body["ledger_lines"])
    total_credit = sum(Decimal(line["credit"]) for line in body["ledger_lines"])
    assert total_debit == total_credit == Decimal("3783.50")


def test_brazilian_nfe_flags_unmatched_bank_settlement() -> None:
    payload = {
        "doc_id": "BR-NFE-2026-999",
        "jurisdiction": "BR",
        "vendor_name": "Instrumentacao Industrial Sul Ltda",
        "tax_id": "14.782.910/0001-55",
        "issue_date": str(date(2026, 11, 8)),
        "currency": "BRL",
        "gross_amount": "9500.00",
        "tax_rate_percent": "14.25",
        "description": "Industrial pressure transmitters",
        "payment_reference": "412611147829100001555500100000099910",
    }
    response = client.post("/api/v1/bookkeeping/reconcile", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "FLAGGED_FOR_REVIEW"
    assert body["matched_bank_tx_id"] is None
