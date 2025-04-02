import re
from typing import Dict, List, Set, Tuple, Optional

class OracleFeatureDetector:
    """
    Detects Oracle-specific SQL constructs in queries
    """
    
    def __init__(self):
        # Oracle-specific keywords and features
        self.oracle_patterns = {
            # Syntax
            "connect_by": re.compile(r'\bCONNECT\s+BY\b', re.IGNORECASE),
            "start_with": re.compile(r'\bSTART\s+WITH\b', re.IGNORECASE),
            "pivot": re.compile(r'\bPIVOT\b', re.IGNORECASE),
            "unpivot": re.compile(r'\bUNPIVOT\b', re.IGNORECASE),
            "merge": re.compile(r'\bMERGE\s+INTO\b', re.IGNORECASE),
            
            # Oracle-specific joins
            "outer_join_operator": re.compile(r'(?:\s|=|\()\+\)', re.IGNORECASE),  # The old (+) outer join syntax
            
            # Oracle hints
            "optimizer_hint": re.compile(r'/\*\+.*?\*/', re.DOTALL),
            
            # Oracle-specific functions
            "decode": re.compile(r'\bDECODE\s*\(', re.IGNORECASE),
            "nvl": re.compile(r'\bNVL\s*\(', re.IGNORECASE),
            "nvl2": re.compile(r'\bNVL2\s*\(', re.IGNORECASE),
            "instr": re.compile(r'\bINSTR\s*\(', re.IGNORECASE),
            "regexp_like": re.compile(r'\bREGEXP_LIKE\s*\(', re.IGNORECASE),
            
            # Date functions
            "to_date": re.compile(r'\bTO_DATE\s*\(', re.IGNORECASE),
            "add_months": re.compile(r'\bADD_MONTHS\s*\(', re.IGNORECASE),
            "months_between": re.compile(r'\bMONTHS_BETWEEN\s*\(', re.IGNORECASE),
            
            # Sequence usage
            "sequence_nextval": re.compile(r'\b\w+\.NEXTVAL\b', re.IGNORECASE),
            "sequence_currval": re.compile(r'\b\w+\.CURRVAL\b', re.IGNORECASE),
            
            # Oracle-specific data types
            "varchar2": re.compile(r'\bVARCHAR2\b', re.IGNORECASE),
            "number": re.compile(r'\bNUMBER\s*\(', re.IGNORECASE),
            "rowid": re.compile(r'\bROWID\b', re.IGNORECASE),
            "clob": re.compile(r'\bCLOB\b', re.IGNORECASE),
            "blob": re.compile(r'\bBLOB\b', re.IGNORECASE),
            
            # Analytical functions
            "analytic_function": re.compile(r'\bOVER\s*\(PARTITION\s+BY\b', re.IGNORECASE),
            
            # Oracle-specific table hints
            "table_hint": re.compile(r'/\*\+\s*(?:FULL|INDEX|NO_INDEX|USE_HASH|ORDERED)\s*\(', re.IGNORECASE),
            
            # Oracle-specific system tables/views
            "dual_table": re.compile(r'\bFROM\s+DUAL\b', re.IGNORECASE),
            "system_tables": re.compile(r'\bFROM\s+(?:USER_|ALL_|DBA_|V\$)\w+\b', re.IGNORECASE),
            
            # PL/SQL elements in SQL
            "plsql_table": re.compile(r'\bTABLE\s*\(\s*\w+\s*\)', re.IGNORECASE),
            
            # Flashback
            "flashback_query": re.compile(r'\bAS\s+OF\s+(?:SCN|TIMESTAMP)\b', re.IGNORECASE),
            
            # Administrative
            "alter_system": re.compile(r'\bALTER\s+SYSTEM\b', re.IGNORECASE),
            
            # Oracle SQL*Plus commands
            "sqlplus_command": re.compile(r'^\s*(?:SET|SHOW|SPOOL|DESC|DESCRIBE|EXEC|EXECUTE|WHENEVER)\b', re.IGNORECASE)
        }
        
        # Descriptions for Oracle features (for user-friendly reporting)
        self.feature_descriptions = {
            "connect_by": "Hierarchical queries using CONNECT BY",
            "start_with": "Hierarchical query starting condition",
            "pivot": "PIVOT operator for transforming rows to columns",
            "unpivot": "UNPIVOT operator for transforming columns to rows",
            "merge": "Oracle MERGE statement",
            "outer_join_operator": "Oracle old-style outer join syntax (+)",
            "optimizer_hint": "Oracle optimizer hint /*+ ... */",
            "decode": "DECODE function",
            "nvl": "NVL function for null handling",
            "nvl2": "NVL2 function for extended null handling",
            "instr": "INSTR string position function",
            "regexp_like": "REGEXP_LIKE for regex pattern matching",
            "to_date": "TO_DATE function",
            "add_months": "ADD_MONTHS date function",
            "months_between": "MONTHS_BETWEEN date function",
            "sequence_nextval": "Sequence NEXTVAL reference",
            "sequence_currval": "Sequence CURRVAL reference",
            "varchar2": "VARCHAR2 data type",
            "number": "NUMBER data type",
            "rowid": "ROWID data type or pseudo-column",
            "clob": "CLOB data type",
            "blob": "BLOB data type",
            "analytic_function": "Analytical function with PARTITION BY",
            "table_hint": "Oracle-specific table access hint",
            "dual_table": "Query using the DUAL table",
            "system_tables": "Oracle system tables/views (USER_*, ALL_*, DBA_*, V$)",
            "plsql_table": "TABLE() operator with collection",
            "flashback_query": "Flashback query",
            "alter_system": "ALTER SYSTEM administrative command",
            "sqlplus_command": "SQL*Plus specific command"
        }
    
    def detect_oracle_features(self, query_text: str) -> Dict[str, List[str]]:
        """
        Identify Oracle-specific features used in a query
        
        Returns:
            A dictionary with feature names and their usage examples
        """
        if not query_text:
            return {}
            
        results = {}
        
        # Check each pattern
        for feature_name, pattern in self.oracle_patterns.items():
            matches = pattern.findall(query_text)
            if matches:
                # Store up to 3 examples of each feature usage
                results[feature_name] = [m.strip() if isinstance(m, str) else m for m in matches[:3]]
        
        return results
    
    def is_oracle_specific_query(self, query_text: str) -> bool:
        """Check if a query contains Oracle-specific constructs"""
        features = self.detect_oracle_features(query_text)
        return len(features) > 0
    
    def get_oracle_feature_details(self, feature_name: str) -> str:
        """Get a user-friendly description of an Oracle feature"""
        return self.feature_descriptions.get(feature_name, "Oracle-specific feature")
    
    def summarize_oracle_features(self, query_text: str) -> List[Dict[str, str]]:
        """
        Summarize Oracle features found in a query in a format suitable for reports
        
        Returns:
            List of dicts with feature name, description, and example
        """
        features = self.detect_oracle_features(query_text)
        summary = []
        
        for feature_name, examples in features.items():
            description = self.get_oracle_feature_details(feature_name)
            example = examples[0] if examples else ""
            
            summary.append({
                "name": feature_name,
                "description": description,
                "example": example
            })
        
        return summary