from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Dict, FrozenSet, Tuple


class Jurisdiction(StrEnum):
    CH = "CH"
    BR = "BR"


class Currency(StrEnum):
    CHF = "CHF"
    EUR = "EUR"
    BRL = "BRL"


class DocumentState(StrEnum):
    INGESTED = "INGESTED"
    EXTRACTED = "EXTRACTED"
    VALIDATED = "VALIDATED"
    LEDGER_POSTED = "LEDGER_POSTED"
    RECONCILED = "RECONCILED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"


ALLOWED_TRANSITIONS: Dict[DocumentState, FrozenSet[DocumentState]] = {
    DocumentState.INGESTED: frozenset({DocumentState.EXTRACTED}),
    DocumentState.EXTRACTED: frozenset({DocumentState.VALIDATED, DocumentState.FLAGGED_FOR_REVIEW}),
    DocumentState.VALIDATED: frozenset({DocumentState.LEDGER_POSTED}),
    DocumentState.LEDGER_POSTED: frozenset({DocumentState.RECONCILED, DocumentState.FLAGGED_FOR_REVIEW}),
    DocumentState.RECONCILED: frozenset(),
    DocumentState.FLAGGED_FOR_REVIEW: frozenset({DocumentState.VALIDATED}),
}


class InvalidStateTransitionError(ValueError):
    pass


def transition_state(current: DocumentState, target: DocumentState) -> DocumentState:
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Explicit state machine violation: cannot transition from {current} to {target}."
        )
    return target


def quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class AccountingDocument:
    doc_id: str
    jurisdiction: Jurisdiction
    vendor_name: str
    tax_id: str
    issue_date: date
    currency: Currency
    gross_amount: Decimal
    tax_rate_percent: Decimal
    description: str
    payment_reference: str
    extraction_confidence: Decimal


@dataclass(frozen=True)
class LedgerLine:
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


@dataclass(frozen=True)
class BankTransaction:
    bank_tx_id: str
    bank_name: str
    booking_date: date
    currency: Currency
    amount: Decimal
    reference: str


@dataclass(frozen=True)
class ReconciliationReport:
    doc_id: str
    jurisdiction: Jurisdiction
    currency: Currency
    state: DocumentState
    state_history: Tuple[DocumentState, ...]
    net_amount: Decimal
    tax_amount: Decimal
    gross_amount: Decimal
    chart_of_accounts_label: str
    ledger_lines: Tuple[LedgerLine, ...]
    matched_bank_tx_id: str | None
    audit_log: Tuple[str, ...]

    def __post_init__(self) -> None:
        total_debit = sum((line.debit for line in self.ledger_lines), Decimal("0.00"))
        total_credit = sum((line.credit for line in self.ledger_lines), Decimal("0.00"))
        if total_debit != total_credit or total_debit != self.gross_amount:
            raise ValueError(
                f"Double-entry invariant violated: debit={total_debit}, credit={total_credit}, gross={self.gross_amount}"
            )
