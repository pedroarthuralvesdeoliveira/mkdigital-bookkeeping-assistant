const SCENARIOS = [
  {
    doc_id: "CH-INV-2026-089",
    label: "🇨🇭 Switzerland · QR-Bill (AlpenCloud AG — CHF 3,783.50 · Reconciled)",
    jurisdiction: "CH",
    vendor_name: "AlpenCloud AG Zürich",
    tax_id: "CHE-114.829.301 MWST",
    issue_date: "2026-11-05",
    currency: "CHF",
    gross_amount: 3783.50,
    tax_rate_percent: 8.10,
    payment_reference: "CH44 3199 9123 0008 8901 2",
    confidence: "99.1%",
    state: "RECONCILED",
    state_history: ["INGESTED", "EXTRACTED", "VALIDATED", "LEDGER_POSTED", "RECONCILED"],
    chart_label: "Swiss Kontenrahmen KMU (OR Art. 957 / MwStG)",
    bank_tx: {
      bank_tx_id: "UBS-CAMT053-99412",
      bank_name: "UBS Switzerland AG (camt.053 ISO 20022)",
      booking_date: "2026-11-06",
      amount: 3783.50
    }
  },
  {
    doc_id: "BR-NFE-2026-441",
    label: "🇧🇷 Brazil · NF-e 441 (Sensores Industriais Sul — BRL 14,850.00 · Reconciled)",
    jurisdiction: "BR",
    vendor_name: "Sensores & Instrumentacao Sul Ltda",
    tax_id: "14.782.910/0001-55",
    issue_date: "2026-11-04",
    currency: "BRL",
    gross_amount: 14850.00,
    tax_rate_percent: 14.25,
    payment_reference: "NF-e Key: 4126 1114 7829 1000 0155 5500 1000 0004 4119",
    confidence: "98.4%",
    state: "RECONCILED",
    state_history: ["INGESTED", "EXTRACTED", "VALIDATED", "LEDGER_POSTED", "RECONCILED"],
    chart_label: "Brazilian Plano de Contas Referencial (SPED / NF-e)",
    bank_tx: {
      bank_tx_id: "ITAU-CNAB240-77821",
      bank_name: "Itau Unibanco S.A. (CNAB 240 API)",
      booking_date: "2026-11-05",
      amount: 14850.00
    }
  },
  {
    doc_id: "CH-INV-2026-104-DIFF",
    label: "🇨🇭 Switzerland · QR-Bill w/ Bank Settlement Mismatch (Helvetia CAD GmbH — CHF 2,162.00)",
    jurisdiction: "CH",
    vendor_name: "Helvetia CAD & Scanning GmbH",
    tax_id: "CHE-392.104.772 MWST",
    issue_date: "2026-11-07",
    currency: "CHF",
    gross_amount: 2162.00,
    tax_rate_percent: 8.10,
    payment_reference: "CH93 0076 2011 6238 5295 7",
    confidence: "96.8%",
    state: "FLAGGED_FOR_REVIEW",
    state_history: ["INGESTED", "EXTRACTED", "VALIDATED", "LEDGER_POSTED", "FLAGGED_FOR_REVIEW"],
    chart_label: "Swiss Kontenrahmen KMU (OR Art. 957 / MwStG)",
    bank_tx: {
      bank_tx_id: "ZKB-CAMT053-31004",
      bank_name: "Zurcher Kantonalbank (camt.053)",
      booking_date: "2026-11-08",
      amount: 2000.00
    }
  }
];

