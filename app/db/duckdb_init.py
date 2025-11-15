# app/db/duckdb_init.py
import duckdb
import pandas as pd
import numpy as np
from typing import Optional
from app.config import settings


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Create or reuse a DuckDB connection.
    Uses in-memory or file-based DB depending on DUCKDB_DB_PATH.
    """
    if settings.duckdb_db_path == ":memory:":
        conn = duckdb.connect(database=":memory:")
    else:
        conn = duckdb.connect(database=settings.duckdb_db_path, read_only=False)
    return conn


def seed_random_data(
    conn: Optional[duckdb.DuckDBPyConnection] = None,
    n_rows: int = 200,
    weirdness: float = 1.0,
    rng_seed: int = 42,
) -> duckdb.DuckDBPyConnection:
    """
    Create a few fun tables with random data for the agents to query.

    n_rows:     how many rows per table (approx).
    weirdness:  controls how extreme weird_score and is_absurd become.
                0.0 = tame, 2.0 = very wild.
    rng_seed:   controls random reproducibility.
    """
    if conn is None:
        conn = get_connection()

    # Reset previous tables to keep things clean.
    conn.execute("DROP TABLE IF EXISTS people;")
    conn.execute("DROP TABLE IF EXISTS transactions;")

    rng = np.random.default_rng(rng_seed)

    # Scale weirdness for weird_score stddev and absurd probability
    weird_scale = 5.0 + 10.0 * weirdness
    absurd_prob = min(0.9, 0.2 + 0.3 * weirdness)

    # Example table: people
    people_df = pd.DataFrame({
        "id": np.arange(1, n_rows + 1),
        "name": [f"Person_{i}" for i in range(1, n_rows + 1)],
        "age": rng.integers(18, 80, size=n_rows),
        "weird_score": rng.normal(loc=0, scale=weird_scale, size=n_rows).round(2),
        "city": rng.choice(["Lagos", "Nairobi", "London", "Mars Base", "Atlantis"], size=n_rows),
    })

    # Example table: transactions
    txn_df = pd.DataFrame({
        "txn_id": np.arange(1, n_rows + 1),
        "person_id": rng.integers(1, n_rows + 1, size=n_rows),
        "amount": rng.exponential(scale=100, size=n_rows).round(2),
        "category": rng.choice(["food", "weapons", "books", "potions"], size=n_rows),
        "is_absurd": rng.choice([0, 1], size=n_rows, p=[1 - absurd_prob, absurd_prob]),
    })

    conn.register("people_df", people_df)
    conn.register("txn_df", txn_df)

    conn.execute("CREATE OR REPLACE TABLE people AS SELECT * FROM people_df;")
    conn.execute("CREATE OR REPLACE TABLE transactions AS SELECT * FROM txn_df;")

    return conn
