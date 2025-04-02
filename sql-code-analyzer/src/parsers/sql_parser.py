import re
from typing import List, Dict, Any, Set
from models.sql_query import SQLQuery
# Fix the import for OracleFeatureDetector
from parsers.oracle_detector import OracleFeatureDetector

class SQLParser:
    """Parser for SQL queries that extracts key information"""
    
    def __init__(self):
        # Patterns for query types
        self.query_type_patterns = {
            "SELECT": re.compile(r'^\s*SELECT', re.IGNORECASE),
            "INSERT": re.compile(r'^\s*INSERT', re.IGNORECASE),
            "UPDATE": re.compile(r'^\s*UPDATE', re.IGNORECASE),
            "DELETE": re.compile(r'^\s*DELETE', re.IGNORECASE),
            "CREATE": re.compile(r'^\s*CREATE', re.IGNORECASE),
            "ALTER": re.compile(r'^\s*ALTER', re.IGNORECASE),
            "DROP": re.compile(r'^\s*DROP', re.IGNORECASE),
            "TRUNCATE": re.compile(r'^\s*TRUNCATE', re.IGNORECASE),
            "MERGE": re.compile(r'^\s*MERGE', re.IGNORECASE),
            "GRANT": re.compile(r'^\s*GRANT', re.IGNORECASE),
            "REVOKE": re.compile(r'^\s*REVOKE', re.IGNORECASE)
        }
        
        # Expanded table extraction patterns
        self.table_patterns = {
            # DML
            "SELECT": [
                re.compile(r'FROM\s+([a-zA-Z0-9_\.\[\]"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?', re.IGNORECASE),
                re.compile(r'JOIN\s+([a-zA-Z0-9_\.\[\]"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?', re.IGNORECASE)
            ],
            "UPDATE": [
                re.compile(r'UPDATE\s+([a-zA-Z0-9_\.\[\]"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?', re.IGNORECASE)
            ],
            "INSERT": [
                re.compile(r'INSERT\s+INTO\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            "DELETE": [
                re.compile(r'DELETE\s+FROM\s+([a-zA-Z0-9_\.\[\]"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?', re.IGNORECASE)
            ],
            "MERGE": [
                re.compile(r'MERGE\s+INTO\s+([a-zA-Z0-9_\.\[\]"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?', re.IGNORECASE),
                re.compile(r'USING\s+([a-zA-Z0-9_\.\[\]"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?', re.IGNORECASE)
            ],
            # DDL
            "CREATE": [
                re.compile(r'CREATE\s+TABLE\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE),
                re.compile(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:[a-zA-Z0-9_]+)\s+ON\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE),
                re.compile(r'CREATE\s+VIEW\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            "ALTER": [
                re.compile(r'ALTER\s+TABLE\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            "DROP": [
                re.compile(r'DROP\s+TABLE\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE),
                re.compile(r'DROP\s+INDEX\s+(?:[a-zA-Z0-9_]+)\s+ON\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE),
                re.compile(r'DROP\s+VIEW\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            "TRUNCATE": [
                re.compile(r'TRUNCATE\s+TABLE\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            # Other common operations
            "GRANT": [
                re.compile(r'GRANT\s+.*?\s+ON\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            "REVOKE": [
                re.compile(r'REVOKE\s+.*?\s+ON\s+([a-zA-Z0-9_\.\[\]"]+)', re.IGNORECASE)
            ],
            # CTE (Common Table Expressions)
            "WITH_CTE": [
                re.compile(r'WITH\s+([a-zA-Z0-9_]+)(?:\s*\([^)]*\))?\s+AS', re.IGNORECASE)
            ]
        }
        
        # Patterns to extract columns (simplified for common cases)
        self.column_patterns = {
            "SELECT": re.compile(r'SELECT\s+(.*?)\s+FROM', re.IGNORECASE | re.DOTALL),
            "INSERT": re.compile(r'INSERT\s+INTO\s+[^\(]*\(([^\)]*)\)', re.IGNORECASE | re.DOTALL),
            "UPDATE": re.compile(r'SET\s+(.*?)(?:WHERE|$)', re.IGNORECASE | re.DOTALL),
            "CREATE": re.compile(r'CREATE\s+TABLE\s+[^\(]*\(([^\)]*)\)', re.IGNORECASE | re.DOTALL)
        }
        
        # Initialize Oracle detector
        self.oracle_detector = OracleFeatureDetector()
    
    def identify_query_type(self, query_text: str) -> str:
        """Identify the type of SQL query"""
        if not query_text:
            return "UNKNOWN"
            
        # Check for WITH clause at the beginning (CTE)
        if re.match(r'^\s*WITH\s+', query_text, re.IGNORECASE):
            # Try to find the actual command after the CTEs
            match = re.search(r'WITH\s+.*?(?:\s*,\s*.*?)*?\s+(SELECT|INSERT|UPDATE|DELETE|MERGE)\s+', 
                           query_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).upper()
        
        # Check regular query types
        for query_type, pattern in self.query_type_patterns.items():
            if pattern.search(query_text):
                return query_type
        
        # Special case for union queries
        if re.search(r'UNION\s+(?:ALL\s+)?SELECT', query_text, re.IGNORECASE):
            return "SELECT"
        
        return "UNKNOWN"
    
    def extract_tables(self, query_text: str, query_type: str) -> List[str]:
        """Extract table names from the SQL query"""
        tables = set()
        
        # Special case for WITH (CTEs)
        if query_text.upper().startswith('WITH '):
            # Extract CTE names
            with_patterns = self.table_patterns.get("WITH_CTE", [])
            for pattern in with_patterns:
                for match in pattern.finditer(query_text):
                    if match.group(1):
                        tables.add(match.group(1))
        
        # Apply appropriate regex based on query type
        patterns = self.table_patterns.get(query_type, [])
        
        for pattern in patterns:
            for match in pattern.finditer(query_text):
                if match.group(1):
                    # Clean up table name (remove brackets, quotes, etc.)
                    table_name = self._clean_identifier(match.group(1))
                    tables.add(table_name)
        
        # If we didn't find any tables but the query looks like a SELECT,
        # try the generic FROM pattern as a fallback
        if not tables and query_type == "UNKNOWN" and "SELECT" in query_text.upper():
            select_patterns = self.table_patterns.get("SELECT", [])
            for pattern in select_patterns:
                for match in pattern.finditer(query_text):
                    if match.group(1):
                        table_name = self._clean_identifier(match.group(1))
                        tables.add(table_name)
        
        # Convert to sorted list for consistent output
        return sorted(tables)
    
    def extract_columns(self, query_text: str, query_type: str) -> List[str]:
        """Extract column names from the SQL query"""
        columns = set()
        
        pattern = self.column_patterns.get(query_type)
        if not pattern:
            return []
            
        match = pattern.search(query_text)
        if not match:
            return []
        
        column_section = match.group(1)
        
        # Handle different types of queries
        if query_type == "SELECT":
            # Handle * special case
            if '*' in column_section:
                columns.add('*')
            
            # Remove subqueries before processing
            # This is a simplification and might not handle all cases correctly
            clean_section = re.sub(r'\([^)]*\)', '', column_section)
            
            # Split columns by commas, but ignore commas inside functions
            col_level = 0
            current_col = ""
            
            for char in clean_section:
                if char == ',' and col_level == 0:
                    columns.add(self._extract_column_name(current_col.strip()))
                    current_col = ""
                else:
                    if char == '(':
                        col_level += 1
                    elif char == ')':
                        col_level -= 1
                    current_col += char
            
            if current_col.strip():
                columns.add(self._extract_column_name(current_col.strip()))
                
        elif query_type == "INSERT":
            # For INSERT, columns are usually simpler
            for col in column_section.split(','):
                clean_col = self._clean_identifier(col.strip())
                if clean_col:
                    columns.add(clean_col)
                
        elif query_type == "UPDATE":
            # For UPDATE, columns are in form "col = value"
            for assignment in column_section.split(','):
                parts = assignment.split('=', 1)
                if len(parts) > 0:
                    clean_col = self._clean_identifier(parts[0].strip())
                    if clean_col:
                        columns.add(clean_col)
                        
        elif query_type == "CREATE":
            # For CREATE TABLE, need to extract column definitions
            for col_def in column_section.split(','):
                # Take the first word as column name
                parts = col_def.strip().split(None, 1)
                if parts:
                    clean_col = self._clean_identifier(parts[0].strip())
                    if clean_col:
                        columns.add(clean_col)
        
        # Remove empty strings and return sorted list
        return sorted(col for col in columns if col)
    
    def _extract_column_name(self, column_expr: str) -> str:
        """Extract the actual column name from an expression"""
        # Handle column aliases: "col AS alias" => "col"
        if ' AS ' in column_expr.upper():
            column_expr = column_expr.split(' AS ')[0].strip()
        
        # Handle table qualifiers: "table.col" => "col"
        if '.' in column_expr:
            parts = column_expr.split('.')
            column_expr = parts[-1]  # Take the part after the last dot
        
        return self._clean_identifier(column_expr)
    
    def _clean_identifier(self, identifier: str) -> str:
        """Clean an SQL identifier (table or column name)"""
        # Remove brackets, quotes, etc.
        cleaned = re.sub(r'[\[\]"`\']', '', identifier.strip())
        # Handle schema qualifiers
        if '.' in cleaned:
            return cleaned  # Keep schema qualification
        return cleaned
    
    def parse(self, query: SQLQuery) -> SQLQuery:
        """Parse a SQL query to extract information"""
        # Use query type if already set, or identify it
        if not query.query_type or query.query_type == "UNKNOWN":
            query.query_type = self.identify_query_type(query.query_text)
        
        # Extract tables
        query.tables = self.extract_tables(query.query_text, query.query_type)
        
        # Extract columns (if appropriate for this query type)
        if query.query_type in self.column_patterns:
            query.columns = self.extract_columns(query.query_text, query.query_type)
        
        # Detect Oracle-specific features
        oracle_features = self.oracle_detector.summarize_oracle_features(query.query_text)
        if oracle_features:
            query.is_oracle_specific = True
            query.oracle_features = oracle_features
            query.oracle_feature_count = len(oracle_features)
        
        # Mark as parsed
        query.parsed = True
        
        return query