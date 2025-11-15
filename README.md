# SQL Fight Club (AI vs AI)

Two unhinged SQL agents battle inside a DuckDB database, trying to one-up each other with increasingly absurd queries.  
They only speak SQL. You watch the chaos in real time.

> “The App Nobody Asked For” – but you’ll stare at it anyway.

---

## 1. Features (MVP)

- 🧠 **Two AI SQL agents** that only communicate in SQL
- 🦆 **DuckDB** as the in-process analytics engine
- ⚔️ **Fight rounds**: agents take turns writing more complex / bizarre SELECT queries
- 📊 **Live UI** (Streamlit) showing:
  - SQL for each round
  - Result preview (top N rows)
  - Errors (if queries explode)
  - A silly “complexity score”
- 🚧 **Safety**: read-only SQL (SELECT only), timeouts, simple query validation

---

## 2. Architecture Overview

- `DuckDB` is created **in-memory** and populated with random but structured data.
- `Agent` = an LLM prompt template that:
  - Receives: schema, previous query, previous result summary, and current “challenge”
  - Outputs: **SQL only**, constrained to SELECT statements.
- `Fight Orchestrator`:
  - Manages rounds between Agent A and Agent B
  - Executes queries against DuckDB
  - Stores logs in memory (and optionally in a `fight_logs` table)
- `Streamlit UI`:
  - “Start Fight” button
  - Configurable: number of rounds, random seed, data size
  - Shows fight as a timeline

---

## 3. Prerequisites

- **Git** installed
- **Python** 3.11+ installed
- **Docker** (optional but recommended)
- An **OpenAI API key** (or compatible provider)

Create an OpenAI API key and keep it safe.

---

## Environment Setup

To set up your local development environment, follow:

👉 [Environment Setup Guide](./ENVIRONMENT_SETUP.md)

---

## 4. Project Structure (proposed)

```bash
sql-fight-club/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ duckdb_init.py       # create DuckDB connection + seed random data
│  ├─ agents/
│  │  ├─ __init__.py
│  │  ├─ base_agent.py        # SQLAgent base class
│  │  ├─ openai_agent.py      # OpenAI-based implementation
│  ├─ core/
│  │  ├─ fight_manager.py     # orchestrates rounds & scoring
│  │  ├─ scoring.py           # query complexity / fun score
│  ├─ ui/
│  │  ├─ streamlit_app.py     # Streamlit entrypoint
│  ├─ models/
│  │  ├─ fight_log.py         # Pydantic models / dataclasses
│  └─ utils/
│     ├─ sql_safety.py        # SELECT-only checks, timeouts, etc.
├─ tests/
│  ├─ test_duckdb_init.py
│  ├─ test_sql_safety.py
├─ .env.example
├─ .gitignore
├─ Dockerfile
├─ requirements.txt
└─ README.md