function formatAmount(val, currency) {
  return `${currency} ${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function renderScenario(index) {
  const item = SCENARIOS[index];
  const taxAmount = +(item.gross_amount * (item.tax_rate_percent / (100 + item.tax_rate_percent))).toFixed(2);
  const netAmount = +(item.gross_amount - taxAmount).toFixed(2);

  document.getElementById("bk-confidence").textContent = `Confidence: ${item.confidence}`;

  const stepsContainer = document.getElementById("state-steps");
  stepsContainer.innerHTML = item.state_history
    .map((st, idx) => {
      const isLast = idx === item.state_history.length - 1;
      const cls = isLast && st === "FLAGGED_FOR_REVIEW" ? "state-pill warn" : "state-pill active";
      const arrow = idx < item.state_history.length - 1 ? `<span style="color:#9c9c9c">→</span>` : "";
      return `<span class="${cls}">${st}</span>${arrow}`;
    })
    .join("");

  document.getElementById("bk-doc-preview").innerHTML = `
    <div class="kv-row"><span class="kv-label">Document ID</span><span class="kv-val"><code>${item.doc_id}</code></span></div>
    <div class="kv-row"><span class="kv-label">Jurisdiction</span><span class="kv-val">${item.jurisdiction === "CH" ? "Switzerland (CH)" : "Brazil (BR)"}</span></div>
    <div class="kv-row"><span class="kv-label">Vendor</span><span class="kv-val">${item.vendor_name}</span></div>
    <div class="kv-row"><span class="kv-label">Tax Identifier</span><span class="kv-val">${item.tax_id}</span></div>
    <div class="kv-row"><span class="kv-label">Issue Date</span><span class="kv-val">${item.issue_date}</span></div>
    <div class="kv-row"><span class="kv-label">Gross Amount</span><span class="kv-val">${formatAmount(item.gross_amount, item.currency)}</span></div>
    <div class="kv-row"><span class="kv-label">Tax Rate</span><span class="kv-val">${item.tax_rate_percent}% (${formatAmount(taxAmount, item.currency)})</span></div>
    <div class="kv-row"><span class="kv-label">Reference</span><span class="kv-val">${item.payment_reference}</span></div>
  `;

  document.getElementById("bk-category").textContent = item.chart_label;

  const lines =
    item.jurisdiction === "CH"
      ? [
          { code: "6570", name: "IT-Aufwand & Cloud-Infrastruktur", debit: netAmount, credit: 0 },
          { code: "1170", name: `Vorsteuer MwSt (${item.tax_rate_percent}%)`, debit: taxAmount, credit: 0 },
          { code: "2000", name: "Verbindlichkeiten (Kreditoren)", debit: 0, credit: item.gross_amount }
        ]
      : [
          { code: "4.1.02.05", name: "Industrial Instrumentation & Technical Services", debit: netAmount, credit: 0 },
          { code: "1.1.05.04", name: `Recoverable Taxes (${item.tax_rate_percent}%)`, debit: taxAmount, credit: 0 },
          { code: "2.1.01.01", name: "Domestic Suppliers Payable", debit: 0, credit: item.gross_amount }
        ];

  document.querySelector("#bk-ledger-table tbody").innerHTML = lines
    .map(
      (line) => `
      <tr>
        <td><code>${line.code}</code></td>
        <td>${line.name}</td>
        <td class="num">${line.debit ? formatAmount(line.debit, item.currency) : "—"}</td>
        <td class="num">${line.credit ? formatAmount(line.credit, item.currency) : "—"}</td>
      </tr>
    `
    )
    .join("");

  document.querySelector("#bk-ledger-table tfoot").innerHTML = `
    <tr>
      <td colspan="2">Balanced Double-Entry Total</td>
      <td class="num">${formatAmount(item.gross_amount, item.currency)}</td>
      <td class="num">${formatAmount(item.gross_amount, item.currency)}</td>
    </tr>
  `;

  const diff = Math.abs(item.bank_tx.amount - item.gross_amount);
  const badge = document.getElementById("bk-match-badge");
  if (item.state === "RECONCILED") {
    badge.className = "pill pill-green";
    badge.textContent = "RECONCILED";
  } else {
    badge.className = "pill pill-red";
    badge.textContent = "FLAGGED_FOR_REVIEW";
  }

  document.getElementById("bk-bank-box").innerHTML = `
    <div class="kv-row"><span class="kv-label">Bank Transaction ID</span><span class="kv-val"><code>${item.bank_tx.bank_tx_id}</code></span></div>
    <div class="kv-row"><span class="kv-label">Feed Source</span><span class="kv-val">${item.bank_tx.bank_name}</span></div>
    <div class="kv-row"><span class="kv-label">Settlement Date</span><span class="kv-val">${item.bank_tx.booking_date}</span></div>
    <div class="kv-row"><span class="kv-label">Settled Amount</span><span class="kv-val">${formatAmount(item.bank_tx.amount, item.currency)}</span></div>
    <div class="kv-row"><span class="kv-label">Variance</span><span class="kv-val">${formatAmount(diff, item.currency)}</span></div>
  `;

  const logs = [
    `Document ${item.doc_id} transitioned INGESTED → EXTRACTED → VALIDATED → LEDGER_POSTED.`,
    item.jurisdiction === "CH"
      ? `Validated Swiss UID (${item.tax_id}) and QR-IBAN reference.`
      : `Validated Brazilian CNPJ (${item.tax_id}) and 44-digit NF-e key.`,
    item.state === "RECONCILED"
      ? `Exact match with bank transaction ${item.bank_tx.bank_tx_id}; state transitioned to RECONCILED.`
      : `Variance of ${formatAmount(diff, item.currency)} against ${item.bank_tx.bank_tx_id}; transitioned to FLAGGED_FOR_REVIEW.`
  ];
  document.getElementById("bk-notes-list").innerHTML = logs.map((l) => `<li>${l}</li>`).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("doc-selector");
  select.innerHTML = SCENARIOS.map((s, idx) => `<option value="${idx}">${s.label}</option>`).join("");
  select.addEventListener("change", () => renderScenario(Number(select.value)));
  document.getElementById("btn-next").addEventListener("click", () => {
    const next = (Number(select.value) + 1) % SCENARIOS.length;
    select.value = String(next);
    renderScenario(next);
  });
  renderScenario(0);
});
