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
    
    def analyze_queries(self, queries: List[SQLQuery]) -> List[SQLQuery]:
        """Analyze a list of SQL queries"""
        analyzed = []
        for query in queries:
            try:
                analyzed_query = self.analyze_query(query)
                analyzed.append(analyzed_query)
            except Exception as e:
                logger.error(f"Failed to analyze query: {e}")
                # Include the original query to maintain the count
                analyzed.append(query)
        return analyzed
    
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