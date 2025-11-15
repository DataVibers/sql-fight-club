"""
Configuration settings for SQL Fight Club
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command")
COHERE_TEMPERATURE = float(os.getenv("COHERE_TEMPERATURE", "0.9"))

# Fight Configuration
DEFAULT_ROUNDS = 5
MAX_ROUNDS = 10
MIN_ROUNDS = 1

# Query Execution
QUERY_TIMEOUT_SECONDS = 10
MAX_RESULT_ROWS = 100

# Database Configuration
DB_SEED_SIZE = 1000  # Number of rows to generate per table
RANDOM_SEED = 42

# UI Configuration
STREAMLIT_PAGE_TITLE = "⚔️ SQL Fight Club"
STREAMLIT_PAGE_ICON = "🦆"
STREAMLIT_LAYOUT = "wide"

# Agent Configuration
AGENT_A_NAME = "Agent Alpha 🔴"
AGENT_B_NAME = "Agent Beta 🔵"

# Scoring weights
SCORE_WEIGHTS = {
    "query_length": 0.1,
    "num_joins": 10,
    "num_subqueries": 15,
    "num_ctes": 20,
    "num_window_functions": 25,
    "num_aggregates": 5,
    "result_row_count": 0.01,
    "execution_time_penalty": -100,  # Penalty per second over 1s
}

# Safety limits
MAX_QUERY_LENGTH = 5000  # Characters
ALLOWED_KEYWORDS = ["SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", 
                    "HAVING", "WITH", "AS", "ON", "AND", "OR", "IN", "LIKE",
                    "BETWEEN", "CASE", "WHEN", "THEN", "ELSE", "END", "LIMIT",
                    "DISTINCT", "UNION", "INTERSECT", "EXCEPT", "OVER", "PARTITION"]
BLOCKED_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", 
                    "TRUNCATE", "EXEC", "EXECUTE"]
