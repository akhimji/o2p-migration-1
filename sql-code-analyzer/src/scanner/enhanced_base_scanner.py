from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Pattern
from pathlib import Path
import re
import logging
import sys
import os

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now use relative imports
from validators.sql_validator import SQLValidator
from validators.sqlparse_validator import SqlParseValidator
from models.sql_query import SQLQuery

logger = logging.getLogger('EnhancedBaseScanner')

class EnhancedBaseScanner(ABC):
    """
    Enhanced abstract base class for all scanners with improved SQL detection
    """
    
    def __init__(self, base_path: str, use_sqlparse: bool = True):
        self.base_path = Path(base_path)
        self._compile_sql_patterns()
        
        # Initialize SQL validators
        self.sql_validator = SQLValidator()
        self.sqlparse_validator = SqlParseValidator() if use_sqlparse else None
    
    def _compile_sql_patterns(self) -> None:
        """
        Compile comprehensive SQL patterns to detect a wider range of SQL operations
        """
        # SQL keywords to detect (expanded list)
        self.sql_keywords = {
            # Data Manipulation Language (DML)
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'UPSERT', 'TRUNCATE',
            
            # Data Definition Language (DDL)
            'CREATE', 'ALTER', 'DROP', 'RENAME', 'COMMENT', 
            
            # Data Control Language (DCL)
            'GRANT', 'REVOKE', 'DENY',
            
            # Transaction Control Language (TCL)
            'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'SET TRANSACTION',
            
            # Database objects
            'TABLE', 'VIEW', 'INDEX', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'SCHEMA',
        }
        
        # SQL clauses and other common keywords
        self.sql_clauses = {
            'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT', 'OFFSET',
            'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'CROSS JOIN',
            'UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT', 'WITH',
            'ON', 'USING', 'VALUES', 'SET', 'IN', 'EXISTS', 'INTO', 'AS'
        }
        
        # Compile pattern for validating SQL queries
        pattern_str = '|'.join(self.sql_keywords | self.sql_clauses)
        self.sql_keyword_pattern = re.compile(pattern_str, re.IGNORECASE)
        
        # SQL command prefixes for beginning of query patterns
        self.sql_command_prefixes = [keyword + r'\s+' for keyword in self.sql_keywords]
    
    def _generate_sql_patterns(self, string_literal_marker: str = '"') -> List[str]:
        """
        Generate SQL detection patterns for a given string literal marker
        
        Args:
            string_literal_marker: The character(s) that marks string literals in the language
        
        Returns:
            List of regex patterns to detect SQL in string literals
        """
        patterns = []
        
        # Simple assignment patterns for each keyword
        for command in self.sql_command_prefixes:
            patterns.append(f'{string_literal_marker}({command}.*?){string_literal_marker}')
        
        # Common method call patterns 
        common_methods = [
            'execute', 'executeQuery', 'executeUpdate', 'executeSql', 'executeStatement',
            'prepareStatement', 'createStatement', 'query', 'createQuery'
        ]
        
        for method in common_methods:
            patterns.append(f'{method}\\(\\s*{string_literal_marker}(.*?){string_literal_marker}')
        
        return patterns
    
    def is_valid_sql_query(self, query_text: str) -> bool:
        """
        Validate if a string is likely a SQL query using our validators
        
        Args:
            query_text: The text to check
            
        Returns:
            True if the text is likely SQL, False otherwise
        """
        if not query_text or len(query_text) < 8:  # Minimum reasonable query length
            return False
        
        # First try with the advanced sqlparse validator if available
        if self.sqlparse_validator:
            is_valid, reason = self.sqlparse_validator.is_valid_sql(query_text)
            if not is_valid:
                logger.debug(f"SQLParse rejected: {reason}")
                return False
            return True
            
        # Fallback to our custom validator
        is_valid, reason = self.sql_validator.is_valid_sql(query_text)
        if not is_valid:
            logger.debug(f"SQL validator rejected: {reason}")
            return False
        
        return True
    
    def detect_query_type(self, query_text: str) -> str:
        """
        Detect the type of SQL query
        
        Args:
            query_text: The SQL query text
            
        Returns:
            The query type (SELECT, INSERT, etc.) or "UNKNOWN"
        """
        if not query_text:
            return "UNKNOWN"
            
        # Try with sqlparse validator first
        if self.sqlparse_validator:
            return self.sqlparse_validator.get_query_type(query_text)
        
        # Fallback to our custom validator
        return self.sql_validator.get_query_type(query_text)
    
    @abstractmethod
    def scan(self) -> List[SQLQuery]:
        """Scan files and extract SQL queries"""
        pass
    
    @abstractmethod
    def get_tech_stack_info(self) -> Dict[str, Any]:
        """Get information about the tech stack"""
        pass