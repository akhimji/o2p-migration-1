from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class SQLQuery:
    """Represents a SQL query found in source code"""
    
    query_text: str
    source_file: str
    language: str
    query_type: Optional[str] = None  # SELECT, INSERT, UPDATE, etc.
    tables: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    parsed: bool = False
    complexity_score: Optional[float] = None
    
    def __str__(self) -> str:
        """String representation of the SQL query"""
        return f"{self.query_type} query in {self.source_file}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "query_text": self.query_text,
            "source_file": self.source_file,
            "language": self.language,
            "query_type": self.query_type,
            "tables": self.tables,
            "columns": self.columns,
            "complexity_score": self.complexity_score
        }