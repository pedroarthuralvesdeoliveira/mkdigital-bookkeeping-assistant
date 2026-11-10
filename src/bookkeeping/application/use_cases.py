from __future__ import annotations

from typing import List

from bookkeeping.domain.models import (
    AccountingDocument,
    DocumentState,
    ReconciliationReport,
    transition_state,
)
from bookkeeping.domain.strategies import (
    BankFeedRepository,
    STRATEGY_REGISTRY,
    compute_tax_split,
)


class BookkeepingWorkflowUseCase:
    def __init__(self, bank_repository: BankFeedRepository) -> None:
        self._bank_repository = bank_repository

    def execute(self, doc: AccountingDocument) -> ReconciliationReport:
        state = DocumentState.INGESTED
        history: List[DocumentState] = [state]
        audit_log: List[str] = []

        state = transition_state(state, DocumentState.EXTRACTED)
        history.append(state)
        audit_log.append(
            f"Document {doc.doc_id} extracted with confidence {doc.extraction_confidence}."
        )

        strategy = STRATEGY_REGISTRY[doc.jurisdiction]
        is_valid_id, id_message = strategy.validate_fiscal_identifiers(doc)
        audit_log.append(id_message)

        net_amount, tax_amount = compute_tax_split(doc.gross_amount, doc.tax_rate_percent)
        ledger_lines = strategy.build_ledger_lines(doc, net_amount, tax_amount)

        if not is_valid_id:
            state = transition_state(state, DocumentState.FLAGGED_FOR_REVIEW)
            history.append(state)
            return ReconciliationReport(
                doc_id=doc.doc_id,
                jurisdiction=doc.jurisdiction,
                currency=doc.currency,
                state=state,
                state_history=tuple(history),
                net_amount=net_amount,
                tax_amount=tax_amount,
                gross_amount=doc.gross_amount,
                chart_of_accounts_label=strategy.chart_label(),
                ledger_lines=ledger_lines,
                matched_bank_tx_id=None,
                audit_log=tuple(audit_log),
            )

        state = transition_state(state, DocumentState.VALIDATED)
        history.append(state)

        state = transition_state(state, DocumentState.LEDGER_POSTED)
        history.append(state)
        audit_log.append(
            f"Posted balanced double-entry lines ({doc.currency} {doc.gross_amount})."
        )

        bank_tx = self._bank_repository.find_by_document_id(doc.doc_id)
        if bank_tx and bank_tx.currency == doc.currency and bank_tx.amount == doc.gross_amount:
            state = transition_state(state, DocumentState.RECONCILED)
            history.append(state)
            matched_id = bank_tx.bank_tx_id
            audit_log.append(
                f"Reconciled against bank feed {bank_tx.bank_tx_id} ({bank_tx.bank_name})."
            )
        else:
            state = transition_state(state, DocumentState.FLAGGED_FOR_REVIEW)
            history.append(state)
            matched_id = None
            audit_log.append(
                "Bank feed amount mismatch or missing settlement; routed to manual review queue."
            )

        return ReconciliationReport(
            doc_id=doc.doc_id,
            jurisdiction=doc.jurisdiction,
            currency=doc.currency,
            state=state,
            state_history=tuple(history),
            net_amount=net_amount,
            tax_amount=tax_amount,
            gross_amount=doc.gross_amount,
            chart_of_accounts_label=strategy.chart_label(),
            ledger_lines=ledger_lines,
            matched_bank_tx_id=matched_id,
            audit_log=tuple(audit_log),
        )
