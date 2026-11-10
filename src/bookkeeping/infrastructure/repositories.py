from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict

from bookkeeping.domain.models import BankTransaction, Currency


class InMemoryBankFeedRepository:
    def __init__(self) -> None:
        self._transactions: Dict[str, BankTransaction] = {
            "CH-INV-2026-089": BankTransaction(
                bank_tx_id="UBS-CAMT053-99412",
                bank_name="UBS Switzerland AG (camt.053 ISO 20022)",
                booking_date=date(2026, 11, 6),
                currency=Currency.CHF,
                amount=Decimal("3783.50"),
                reference="RF48 2026 0890 0012",
            ),
            "BR-NFE-2026-441": BankTransaction(
                bank_tx_id="ITAU-CNAB240-77821",
                bank_name="Itau Unibanco S.A. (CNAB 240 API)",
                booking_date=date(2026, 11, 5),
                currency=Currency.BRL,
                amount=Decimal("14850.00"),
                reference="NFE-441-AUTOMACAO",
            ),
        }

    def find_by_document_id(self, doc_id: str) -> BankTransaction | None:
        return self._transactions.get(doc_id)
