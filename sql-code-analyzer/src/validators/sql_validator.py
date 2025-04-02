import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger('SQLValidator')

class SQLValidator:
    """
    Class to validate whether a string contains a real SQL query,
    with sophisticated rules to reduce false positives
    """
    
    def __init__(self):
        # SQL command keywords that typically start a SQL statement
        self.sql_commands = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
            'TRUNCATE', 'MERGE', 'GRANT', 'REVOKE', 'WITH', 'EXECUTE'
        }
        
        # SQL clauses that must appear in the correct context
        self.sql_clauses = {
            'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'JOIN',
            'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN',
            'CROSS JOIN', 'UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT'
        }
        
        # SQL operators and syntax that suggests SQL
        self.sql_operators = {
            ' AS ', ' ON ', ' AND ', ' OR ', ' IN ', ' NOT IN ',
            ' IS NULL', ' IS NOT NULL', ' BETWEEN ', ' LIKE ',
            ' EXISTS ', ' DESC', ' ASC', ' LIMIT ', ' OFFSET '
        }
        
        # SQL data types that suggest DDL statements
        self.sql_datatypes = {
            ' INT ', ' INTEGER ', ' VARCHAR', ' CHAR', ' TEXT ',
            ' DATE ', ' DATETIME ', ' TIMESTAMP ', ' BOOLEAN ',
            ' FLOAT ', ' DOUBLE ', ' DECIMAL ', ' NUMERIC ',
            ' BIGINT ', ' SMALLINT ', ' BLOB ', ' CLOB '
        }
        
        # Common table and column naming patterns in SQL
        self.common_db_objects = {
            'TABLE ', 'VIEW ', 'INDEX ', 'FUNCTION ', 'PROCEDURE ',
            'TRIGGER ', 'SEQUENCE ', 'DATABASE ', 'SCHEMA '
        }
        
        # False positive patterns - camelCase method calls that might contain SQL keywords
        self.false_positive_patterns = [
            # Method calls with SQL keywords but not actual SQL
            re.compile(r'(?:create|select|update|delete|drop|insert|alter)[A-Z][a-zA-Z0-9_]*\('),
            # Reserved words in variable names followed by dot notation
            re.compile(r'\b(?:select|from|where|table|join|update|delete|drop)\.[a-zA-Z_]'),
            # UI related text that might contain SQL keywords
            re.compile(r'"(?:Select|Update|Delete|Insert)[^"]*(?:button|label|text)"'),
            # Function names containing SQL keywords in camelCase
            re.compile(r'\b(?:get|set|fetch|retrieve|load|save|process|handle|perform)[A-Z][a-zA-Z]*(?:Select|Insert|Update|Delete)[a-zA-Z]*\b')
        ]
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for repeated use"""
        # Pattern to match the start of a SQL statement
        self.sql_start_pattern = re.compile(
            r'^\s*(?:' + '|'.join(self.sql_commands) + r')\s+',
            re.IGNORECASE
        )
        
        # Pattern to match SQL clauses - must be full words
        self.clause_pattern = re.compile(
            r'\b(' + '|'.join(self.sql_clauses) + r')\b',
            re.IGNORECASE
        )
        
        # Combined pattern for SQL syntax elements
        all_syntax = list(self.sql_operators) + list(self.sql_datatypes) + list(self.common_db_objects)
        self.syntax_pattern = re.compile(
            '|'.join(map(re.escape, all_syntax)),
            re.IGNORECASE
        )
    
    def is_valid_sql(self, query_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if the given text is likely a SQL query
        
        Returns:
            Tuple of (is_valid, reason)
            - is_valid: Boolean indicating if this is likely valid SQL
            - reason: String explanation why it was accepted or rejected
        """
        if not query_text or len(query_text) < 10:
            return False, "Text too short to be SQL"
        
        # Remove string literals to avoid false positives in quoted text
        clean_text = self._remove_string_literals(query_text)
        
        # Check for false positives
        for pattern in self.false_positive_patterns:
            if pattern.search(query_text):
                return False, "Matched false positive pattern"
        
        # Check if it's a SQL command at the beginning
        if self.sql_start_pattern.search(clean_text):
            command = re.match(r'^\s*(\w+)', clean_text).group(1).upper()
            
            # Validate SQL command context
            if command == 'SELECT' and not re.search(r'\bFROM\b', clean_text, re.IGNORECASE):
                # SELECT without FROM is suspicious unless it's a simple expression
                if not re.search(r'SELECT\s+(?:@@|[A-Za-z0-9_.]+\()', clean_text, re.IGNORECASE):
                    return False, "SELECT without FROM clause"
                    
            elif command == 'UPDATE' and not re.search(r'\bSET\b', clean_text, re.IGNORECASE):
                return False, "UPDATE without SET clause"
                
            elif command == 'INSERT' and not re.search(r'\bINTO\b', clean_text, re.IGNORECASE):
                return False, "INSERT without INTO clause"
                
            elif command == 'CREATE' and not any(re.search(rf'\b{obj}\b', clean_text, re.IGNORECASE) for obj in self.common_db_objects):
                return False, "CREATE without valid object type"
            
            elif command == 'DROP' and not any(re.search(rf'\b{obj}\b', clean_text, re.IGNORECASE) for obj in self.common_db_objects):
                return False, "DROP without valid object type"
            
            return True, f"Valid SQL {command} statement"
            
        # Check for SQL clauses that suggest it's part of a SQL query
        clause_matches = self.clause_pattern.findall(clean_text)
        if len(clause_matches) >= 2:  # Multiple SQL clauses suggest real SQL
            return True, f"Contains multiple SQL clauses: {', '.join(clause_matches[:3])}"
        
        # Look for SQL syntax elements
        syntax_matches = self.syntax_pattern.findall(clean_text)
        if len(syntax_matches) >= 3:  # Multiple SQL syntax elements suggest real SQL
            return True, f"Contains multiple SQL syntax elements"
        
        # If we've reached here, not enough evidence it's SQL
        return False, "Insufficient SQL syntax markers"
    
    def _remove_string_literals(self, text: str) -> str:
        """Remove string literals from text to avoid false positives in quoted content"""
        # Replace content inside single quotes
        text = re.sub(r"'[^']*'", "''", text)
        # Replace content inside double quotes that aren't SQL identifiers
        # (SQL identifiers in quotes usually don't contain spaces)
        text = re.sub(r'"[^"]*\s[^"]*"', '""', text)
        return text
    
    def get_query_type(self, query_text: str) -> str:
        """
        Determine the type of a validated SQL query
        """
        if not query_text:
            return "UNKNOWN"
            
        # Clean up and normalize query text
        query_start = query_text.lstrip().upper()
        
        # WITH clause could be a CTE (Common Table Expression)
        if query_start.startswith('WITH'):
            # Try to find the main command after the CTE
            match = re.search(r'WITH\s+.+?(?:\s+,\s+.+?)*?\s+(SELECT|INSERT|UPDATE|DELETE|MERGE)\s+', 
                            query_start, re.DOTALL)
            if match:
                return match.group(1)
            return "WITH"  # It's a WITH statement without a clear following command
        
        # Check for common SQL commands
        for command in self.sql_commands:
            if query_start.startswith(command):
                return command
        
        # If we can't determine the type, return UNKNOWN
        return "UNKNOWN"
    
    def extract_statement_from_string_literal(self, text: str) -> str:
        """
        Extract the actual SQL statement from a string literal found in code
        - Handles escaped quotes, concatenation, etc.
        """
        # Remove leading/trailing quotes if present
        text = text.strip()
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
            
        # Replace escaped quotes with regular quotes
        text = text.replace("\\'", "'").replace('\\"', '"')
        
        # Remove string concatenation artifacts
        text = re.sub(r'"\s*\+\s*"', '', text)
        text = re.sub(r'"\s*\+\s*\n\s*"', ' ', text)
        
        return text