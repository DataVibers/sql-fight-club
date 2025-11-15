"""
Fight Manager - Orchestrates the SQL battle between agents
"""
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass
import duckdb

from app.config import (
    QUERY_TIMEOUT_SECONDS, 
    MAX_RESULT_ROWS,
    AGENT_A_NAME,
    AGENT_B_NAME
)
from app.agents.base_agent import SQLAgent
from app.utils.sql_safety import validate_query, execute_query_safely
from app.core.scoring import calculate_query_score
from app.models.fight_log import FightRound, FightResult


@dataclass
class FightState:
    """Tracks the current state of the fight"""
    current_round: int
    agent_a_score: int
    agent_b_score: int
    rounds: List[FightRound]
    winner: Optional[str] = None


class FightManager:
    """Manages the SQL Fight Club battle"""
    
    def __init__(
        self, 
        agent_a: SQLAgent, 
        agent_b: SQLAgent,
        db_connection: duckdb.DuckDBPyConnection,
        num_rounds: int = 5
    ):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.db_connection = db_connection
        self.num_rounds = num_rounds
        self.state = FightState(
            current_round=0,
            agent_a_score=0,
            agent_b_score=0,
            rounds=[]
        )
        
    def get_schema(self) -> str:
        """Get database schema for agents"""
        schema_query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """
        result = self.db_connection.execute(schema_query).fetchall()
        
        schema_text = "Database Schema:\n"
        current_table = None
        for table, column, dtype in result:
            if table != current_table:
                schema_text += f"\n{table}:\n"
                current_table = table
            schema_text += f"  - {column} ({dtype})\n"
        
        return schema_text
    
    def execute_round(
        self, 
        round_num: int,
        agent: SQLAgent,
        agent_name: str,
        challenge: str,
        previous_query: Optional[str] = None,
        previous_result_summary: Optional[str] = None
    ) -> FightRound:
        """Execute one round for one agent"""
        
        schema = self.get_schema()
        
        # Generate query from agent
        try:
            query = agent.generate_query(
                schema=schema,
                challenge=challenge,
                previous_query=previous_query,
                previous_result_summary=previous_result_summary
            )
        except Exception as e:
            return FightRound(
                round_number=round_num,
                agent_name=agent_name,
                query=None,
                success=False,
                error=f"Agent failed to generate query: {str(e)}",
                execution_time=0.0,
                result_row_count=0,
                score=0
            )
        
        # Validate query
        is_valid, validation_error = validate_query(query)
        if not is_valid:
            return FightRound(
                round_number=round_num,
                agent_name=agent_name,
                query=query,
                success=False,
                error=f"Query validation failed: {validation_error}",
                execution_time=0.0,
                result_row_count=0,
                score=0
            )
        
        # Execute query
        start_time = time.time()
        result, error = execute_query_safely(
            self.db_connection, 
            query, 
            QUERY_TIMEOUT_SECONDS
        )
        execution_time = time.time() - start_time
        
        if error:
            return FightRound(
                round_number=round_num,
                agent_name=agent_name,
                query=query,
                success=False,
                error=error,
                execution_time=execution_time,
                result_row_count=0,
                score=0
            )
        
        # Calculate score
        row_count = len(result) if result else 0
        score = calculate_query_score(query, row_count, execution_time)
        
        # Get result preview
        result_preview = None
        if result and len(result) > 0:
            preview_rows = result[:10]  # First 10 rows for preview
            result_preview = preview_rows
        
        return FightRound(
            round_number=round_num,
            agent_name=agent_name,
            query=query,
            success=True,
            error=None,
            execution_time=execution_time,
            result_row_count=row_count,
            result_preview=result_preview,
            score=score
        )
    
    def run_fight(self) -> FightResult:
        """Run the complete fight"""
        
        previous_a_query = None
        previous_b_query = None
        previous_a_summary = None
        previous_b_summary = None
        
        for round_num in range(1, self.num_rounds + 1):
            self.state.current_round = round_num
            
            # Agent A's turn
            challenge_a = self._generate_challenge(round_num, "A", previous_b_query)
            round_a = self.execute_round(
                round_num=round_num,
                agent=self.agent_a,
                agent_name=AGENT_A_NAME,
                challenge=challenge_a,
                previous_query=previous_b_query,
                previous_result_summary=previous_b_summary
            )
            self.state.rounds.append(round_a)
            self.state.agent_a_score += round_a.score
            
            if round_a.success:
                previous_a_query = round_a.query
                previous_a_summary = f"Returned {round_a.result_row_count} rows in {round_a.execution_time:.2f}s"
            
            # Agent B's turn
            challenge_b = self._generate_challenge(round_num, "B", previous_a_query)
            round_b = self.execute_round(
                round_num=round_num,
                agent=self.agent_b,
                agent_name=AGENT_B_NAME,
                challenge=challenge_b,
                previous_query=previous_a_query,
                previous_result_summary=previous_a_summary
            )
            self.state.rounds.append(round_b)
            self.state.agent_b_score += round_b.score
            
            if round_b.success:
                previous_b_query = round_b.query
                previous_b_summary = f"Returned {round_b.result_row_count} rows in {round_b.execution_time:.2f}s"
        
        # Determine winner
        if self.state.agent_a_score > self.state.agent_b_score:
            self.state.winner = AGENT_A_NAME
        elif self.state.agent_b_score > self.state.agent_a_score:
            self.state.winner = AGENT_B_NAME
        else:
            self.state.winner = "TIE 🤝"
        
        return FightResult(
            total_rounds=self.num_rounds,
            agent_a_score=self.state.agent_a_score,
            agent_b_score=self.state.agent_b_score,
            winner=self.state.winner,
            rounds=self.state.rounds
        )
    
    def _generate_challenge(self, round_num: int, agent: str, opponent_query: Optional[str]) -> str:
        """Generate a challenge prompt for the current round"""
        
        challenges = {
            1: "Write a SELECT query to explore the data. Keep it simple to start.",
            2: "Now add some JOINs. Show off your relational skills.",
            3: "Time to get fancy. Use aggregations, GROUP BY, or window functions.",
            4: "Your opponent is getting cocky. Use CTEs or subqueries to crush them.",
            5: "FINAL ROUND. Go completely unhinged. Recursive CTEs? Lateral joins? Whatever it takes."
        }
        
        base_challenge = challenges.get(round_num, "Write an impressive SQL query.")
        
        if opponent_query and round_num > 1:
            base_challenge += f"\n\nYour opponent just wrote this:\n{opponent_query}\n\nOne-up them."
        
        return base_challenge
