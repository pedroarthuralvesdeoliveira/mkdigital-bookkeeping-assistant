from __future__ import annotations

from decimal import Decimal
from typing import Dict, Protocol, Tuple

from bookkeeping.domain.models import (
    AccountingDocument,
    BankTransaction,
    Jurisdiction,
    LedgerLine,
    quantize_money,
)


class AccountingRuleStrategy(Protocol):
    def chart_label(self) -> str: ...
    def validate_fiscal_identifiers(self, doc: AccountingDocument) -> Tuple[bool, str]: ...
    def build_ledger_lines(
        self, doc: AccountingDocument, net_amount: Decimal, tax_amount: Decimal
    ) -> Tuple[LedgerLine, ...]: ...


class BankFeedRepository(Protocol):
    def find_by_document_id(self, doc_id: str) -> BankTransaction | None: ...


class SwissKmuStrategy:
    def chart_label(self) -> str:
        return "Swiss Kontenrahmen KMU (OR Art. 957 / MwStG)"

    def validate_fiscal_identifiers(self, doc: AccountingDocument) -> Tuple[bool, str]:
        if not doc.tax_id.startswith("CHE-"):
            return False, f"Invalid Swiss UID '{doc.tax_id}': expected CHE-xxx.xxx.xxx MWST."
        return True, f"Validated Swiss UID ({doc.tax_id}) and QR-IBAN reference ({doc.payment_reference})."

    def build_ledger_lines(
        self, doc: AccountingDocument, net_amount: Decimal, tax_amount: Decimal
    ) -> Tuple[LedgerLine, ...]:
        return (
            LedgerLine(
                account_code="6570",
                account_name="IT-Aufwand & Cloud-Infrastruktur",
                debit=net_amount,
                credit=Decimal("0.00"),
            ),
            LedgerLine(
                account_code="1170",
                account_name=f"Vorsteuer MwSt ({doc.tax_rate_percent}%)",
                debit=tax_amount,
                credit=Decimal("0.00"),
            ),
            LedgerLine(
                account_code="2000",
                account_name="Verbindlichkeiten aus Lieferungen und Leistungen (Kreditoren)",
                debit=Decimal("0.00"),
                credit=doc.gross_amount,
            ),
        )


class BrazilianNfeStrategy:
    def chart_label(self) -> str:
        return "Brazilian Plano de Contas Referencial (SPED / NF-e)"

    def validate_fiscal_identifiers(self, doc: AccountingDocument) -> Tuple[bool, str]:
        digits = "".join(ch for ch in doc.tax_id if ch.isdigit())
        if len(digits) != 14:
            return False, f"Invalid Brazilian CNPJ '{doc.tax_id}': expected 14 digits."
        return True, f"Validated Brazilian CNPJ ({doc.tax_id}) and NF-e key ({doc.payment_reference})."

    def build_ledger_lines(
        self, doc: AccountingDocument, net_amount: Decimal, tax_amount: Decimal
    ) -> Tuple[LedgerLine, ...]:
        return (
            LedgerLine(
                account_code="4.1.02.05",
                account_name="Industrial Instrumentation & Technical Services",
                debit=net_amount,
                credit=Decimal("0.00"),
            ),
            LedgerLine(
                account_code="1.1.05.04",
                account_name=f"Recoverable Taxes — PIS/COFINS/ICMS ({doc.tax_rate_percent}%)",
                debit=tax_amount,
                credit=Decimal("0.00"),
            ),
            LedgerLine(
                account_code="2.1.01.01",
                account_name="Domestic Suppliers Payable (Fornecedores Nacionais)",
                debit=Decimal("0.00"),
                credit=doc.gross_amount,
            ),
        )


STRATEGY_REGISTRY: Dict[Jurisdiction, AccountingRuleStrategy] = {
    Jurisdiction.CH: SwissKmuStrategy(),
    Jurisdiction.BR: BrazilianNfeStrategy(),
}


def compute_tax_split(gross_amount: Decimal, tax_rate_percent: Decimal) -> Tuple[Decimal, Decimal]:
    hundred = Decimal("100.00")
    tax_amount = quantize_money(gross_amount * (tax_rate_percent / (hundred + tax_rate_percent)))
    net_amount = quantize_money(gross_amount - tax_amount)
    return net_amount, tax_amount
