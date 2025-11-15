# app/core/fight_manager.py
from typing import List, Optional, Callable, Sequence, Tuple
import time
import re

import duckdb
import pandas as pd

from app.db.duckdb_init import seed_random_data
from app.agents.base_agent import SQLAgent
from app.models.fight_log import AgentTurn
from app.utils.sql_safety import is_select_only
from app.core.scoring import complexity_score
from app.config import settings


def introspect_schema(conn: duckdb.DuckDBPyConnection) -> str:
    """
    Return a text description of tables and columns for the agents.
    """
    rows = conn.execute(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """
    ).fetchall()

    lines: List[str] = []
    current_table: Optional[str] = None
    for table_name, col_name, data_type in rows:
        if table_name != current_table:
            current_table = table_name
            lines.append(f"\nTABLE {table_name}:")
        lines.append(f"  - {col_name} ({data_type})")
    return "\n".join(lines)


def _theme_prompt(theme: str) -> str:
    theme = theme.lower().strip()
    if theme == "finance bros":
        return (
            "Make an absurd finance-style query referencing salaries, bonuses, "
            "offshore accounts, and suspicious transactions."
        )
    if theme == "space pirates":
        return (
            "Make a chaotic, space-pirate themed query about stolen goods, "
            "illegal trades, and intergalactic bounties."
        )
    if theme == "healthcare":
        return (
            "Make a healthcare-flavored query about patients, treatments, "
            "billing, and questionable procedures."
        )
    if theme == "gaming":
        return (
            "Make a gaming-style query about players, scores, loot drops, "
            "and ridiculous achievements."
        )
    if theme == "fantasy kingdom":
        return (
            "Make a fantasy kingdom query involving dragons, gold, quests, "
            "and wildly unbalanced magic items."
        )
    # default chaos
    return (
        "Write an absurd, theatrical SQL query that surfaces the 'weirdest' "
        "things in the data."
    )


def _difficulty_prompt(difficulty: str) -> str:
    difficulty = difficulty.lower().strip()
    if difficulty == "tryhard":
        return (
            "Use at least one JOIN, GROUP BY, and a CASE expression to make it more complex."
        )
    if difficulty == "insane window functions":
        return (
            "Use multiple JOINs, nested subqueries, CTEs, and window functions "
            "to make the query hilariously overengineered."
        )
    # Chill
    return (
        "Keep it relatively simple but still weird. One or two joins max, "
        "no need for heavy window functions."
    )


def _estimate_tokens(text: str) -> int:
    """
    Very rough token estimate based on character length.
    This is just for display, not billing accuracy.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def _sanitize_table_name(name: str) -> str:
    """
    Make a DuckDB-safe table name from user input.
    """
    name = name.strip()
    if not name:
        return "user_table"
    name = name.lower().replace(" ", "_")
    name = "".join(ch for ch in name if ch.isalnum() or ch == "_")
    if not name:
        name = "user_table"
    if name[0].isdigit():
        name = f"t_{name}"
    return name


class FightManager:
    def __init__(
        self,
        agent_a: SQLAgent,
        agent_b: SQLAgent,
        rounds: int | None = None,
        n_rows: int = 200,
        weirdness: float = 1.0,
        rng_seed: int = 42,
        extra_tables: Optional[Sequence[Tuple[str, pd.DataFrame]]] = None,
    ):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.rounds = rounds or settings.fight_rounds_default

        # Seed base random data
        self.conn = seed_random_data(
            n_rows=n_rows,
            weirdness=weirdness,
            rng_seed=rng_seed,
        )

        # Attach extra user-provided tables (from uploaded CSVs)
        self.extra_table_names: List[str] = []
        if extra_tables:
            for raw_name, df in extra_tables:
                table_name = _sanitize_table_name(raw_name)
                tmp_name = f"{table_name}_df"
                # Register and create a proper table
                self.conn.register(tmp_name, df)
                self.conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {tmp_name};"
                )
                self.extra_table_names.append(table_name)

        # After all tables exist, introspect schema
        self.schema_description = introspect_schema(self.conn)
        self.turns: List[AgentTurn] = []

    def _summarize_result(self, rows_preview: list[dict]) -> str:
        if not rows_preview:
            return "No rows returned."
        return (
            f"{len(rows_preview)} rows previewed; "
            f"first row keys: {list(rows_preview[0].keys())}"
        )

    def run_fight(
        self,
        mode: str = "ai_vs_ai",  # "ai_vs_ai" or "you_vs_ai"
        human_sqls: Optional[List[str]] = None,
        theme: str = "Default chaos",
        difficulty: str = "Chill",
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> List[AgentTurn]:
        """
        Run the fight for the configured number of rounds.

        mode:
            - "ai_vs_ai": both agents are LLMs.
            - "you_vs_ai": Agent A is the human, Agent B is the LLM.
              In this mode, human_sqls must be a list of SQL strings
              with length == rounds // 2.

        human_sqls:
            Used only in "you_vs_ai" mode. One SQL string for each of
            the human's turns (Agent A).

        theme, difficulty:
            Used to build the base challenge text for the agents.

        on_progress:
            Optional callback called as:
                on_progress(current_round, total_rounds)
        """
        theme_text = _theme_prompt(theme)
        difficulty_text = _difficulty_prompt(difficulty)
        base_challenge = f"{theme_text} {difficulty_text}"

        previous_query: Optional[str] = None
        previous_result_summary: Optional[str] = None
        challenge = base_challenge

        current_agent: SQLAgent = self.agent_a
        human_turn_index = 0

        # Basic validation for human mode
        if mode == "you_vs_ai":
            expected_human_turns = self.rounds // 2
            if not human_sqls or len(human_sqls) != expected_human_turns:
                raise ValueError(
                    f"Expected {expected_human_turns} human SQL queries, "
                    f"but got {0 if not human_sqls else len(human_sqls)}."
                )

        for round_num in range(1, self.rounds + 1):
            start_time = time.perf_counter()

            # Decide how to get SQL for this turn
            if mode == "you_vs_ai" and current_agent is self.agent_a:
                # Human turn
                sql = human_sqls[human_turn_index]
                human_turn_index += 1
                estimated_tokens = 0
            else:
                # AI turn
                sql = current_agent.generate_sql(
                    schema=self.schema_description,
                    previous_query=previous_query,
                    previous_result_summary=previous_result_summary,
                    challenge=challenge,
                )
                estimated_tokens = _estimate_tokens(sql)

            valid = is_select_only(sql)
            error: Optional[str] = None
            rows_preview: Optional[list[dict]] = None

            if not valid:
                error = "Rejected: query is not SELECT-only or contains forbidden keywords."
            else:
                try:
                    result = self.conn.execute(sql)
                    rows = result.fetchmany(settings.max_rows_preview)
                    col_names = (
                        [d[0] for d in result.description] if result.description else []
                    )
                    rows_preview = [dict(zip(col_names, row)) for row in rows]
                except Exception as e:
                    error = str(e)

            duration = time.perf_counter() - start_time
            score = complexity_score(sql)

            turn = AgentTurn(
                round_number=round_num,
                agent_name=current_agent.name,
                prompt=challenge,
                sql=sql,
                is_valid_sql=valid and error is None,
                error=error,
                rows_preview=rows_preview,
                complexity_score=score,
                duration_seconds=duration,
                estimated_tokens=estimated_tokens,
            )
            self.turns.append(turn)

            # Prepare inputs for the next turn
            previous_query = sql
            previous_result_summary = self._summarize_result(rows_preview or [])
            challenge = (
                f"Building on the previous query and result, stay in the '{theme}' theme. "
                f"{difficulty_text} Make it even more outrageous and complex than before."
            )

            # Notify caller of progress
            if on_progress is not None:
                on_progress(round_num, self.rounds)

            # Swap agents
            current_agent = (
                self.agent_b if current_agent is self.agent_a else self.agent_a
            )

        return self.turns
