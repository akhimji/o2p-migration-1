from typing import List, Dict
import logging
from models.sql_query import SQLQuery

logger = logging.getLogger('SQLAnalyzer')

class SQLAnalyzer:
    """Analyzer for SQL queries that extracts insights and metrics"""
    
    def __init__(self):
        pass
        
    def calculate_complexity(self, query: SQLQuery) -> float:
        """Calculate a simple complexity score for a SQL query"""
        if not query or not hasattr(query, 'query_text') or not query.query_text:
            return 1.0  # Default complexity
        
        # Very simple complexity calculation - just for demonstration
        complexity = 1.0
        query_upper = query.query_text.upper()
        
        # More complex if it has joins
        if "JOIN" in query_upper:
            complexity += 1.0
            
        # More complex if it has subqueries - safely check
        parts = query_upper.split("SELECT")
        if len(parts) > 1 and len(parts[0]) > 0:
            complexity += 2.0
        
        # More complex if it has aggregations
        for agg in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]:
            if agg in query_upper:
                complexity += 0.5
        
        return complexity
    
    def analyze_query(self, query: SQLQuery) -> SQLQuery:
        """Analyze a single SQL query"""
        try:
            if not query.parsed:
                logger.warning(f"Query not parsed before analysis: {query.query_text[:50]}...")
                return query
                
            # Calculate complexity
            query.complexity_score = self.calculate_complexity(query)
            
            return query
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Return the original query without modification
            return query
    
    def detect_join_types(self, query: SQLQuery) -> Dict[str, bool]:
        """
        Detect different types of joins in a SQL query
        Returns a dictionary with join types and boolean values
        """
        query_text = query.query_text.upper()
        
        join_types = {
            "inner_join": False,
            "left_join": False,
            "right_join": False,
            "full_join": False, 
            "cross_join": False,
            "natural_join": False,
            "self_join": False,
            "multiple_joins": False
        }
        
        # Check for various join types
        join_types["inner_join"] = " JOIN " in query_text or " INNER JOIN " in query_text
        join_types["left_join"] = " LEFT JOIN " in query_text or " LEFT OUTER JOIN " in query_text
        join_types["right_join"] = " RIGHT JOIN " in query_text or " RIGHT OUTER JOIN " in query_text
        join_types["full_join"] = " FULL JOIN " in query_text or " FULL OUTER JOIN " in query_text
        join_types["cross_join"] = " CROSS JOIN " in query_text
        join_types["natural_join"] = " NATURAL JOIN " in query_text
        
        # Count the number of joins
        join_count = query_text.count(" JOIN ")
        join_types["multiple_joins"] = join_count > 1
        
        # Detect self joins (same table joined to itself)
        if join_count > 0 and query.tables:
            table_occurrences = {}
            for table in query.tables:
                table_occurrences[table] = query_text.count(table.upper())
                # If a table appears multiple times in a query with joins, it's likely a self join
                if table_occurrences[table] > 1 and any(join_types.values()):
                    join_types["self_join"] = True
        
        return join_types

    def determine_query_complexity(self, query: SQLQuery) -> int:
        """
        Calculate the complexity score of a SQL query based on various factors
        Higher score means more complex query
        """
        complexity = 0
        
        # Base complexity by query type
        if query.query_type in ["SELECT", "WITH"]:
            complexity += 1  # Base score for SELECT/WITH
        
        # Add complexity for each table referenced (more tables = more complex)
        if hasattr(query, 'tables'):
            table_count = len(query.tables)
            if table_count > 1:
                complexity += min(3, table_count - 1)  # Up to +3 for multiple tables
        
        # Add complexity for WHERE conditions
        if hasattr(query, 'where_conditions') and query.where_conditions:
            condition_count = len(query.where_conditions)
            complexity += min(2, condition_count // 2)  # Up to +2 for multiple conditions
        
        # Add complexity for Oracle-specific features
        if query.is_oracle_specific:
            complexity += min(3, query.oracle_feature_count)  # Up to +3 for Oracle features
        
        # Check for advanced SQL features in the query text
        query_text = query.query_text.upper()
        
        # Check for JOIN operations
        if " JOIN " in query_text:
            # Simple check for the number of joins
            join_count = query_text.count(" JOIN ")
            complexity += min(3, join_count)  # Up to +3 for multiple joins
            
            # Check for complex join types
            if " OUTER JOIN " in query_text or " LEFT JOIN " in query_text or " RIGHT JOIN " in query_text:
                complexity += 1
            if " FULL JOIN " in query_text or " FULL OUTER JOIN " in query_text:
                complexity += 2
            if " CROSS JOIN " in query_text:
                complexity += 2
        
        # Check for other complex features
        if " GROUP BY " in query_text:
            complexity += 1
        if " HAVING " in query_text:
            complexity += 1
        if " UNION " in query_text or " INTERSECT " in query_text or " EXCEPT " in query_text:
            complexity += 2
        if " CASE " in query_text:
            complexity += 1
        if "SUBQUERY" in query_text or "SUB-QUERY" in query_text or query_text.count("SELECT ") > 1:
            complexity += 2
        
        return complexity

    def analyze_queries(self, queries: List[SQLQuery]) -> List[SQLQuery]:
        """
        Analyze a list of SQL queries
        """
        analyzed_queries = []
        
        for query in queries:
            # Ensure basic properties are set
            if not hasattr(query, 'complexity'):
                query.complexity = 0
            
            if not hasattr(query, 'has_joins'):
                query.has_joins = False
                
            if not hasattr(query, 'join_count'):
                query.join_count = 0
                
            if not hasattr(query, 'join_types'):
                query.join_types = {}
            
            # Determine query complexity
            query.complexity = self.determine_query_complexity(query)
            
            # Simple join detection
            query_text = query.query_text.upper()
            query.has_joins = " JOIN " in query_text
            query.join_count = query_text.count(" JOIN ")
            
            # Simple join types detection
            query.join_types = {
                "inner_join": " INNER JOIN " in query_text or (" JOIN " in query_text and 
                                                              " LEFT " not in query_text and 
                                                              " RIGHT " not in query_text and
                                                              " FULL " not in query_text and
                                                              " CROSS " not in query_text),
                "left_join": " LEFT JOIN " in query_text or " LEFT OUTER JOIN " in query_text,
                "right_join": " RIGHT JOIN " in query_text or " RIGHT OUTER JOIN " in query_text,
                "full_join": " FULL JOIN " in query_text or " FULL OUTER JOIN " in query_text,
                "cross_join": " CROSS JOIN " in query_text,
                "natural_join": " NATURAL JOIN " in query_text,
                "self_join": False,  # Will determine this later if needed
                "multiple_joins": query_text.count(" JOIN ") > 1
            }
            
            analyzed_queries.append(query)
        
        return analyzed_queries
    
    def get_query_statistics(self, queries: List[SQLQuery]) -> Dict:
        """Get statistics about the analyzed queries"""
        stats = {
            "total_queries": len(queries),
            "query_types": {},
            "tables_accessed": {},
            "avg_complexity": 0
        }
        
        # Count query types
        for query in queries:
            query_type = query.query_type or "UNKNOWN"
            stats["query_types"][query_type] = stats["query_types"].get(query_type, 0) + 1
            
            # Count table access (safely)
            if hasattr(query, 'tables') and query.tables:
                for table in query.tables:
                    stats["tables_accessed"][table] = stats["tables_accessed"].get(table, 0) + 1
        
        # Calculate average complexity
        if queries:
            complexities = [query.complexity_score for query in queries if hasattr(query, 'complexity_score') and query.complexity_score is not None]
            if complexities:
                stats["avg_complexity"] = sum(complexities) / len(complexities)
            
        return stats