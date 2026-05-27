# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Agente Guardian** — a perishable product dispatch engine that enforces FEFO (First Expired, First Out) ordering and a security hold on near-expiry batches, with an optional AI-powered test generation layer via LangChain + Ollama.

## Commands

```bash
# Run all tests
pytest tests/

# Run a single test file or test
pytest tests/test_engine.py
pytest tests/test_engine.py::test_fefo_order -v

# Run with JSON reporting (matches pytest.ini config)
pytest tests/ --json-report --json-report-file=reports/test_report.json -v

# Run AI test generator (requires local Ollama with llama3:8b)
python guardian/agent.py

# Run tests inside Docker sandbox (requires guardian-sandbox image)
python guardian/sandbox.py
```

## Architecture

### Core Layers

**`domain/`** — Data contracts and exceptions only; no business logic.
- `models.py`: `Lote` and `ResultadoDespacho` as `TypedDict`s (ISO 8601 dates, int stock)
- `exceptions.py`: `FechaInvalidaError`, `StockInsuficienteError`, `LoteInvalidoError`

**`engine.py`** — Single public function `gestionar_despacho(inventario, pedido_cliente, fecha_sistema)` implements all dispatch logic:
1. Validates `fecha_sistema` format and `pedido_cliente ≥ 0`
2. Filters batches where `(fecha_vencimiento - fecha_sistema) > DIAS_BLOQUEO_SEGURIDAD` (3 days)
3. Sorts eligible batches by expiration date ascending (FEFO; ISO dates sort lexicographically)
4. Checks accumulated eligible stock covers the order; raises `StockInsuficienteError` otherwise
5. Consumes batches in order, returning a list of `ResultadoDespacho` dicts

**`guardian/`** — Optional AI layer; not part of the core dispatch logic.
- `agent.py`: Reads source + test case matrix, calls Ollama (llama3:8b) via LangChain, writes `test_generated.py`
- `sandbox.py`: Runs pytest inside a Docker container (`guardian-sandbox` image), returns `"APROBADO"` or `"RECHAZADO"`

### Public API (`__init__.py`)

```python
from . import gestionar_despacho, Lote, ResultadoDespacho
from . import FechaInvalidaError, StockInsuficienteError, LoteInvalidoError
```

### Key Constant

`DIAS_BLOQUEO_SEGURIDAD = 3` in `engine.py` — the security hold threshold in days.

## Test Cases

`casos_prueba.md` at the repo root documents 10 canonical scenarios (TC-01 through TC-10) covering FEFO ordering, security-hold boundaries (exact 3-day edge, 1-day-to-expiry), insufficient stock, empty inventory, and multi-batch distributions. These are the reference specs for any changes to dispatch logic.

## Conventions

- Business logic docs and exception messages are in **Spanish**.
- Dates are always ISO 8601 (`YYYY-MM-DD`); lexicographic sort equals chronological sort, so no `datetime` conversion is needed for ordering.
- Exception messages follow the pattern `[ExceptionType] descriptive message with context`.
- `TypedDict` is preferred over dataclasses/Pydantic for domain models to stay JSON-native.
