# app/core/scoring.py
import math

def complexity_score(sql: str) -> float:
    """
    Toy heuristic: more joins, subqueries, and functions = more 'complex'.
    """
    s = sql.lower()
    score = 0
    score += s.count(" join ") * 2
    score += s.count(" group by ") * 1.5
    score += s.count(" order by ") * 1.0
    score += s.count(" over(") * 3.0
    score += s.count(" case ") * 1.5
    score += s.count("(") * 0.2
    return round(score, 2)
