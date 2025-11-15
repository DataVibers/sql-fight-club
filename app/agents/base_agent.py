from abc import ABC, abstractmethod
from typing import Optional

class SQLAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_sql(
        self,
        schema: str,
        previous_query: Optional[str],
        previous_result_summary: Optional[str],
        challenge: str,
    ) -> str:
        """
        Return a SQL string. Implementation must ensure it uses the given schema.
        """
        ...
