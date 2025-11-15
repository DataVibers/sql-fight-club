from typing import Optional
from openai import OpenAI
from app.config import settings
from app.agents.base_agent import SQLAgent

SYSTEM_PROMPT = """You are a theatrical SQL battle agent.
You receive:
- A DuckDB schema
- The previous query (if any)
- A short summary of the previous result (if any)
- A "challenge" describing how to one-up the last query

You must respond with ONE valid DuckDB SQL query ONLY.
Rules:
- SELECT statements only (no INSERT/UPDATE/DELETE/DDL).
- Use the given tables and columns only.
- Make the query more absurd, complex, or creative each round.
- Do not include any explanation, just the SQL.
"""

class OpenAISQLAgent(SQLAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def generate_sql(
        self,
        schema: str,
        previous_query: Optional[str],
        previous_result_summary: Optional[str],
        challenge: str,
    ) -> str:
        user_prompt = f"""
DuckDB schema:
{schema}

Previous query:
{previous_query or "None"}

Previous result summary:
{previous_result_summary or "None"}

Your challenge:
{challenge}

Respond with ONLY a SQL SELECT statement, no prose.
"""

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            #temperature=0.9,
        )

        sql = resp.choices[0].message.content.strip()
        return sql
