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
        
        # Oracle-specific data
        self.is_oracle_specific = False
        self.oracle_features = []
        self.oracle_feature_count = 0

        # New: Join information
        self.join_types = {}  # Dictionary of join types
        self.has_joins = False  # Flag if query has any joins
        self.join_count = 0  # Count of join operations

        # New: Complexity attribute
        self.complexity = 0  # Initialize complexity
    
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
            "security_issues": self.security_issues,
            # Oracle-specific fields
            "is_oracle_specific": self.is_oracle_specific,
            "oracle_features": self.oracle_features,
            "oracle_feature_count": self.oracle_feature_count,
            # New: Join information
            "join_types": self.join_types,
            "has_joins": self.has_joins,
            "join_count": self.join_count,
            # New: Complexity attribute
            "complexity": self.complexity
        }
    
    def __str__(self) -> str:
        """String representation of the query"""
        query_type = self.query_type or "UNKNOWN"
        tables = ", ".join(self.tables) if self.tables else "Unknown"
        oracle_note = " (Oracle-specific)" if self.is_oracle_specific else ""
        return f"[{query_type}]{oracle_note} from {self.source_file} - Tables: {tables}"