import logging
import re
from typing import Tuple, Optional, List

# Try to import sqlparse, which might not be installed
try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False
    logging.warning("sqlparse library not available. Advanced SQL validation disabled.")

logger = logging.getLogger('SQLParseValidator')

class SqlParseValidator:
    """
    SQL validator that uses the sqlparse library for more accurate validation.
    Falls back to basic validation if sqlparse is not available.
    """
    
    def __init__(self):
        self.sqlparse_available = SQLPARSE_AVAILABLE
        
        # SQL keywords that typically start a statement
        self.sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
            'TRUNCATE', 'MERGE', 'GRANT', 'REVOKE', 'BEGIN', 'COMMIT', 'ROLLBACK',
            'WITH', 'SET', 'EXECUTE', 'EXEC', 'CALL', 'EXPLAIN'
        ]
        
        # False positive patterns for method names
        self.false_method_pattern = re.compile(r'(?:create|select|update|delete|drop|insert|alter)[A-Z][a-zA-Z0-9_]*\s*\(')
    
    def is_valid_sql(self, query_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if the given text is likely a SQL query using sqlparse
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Quick false positive check for method names
        if self.false_method_pattern.search(query_text):
            return False, "Matches a method name pattern"
        
        # Basic validation
        if not query_text or len(query_text) < 10:
            return False, "Text too short to be SQL"
        
        # Use sqlparse if available
        if self.sqlparse_available:
            return self._validate_with_sqlparse(query_text)
        else:
            # Fallback to basic keyword validation
            return self._basic_validate(query_text)
    
    def _validate_with_sqlparse(self, query_text: str) -> Tuple[bool, Optional[str]]:
        """Validate using sqlparse library"""
        try:
            # Try to parse the query
            statements = sqlparse.parse(query_text)
            
            if not statements:
                return False, "No SQL statement found by parser"
            
            # Check if the parsed statement has a recognizable structure
            stmt = statements[0]
            
            # Get the statement type
            stmt_type = self._get_statement_type(stmt)
            if not stmt_type:
                return False, "Unrecognized SQL statement type"
            
            # Check if statement has minimum required tokens for its type
            valid, reason = self._validate_statement_structure(stmt, stmt_type)
            if not valid:
                return False, reason
                
            return True, f"Valid {stmt_type} statement"
            
        except Exception as e:
            logger.debug(f"SQL parse error: {e}")
            return False, f"SQL parse error: {str(e)}"
    
    def _get_statement_type(self, stmt) -> Optional[str]:
        """Get the statement type from sqlparse statement"""
        # Extract first token that's a keyword
        first_keyword = None
        for token in stmt.tokens:
            if token.is_keyword and token.value.upper() in self.sql_keywords:
                first_keyword = token.value.upper()
                break
        
        return first_keyword
    
    def _validate_statement_structure(self, stmt, stmt_type: str) -> Tuple[bool, Optional[str]]:
        """Validate the structure of a specific statement type"""
        if stmt_type == 'SELECT':
            # Check for FROM clause in SELECT
            has_from = any(token.is_keyword and token.value.upper() == 'FROM' for token in stmt.tokens)
            if not has_from:
                # Exception for SELECT expressions/functions
                if len(stmt.tokens) > 2:
                    return True, "SELECT expression"
                return False, "SELECT without FROM clause"
                
        elif stmt_type == 'INSERT':
            # Check for INTO clause in INSERT
            has_into = any(token.is_keyword and token.value.upper() == 'INTO' for token in stmt.tokens)
            if not has_into:
                return False, "INSERT without INTO clause"
                
        elif stmt_type == 'UPDATE':
            # Check for SET clause in UPDATE
            has_set = any(token.is_keyword and token.value.upper() == 'SET' for token in stmt.tokens)
            if not has_set:
                return False, "UPDATE without SET clause"
                
        elif stmt_type == 'CREATE':
            # Check for object type after CREATE
            found_object = False
            for i, token in enumerate(stmt.tokens):
                if token.is_keyword and token.value.upper() == 'CREATE' and i+1 < len(stmt.tokens):
                    next_tokens = ' '.join(t.value.upper() for t in stmt.tokens[i+1:i+3])
                    if any(obj in next_tokens for obj in ['TABLE', 'VIEW', 'INDEX', 'FUNCTION', 'PROCEDURE', 'TRIGGER']):
                        found_object = True
                        break
            
            if not found_object:
                return False, "CREATE without valid object type"
        
        # Default to valid for other statement types or if we passed specific checks
        return True, f"Valid {stmt_type} structure"
    
    def _basic_validate(self, query_text: str) -> Tuple[bool, Optional[str]]:
        """Basic validation without sqlparse"""
        # Normalize to uppercase for keyword matching
        upper_text = query_text.upper()
        
        # Check for SQL keywords at the beginning
        for keyword in self.sql_keywords:
            if re.match(rf'^\s*{keyword}\b', upper_text):
                # Additional validation based on keyword
                if keyword == 'SELECT' and not re.search(r'\bFROM\b', upper_text):
                    # Check if it's a function call or system variable
                    if not re.search(r'SELECT\s+(?:@@|[A-Za-z0-9_.]+\()', upper_text):
                        return False, "SELECT without FROM clause"
                
                elif keyword == 'INSERT' and not re.search(r'\bINTO\b', upper_text):
                    return False, "INSERT without INTO clause"
                    
                elif keyword == 'UPDATE' and not re.search(r'\bSET\b', upper_text):
                    return False, "UPDATE without SET clause"
                
                elif keyword == 'CREATE' and not re.search(r'\b(TABLE|VIEW|INDEX|PROCEDURE|FUNCTION|TRIGGER)\b', upper_text):
                    return False, "CREATE without valid object type"
                
                return True, f"Starts with SQL keyword {keyword}"
        
        # Check for clauses that strongly indicate SQL
        sql_clauses = ['FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN', 'INNER JOIN', 'LEFT JOIN']
        clause_count = 0
        for clause in sql_clauses:
            if re.search(rf'\b{clause}\b', upper_text):
                clause_count += 1
        
        if clause_count >= 2:
            return True, f"Contains multiple SQL clauses"
            
        # Not enough evidence
        return False, "Insufficient SQL syntax markers"
    
    def get_query_type(self, query_text: str) -> str:
        """
        Determine the type of a validated SQL query using sqlparse if available
        """
        if not self.sqlparse_available:
            # Basic detection using regex
            upper_text = query_text.lstrip().upper()
            for keyword in self.sql_keywords:
                if upper_text.startswith(keyword):
                    return keyword
            
            # Special case for WITH
            if upper_text.startswith('WITH'):
                match = re.search(r'WITH\s+.+?(?:\s+,\s+.+?)*?\s+(SELECT|INSERT|UPDATE|DELETE|MERGE)\s+', 
                                upper_text, re.DOTALL)
                if match:
                    return match.group(1)
            
            return "UNKNOWN"
        
        try:
            # Parse the query
            statements = sqlparse.parse(query_text)
            if not statements:
                return "UNKNOWN"
                
            # Get the statement type
            return self._get_statement_type(statements[0]) or "UNKNOWN"
        except:
            return "UNKNOWN"