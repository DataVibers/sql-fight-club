# app/ui/streamlit_app.py

import streamlit as st
from openai import OpenAI
import pandas as pd

from app.agents.openai_agent import OpenAISQLAgent
from app.core.fight_manager import FightManager
from app.config import settings


# Reuse the same OpenAI API key for explanations
_explain_client = OpenAI(api_key=settings.openai_api_key)


def explain_sql_query(sql: str, schema_description: str) -> str:
    """
    Call the LLM to explain a SQL query in plain language.
    """
    system_prompt = (
        "You are an expert SQL teacher. "
        "When given a SQL query and a schema description, "
        "you explain what the query does in clear, friendly language. "
        "Do NOT modify or reformat the SQL. "
        "Do NOT return any new SQL. Just explain."
    )

    user_prompt = f"""
Schema:
{schema_description}

SQL query to explain:
{sql}

Explain what this query is doing, step by step, for a non-expert audience.
"""

    resp = _explain_client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return resp.choices[0].message.content.strip()


def _render_turn_box(turn, bg_color: str, schema_description: str) -> None:
    """
    Render a single agent's turn inside a colored box.
    """
    st.markdown(
        f"""
<div style="background-color:{bg_color};padding:10px;border-radius:8px;margin-bottom:8px;">
  <strong>{turn.agent_name}</strong><br/>
  <span style="font-size:12px;">Complexity: {turn.complexity_score}</span><br/>
  <span style="font-size:12px;">Time: {turn.duration_seconds:.3f} s</span>
</div>
""",
        unsafe_allow_html=True,
    )

    st.code(turn.sql, language="sql")

    if not turn.is_valid_sql:
        st.error(f"Invalid SQL (blocked by safety rules): {turn.error}")
    elif turn.error:
        st.error(f"Execution error: {turn.error}")
    elif not turn.rows_preview:
        st.info("No rows returned.")
    else:
        st.dataframe(turn.rows_preview, use_container_width=True)

    # ---- Explain this query (LLM) ----
    if st.button(
        "Explain this query",
        key=f"explain_{turn.round_number}_{turn.agent_name}",
    ):
        with st.spinner("Asking the LLM to explain this query..."):
            explanation = explain_sql_query(turn.sql, schema_description)
        with st.expander("Explanation", expanded=True):
            st.markdown(explanation)


def _render_round_pair(left_turn, right_turn, pair_index: int, schema_description: str) -> None:
    """
    Render a pair of turns (Agent A vs Agent B) as a single 'round'.
    """
    st.markdown(f"### Round {pair_index + 1}")

    col_left, col_right = st.columns(2)

    with col_left:
        _render_turn_box(left_turn, "#e6f0ff", schema_description)  # light blue for left agent

    with col_right:
        _render_turn_box(right_turn, "#ffe6e6", schema_description)  # light red for right agent

    # Decide per-round winner based on complexity score
    score_left = left_turn.complexity_score
    score_right = right_turn.complexity_score

    if score_left > score_right:
        st.markdown(f"**Winner of this round: {left_turn.agent_name} 🏆**")
    elif score_right > score_left:
        st.markdown(f"**Winner of this round: {right_turn.agent_name} 🏆**")
    else:
        st.markdown("**This round is a draw 🤝**")

    st.markdown("---")


