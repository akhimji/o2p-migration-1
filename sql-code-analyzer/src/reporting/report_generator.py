from typing import List, Dict, Any
import re
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
    
    def generate_config_report(self, config_info: Dict[str, Any]) -> str:
        """Generate a report of configuration findings"""
        report = []
        
        # Database connections section
        report.append("\n== Database Connections ==")
        if config_info["connection_strings"]:
            report.append(f"Found {len(config_info['connection_strings'])} connection strings:")
            
            for i, conn in enumerate(config_info["connection_strings"][:5], 1):  # Show first 5
                report.append(f"\n{i}. {conn.get('name', 'Unnamed')} ({conn.get('database_type', 'Unknown database')})")
                report.append(f"   Source: {conn.get('source_file', 'Unknown')}")
                
                # Show a sanitized version of the connection string
                if 'connection_string' in conn:
                    sanitized = self._sanitize_connection_string(conn['connection_string'])
                    report.append(f"   Connection: {sanitized}")
            
            if len(config_info["connection_strings"]) > 5:
                report.append(f"\n...and {len(config_info['connection_strings']) - 5} more connection strings")
        else:
            report.append("No connection strings found.")
        
        # Databases section
        report.append("\n== Detected Databases ==")
        if config_info["databases"]:
            for db in sorted(config_info["databases"]):
                report.append(f"- {db.upper()}")
        else:
            report.append("No specific database technologies detected.")
        
        # Dependencies section
        report.append("\n== Key Dependencies ==")
        for dep_type, deps in config_info["dependencies"].items():
            if deps:
                report.append(f"\n{dep_type.upper()} Dependencies:")
                
                # For Maven/Gradle dependencies
                if dep_type in ['maven', 'gradle']:
                    # Group by groupId
                    groups = {}
                    for dep in deps:
                        group = dep.get('groupId', 'unknown')
                        if group not in groups:
                            groups[group] = []
                        groups[group].append(dep)
                    
                    # Show top groups
                    top_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]
                    for group, group_deps in top_groups:
                        report.append(f"- {group}: {len(group_deps)} artifacts")
                
                # For npm dependencies
                elif dep_type == 'npm':
                    # Count by type
                    prod_deps = [d for d in deps if d.get('type') == 'dependencies']
                    dev_deps = [d for d in deps if d.get('type') == 'devDependencies']
                    report.append(f"- {len(prod_deps)} production dependencies")
                    report.append(f"- {len(dev_deps)} development dependencies")
        
        return "\n".join(report)
    
    def _sanitize_connection_string(self, conn_str: str) -> str:
        """Sanitize connection string to hide sensitive information"""
        # Replace password in JDBC URLs
        sanitized = re.sub(r'password=([^;]+)', r'password=*****', conn_str, flags=re.IGNORECASE)
        
        # Replace password in key-value formatted strings
        sanitized = re.sub(r'Password=([^;]+)', r'Password=*****', sanitized, flags=re.IGNORECASE)
        
        # Replace password in connection strings with embedded credentials
        sanitized = re.sub(r'://[^:]+:([^@]+)@', r'://*****:*****@', sanitized)
        
        return sanitized