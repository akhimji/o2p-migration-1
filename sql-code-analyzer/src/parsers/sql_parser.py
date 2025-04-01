import re
from typing import List
from models.sql_query import SQLQuery

class SQLParser:
    """Parser for SQL queries that extracts key information"""
    
    def __init__(self):
        self.query_type_patterns = {
            "SELECT": re.compile(r'^\s*SELECT', re.IGNORECASE),
            "INSERT": re.compile(r'^\s*INSERT', re.IGNORECASE),
            "UPDATE": re.compile(r'^\s*UPDATE', re.IGNORECASE),
            "DELETE": re.compile(r'^\s*DELETE', re.IGNORECASE),
            "CREATE": re.compile(r'^\s*CREATE', re.IGNORECASE),
            "ALTER": re.compile(r'^\s*ALTER', re.IGNORECASE),
            "DROP": re.compile(r'^\s*DROP', re.IGNORECASE)
        }
        
        # Simple patterns for table extraction
        self.table_patterns = {
            "FROM": re.compile(r'FROM\s+([a-zA-Z0-9_\.]+)', re.IGNORECASE),
            "UPDATE": re.compile(r'UPDATE\s+([a-zA-Z0-9_\.]+)', re.IGNORECASE),
            "INSERT INTO": re.compile(r'INSERT\s+INTO\s+([a-zA-Z0-9_\.]+)', re.IGNORECASE),
            "DELETE FROM": re.compile(r'DELETE\s+FROM\s+([a-zA-Z0-9_\.]+)', re.IGNORECASE),
        }
    
    def identify_query_type(self, query_text: str) -> str:
        """Identify the type of SQL query"""
        for query_type, pattern in self.query_type_patterns.items():
            if pattern.search(query_text):
                return query_type
        return "UNKNOWN"
    
    def extract_tables(self, query_text: str, query_type: str) -> List[str]:
        """Extract table names from the SQL query"""
        tables = []
        
        # Apply appropriate regex based on query type
        if query_type == "SELECT":
            matches = self.table_patterns["FROM"].findall(query_text)
            tables.extend(matches)
        elif query_type == "UPDATE":
            matches = self.table_patterns["UPDATE"].findall(query_text)
            tables.extend(matches)
        elif query_type == "INSERT":
            matches = self.table_patterns["INSERT INTO"].findall(query_text)
            tables.extend(matches)
        elif query_type == "DELETE":
            matches = self.table_patterns["DELETE FROM"].findall(query_text)
            tables.extend(matches)
            
        return tables
    
    def parse(self, query: SQLQuery) -> SQLQuery:
        """Parse a SQL query to extract information"""
        # Identify query type
        query.query_type = self.identify_query_type(query.query_text)
        
        # Extract tables
        query.tables = self.extract_tables(query.query_text, query.query_type)
        
        # Mark as parsed
        query.parsed = True
        
        return query