def main():
    st.set_page_config(
        page_title="SQL Fight Club (AI vs AI)",
        layout="wide",
    )

    st.title("SQL Fight Club (AI vs AI)")
    st.caption("Two unhinged SQL agents battle inside DuckDB. You watch the chaos.")

    # ---- Sidebar: settings ----
    with st.sidebar:
        st.header("Fight Settings")

        mode = st.radio(
            "Mode",
            ["AI vs AI", "You vs AI"],
            index=0,
            help="In 'You vs AI', you play as Agent A (left side).",
        )

        theme = st.selectbox(
            "Fight theme",
            [
                "Default chaos",
                "Finance bros",
                "Space pirates",
                "Healthcare",
                "Gaming",
                "Fantasy kingdom",
            ],
        )

        difficulty = st.selectbox(
            "Difficulty",
            ["Chill", "Tryhard", "Insane window functions"],
        )

        rounds = st.slider(
            "Number of turns (total)",
            min_value=2,
            max_value=12,
            value=settings.fight_rounds_default,
            step=2,  # keep it even so we always have full A vs B pairs
            help="Total number of turns (Agent A + Agent B). Must be even.",
        )

        st.markdown("---")
        st.subheader("Data controls")

        rows_per_table = st.slider(
            "Rows per base table",
            min_value=100,
            max_value=5000,
            value=200,
            step=100,
            help="How many rows to generate in people and transactions.",
        )

        weirdness = st.slider(
            "Weirdness level",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Higher values increase weird_score spread and absurd flags.",
        )

        if "data_seed" not in st.session_state:
            st.session_state["data_seed"] = 42

        if st.button("Regenerate random data"):
            st.session_state["data_seed"] += 1
            st.info("Random dataset will be regenerated for the next fight.")

        st.markdown("---")
        start_button = st.button("Start Fight 💥")

    # ---- Main area: Human SQL inputs (for You vs AI) ----
    human_sqls = None
    if mode == "You vs AI":
        st.markdown("### Your SQL turns (you are **Agent A**)")
        st.write(
            "You will play as Agent A on the left side. "
            "Enter one SQL **SELECT** statement for each of your turns."
        )

        num_human_turns = rounds // 2
        human_sqls = []
        for i in range(num_human_turns):
            sql = st.text_area(
                f"Your SQL for Round {i + 1}",
                key=f"human_sql_round_{i + 1}",
                height=120,
                placeholder=(
                    "Write a SELECT query using tables like people, transactions, etc. "
                    "Remember: only SELECT statements are allowed."
                ),
            )
            human_sqls.append(sql)

    # ---- CSV upload as extra table ----
    st.markdown("### Optional: Upload an extra table")
    st.write(
        "You can upload a CSV file to add as an extra table in DuckDB. "
        "The agents will see it in the schema and can query it."
    )

    uploaded_file = st.file_uploader(
        "Upload a CSV to include in the fight (optional)",
        type=["csv"],
    )

    extra_tables = None
    if uploaded_file is not None:
        default_name = "user_table"
        table_name = st.text_input(
            "Table name to use in SQL (no spaces ideally)",
            value=default_name,
        )
        try:
            user_df = pd.read_csv(uploaded_file)
            if table_name:
                extra_tables = [(table_name, user_df)]
                st.success(
                    f"CSV loaded. It will be available as table `{table_name}` in the fight."
                )
                st.dataframe(user_df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

    if not start_button:
        # Nothing to run yet; just show the input widgets.
        return

    # Basic validation for human mode
    if mode == "You vs AI":
        if any(not (q or "").strip() for q in human_sqls):
            st.error("Please fill in all your SQL boxes before starting the fight.")
            return

    # ---- Instantiate agents and fight manager ----
    agent_a = OpenAISQLAgent(name="Agent A")  # human still counted as Agent A in logs
    agent_b = OpenAISQLAgent(name="Agent B")

    manager = FightManager(
        agent_a=agent_a,
        agent_b=agent_b,
        rounds=rounds,
        n_rows=rows_per_table,
        weirdness=weirdness,
        rng_seed=st.session_state["data_seed"],
        extra_tables=extra_tables,
    )

    # ---- Schema panel + sample data (context) ----
    with st.expander("Show DuckDB schema & sample data"):
        st.markdown("#### Schema")
        st.text(manager.schema_description)

        try:
            st.markdown("#### Sample: people")
            people_df = manager.conn.execute("SELECT * FROM people LIMIT 5").df()
            st.dataframe(people_df, use_container_width=True)

            st.markdown("#### Sample: transactions")
            txn_df = manager.conn.execute("SELECT * FROM transactions LIMIT 5").df()
            st.dataframe(txn_df, use_container_width=True)

            # Extra tables (from uploaded CSVs)
            for tbl in manager.extra_table_names:
                st.markdown(f"#### Sample: {tbl}")
                df_extra = manager.conn.execute(f"SELECT * FROM {tbl} LIMIT 5").df()
                st.dataframe(df_extra, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load sample tables: {e}")

    # Progress bar + status text
    progress_bar = st.progress(0.0)
    status_placeholder = st.empty()

    def on_progress(current_round: int, total_rounds: int) -> None:
        progress = current_round / float(total_rounds)
        progress_bar.progress(progress)
        status_placeholder.text(f"Running turn {current_round}/{total_rounds}...")

    mode_key = "ai_vs_ai" if mode == "AI vs AI" else "you_vs_ai"

    with st.spinner("The agents are battling in SQL..."):
        turns = manager.run_fight(
            mode=mode_key,
            human_sqls=human_sqls,
            theme=theme,
            difficulty=difficulty,
            on_progress=on_progress,
        )

    # Clear progress indicators and celebrate
    progress_bar.empty()
    status_placeholder.empty()
    st.balloons()

    # ---- Scoreboard (overall winner) ----
    st.markdown("## Scoreboard")

    total_a = sum(
        t.complexity_score for t in turns if t.agent_name.strip().lower() == "agent a"
    )
    total_b = sum(
        t.complexity_score for t in turns if t.agent_name.strip().lower() == "agent b"
    )

    col1, col2 = st.columns(2)
    col1.metric("Agent A total complexity", total_a)
    col2.metric("Agent B total complexity", total_b)

    if total_a > total_b:
        st.success("Overall winner: **Agent A 🏆**")
    elif total_b > total_a:
        st.success("Overall winner: **Agent B 🏆**")
    else:
        st.info("Overall result: **Draw 🤝**")

    # ---- Turn stats: latency & token estimates ----
    st.markdown("### Turn Stats (latency & tokens)")
    stats_rows = [
        {
            "Turn": t.round_number,
            "Agent": t.agent_name,
            "Time (s)": round(t.duration_seconds, 3),
            "Estimated tokens": t.estimated_tokens if t.estimated_tokens is not None else "",
        }
        for t in turns
    ]
    st.dataframe(stats_rows, use_container_width=True)

    # ---- Fight rounds, side-by-side ----
    st.markdown("## Fight Rounds")

    # We expect an even number of turns (A, B, A, B, ...)
    # Group them in pairs for each round row.
    for i in range(0, len(turns), 2):
        if i + 1 < len(turns):
            left_turn = turns[i]
            right_turn = turns[i + 1]
            _render_round_pair(left_turn, right_turn, i // 2, manager.schema_description)
        else:
            # Fallback for an odd number of turns (shouldn't happen with step=2)
            _render_round_pair(turns[i], turns[i], i // 2, manager.schema_description)


if __name__ == "__main__":
    main()
