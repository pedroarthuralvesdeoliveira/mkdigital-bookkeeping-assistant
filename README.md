# MKdigital — AI Bookkeeping Assistant (Project A)

[![CI](https://github.com/pedroarthuralvesdeoliveira/mkdigital-bookkeeping-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/pedroarthuralvesdeoliveira/mkdigital-bookkeeping-assistant/actions)

Clean-architecture backend and interactive web simulation for **MKdigital Project A (AI Bookkeeping Assistant — Switzerland 🇨🇭 & Brazil 🇧🇷)**, built by **Pedro Arthur Alves de Oliveira**.

- **🌐 Live Cloudflare URL (Project A):** [https://mkdigital-bookkeeping-assistant.pedroarthuralvesdeoliveira1.workers.dev](https://mkdigital-bookkeeping-assistant.pedroarthuralvesdeoliveira1.workers.dev)
- **🔗 Companion Project B (Plant Brownfield Reconstruction Agent):** [https://mkdigital-plant-brownfield.pedroarthuralvesdeoliveira1.workers.dev](https://mkdigital-plant-brownfield.pedroarthuralvesdeoliveira1.workers.dev) ([GitHub Repo](https://github.com/pedroarthuralvesdeoliveira/mkdigital-plant-brownfield-agent))
- **🤖 Complementary Open-Source LLM Pipeline:** [AI-Contract-Risk-Analysis-Agent](https://github.com/pedroarthuralvesdeoliveira/AI-Contract-Risk-Analysis-Agent)

---

## 🏗️ Software Engineering & Backend Design Principles

- **Clean Architecture & SOLID:**
  - `domain/models.py`: Immutable value objects (`@dataclass(frozen=True)`), fixed-point monetary math (`Decimal` with `ROUND_HALF_UP`), double-entry invariant check ($\sum \text{Debit} = \sum \text{Credit} = \text{Gross}$), and an **explicit state machine** (`INGESTED → EXTRACTED → VALIDATED → LEDGER_POSTED → RECONCILED | FLAGGED_FOR_REVIEW`).
  - `domain/strategies.py`: **Strategy Pattern** (`AccountingRuleStrategy` protocol) isolating Swiss SME rules (`SwissKmuStrategy` — *Kontenrahmen KMU*, UID `CHE-xxx.xxx.xxx MWST`, `Vorsteuer MwSt`) from Brazilian tax rules (`BrazilianNfeStrategy` — *Plano de Contas Referencial*, `CNPJ`, `NF-e`), adhering to the Open/Closed Principle.
  - `application/use_cases.py`: Stateless orchestration (`BookkeepingWorkflowUseCase`) depending solely on domain abstractions (`BankFeedRepository` protocol).
  - `infrastructure/repositories.py` & `api/app.py`: FastAPI adapter with Dependency Injection (`Depends`) and strict Pydantic v2 boundary contracts.
- **UI Palette:** Authentic **MKdigital (`mkdigital.ch`)** design tokens (`#0a0a0a`, `#0f0f0f`, `#161616`, `#222222`, `#ffffff`, `#9c9c9c`, `#70befa`, `Inter Tight`).

## ⚡ Quick Start

```bash
PYTHONPATH=src uv run --with fastapi --with pydantic --with pytest --with httpx pytest -v
PYTHONPATH=src uv run --with fastapi --with pydantic --with uvicorn uvicorn bookkeeping.api.app:app --reload
```
