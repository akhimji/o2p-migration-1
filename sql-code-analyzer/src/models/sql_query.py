from typing import List, Dict, Any, Optional

class SQLQuery:
    """Model for a SQL query discovered in source code"""
    
    def __init__(self, query_text: str, source_file: str, language: str, query_type: str = None):
        self.query_text = query_text
        self.source_file = source_file
        self.language = language
        self.query_type = query_type
        self.tables = []
        self.columns = []
        self.parsed = False
        self.complexity_score = 0.0
        self.risk_score = 0.0
        self.performance_issues = []
        self.security_issues = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the query object to a dictionary"""
        return {
            "query_text": self.query_text,
            "source_file": self.source_file,
            "language": self.language,
            "query_type": self.query_type,
            "tables": self.tables,
            "columns": self.columns,
            "parsed": self.parsed,
            "complexity_score": self.complexity_score,
            "risk_score": self.risk_score,
            "performance_issues": self.performance_issues,
            "security_issues": self.security_issues
        }
    
    def __str__(self) -> str:
        """String representation of the query"""
        query_type = self.query_type or "UNKNOWN"
        tables = ", ".join(self.tables) if self.tables else "Unknown"
        return f"[{query_type}] from {self.source_file} - Tables: {tables}"