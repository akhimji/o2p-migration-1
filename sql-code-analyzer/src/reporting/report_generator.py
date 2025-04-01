from typing import List, Dict
from models.sql_query import SQLQuery
from analyzers.sql_analyzer import SQLAnalyzer

class ReportGenerator:
    """Generates reports based on SQL analysis"""
    
    def __init__(self):
        self.analyzer = SQLAnalyzer()
        
    def generate_summary_report(self, queries: List[SQLQuery]) -> str:
        """Generate a summary report of SQL queries"""
        if not queries:
            return "No SQL queries found."
            
        stats = self.analyzer.get_query_statistics(queries)
        
        # Build the report
        report = []
        report.append(f"Total SQL queries found: {stats['total_queries']}")
        report.append("\nQuery Types:")
        for query_type, count in stats["query_types"].items():
            report.append(f"  {query_type}: {count}")
            
        report.append("\nMost Accessed Tables:")
        sorted_tables = sorted(stats["tables_accessed"].items(), key=lambda x: x[1], reverse=True)
        for table, count in sorted_tables[:10]:  # Top 10
            report.append(f"  {table}: {count} queries")
            
        report.append(f"\nAverage Query Complexity: {stats['avg_complexity']:.2f}")
        
        # Add some example queries
        report.append("\nExample Queries:")
        for i, query in enumerate(queries[:3]):  # First 3 as examples
            report.append(f"\n{i+1}. {query.query_type} query from {query.source_file}:")
            truncated_query = (query.query_text[:97] + '...') if len(query.query_text) > 100 else query.query_text
            report.append(f"   {truncated_query}")
            
        return "\n".join(report)
    
    def generate_detailed_report(self, queries: List[SQLQuery]) -> str:
        """Generate a detailed report of SQL queries"""
        # More detailed report implementation
        pass