from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

@dataclass
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    fight_rounds_default: int = int(os.getenv("FIGHT_ROUNDS_DEFAULT", "6"))
    max_rows_preview: int = int(os.getenv("MAX_ROWS_PREVIEW", "20"))
    duckdb_db_path: str = os.getenv("DUCKDB_DB_PATH", ":memory:")

settings = Settings()
