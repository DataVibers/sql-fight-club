# app/models/fight_log.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentTurn:
    round_number: int
    agent_name: str
    prompt: str
    sql: str
    is_valid_sql: bool
    error: Optional[str]
    rows_preview: Optional[list[dict]]  # list of dicts for JSON-ish preview
    complexity_score: float
    duration_seconds: float
    estimated_tokens: Optional[int] = None
