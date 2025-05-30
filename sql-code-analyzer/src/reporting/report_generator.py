import json
from typing import List, Dict, Any
import re
from models.sql_query import SQLQuery
from analyzers.sql_analyzer import SQLAnalyzer
# Add Oracle detector import
from parsers.oracle_detector import OracleFeatureDetector

class ReportGenerator:
    """Generate reports from SQL query analysis"""
    
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
    
    def generate_json_report(self, queries: List[SQLQuery], tech_stack_info: Dict = None, connection_strings: List[str] = None, output_file: str = None) -> str:
        """
        Generate a JSON report of SQL queries with Oracle feature detection
        
        Args:
            queries: List of SQL query objects
            tech_stack_info: Dictionary with tech stack detection results
            connection_strings: List of detected connection strings
            output_file: Path to save the JSON report
            
        Returns:
            JSON string of the report
        """
        # Convert queries to dictionaries
        queries_dict = [query.to_dict() for query in queries]
        
        # Create summary section
        summary = {
            "total_queries": len(queries),
            "query_types": self._count_query_types(queries),
            "oracle_specific_queries": sum(1 for q in queries if q.is_oracle_specific),
            "oracle_features": self._summarize_oracle_features(queries)
        }
        
        # Complete report structure
        report = {
            "summary": summary,
            "queries": queries_dict
        }
        
        # Add tech stack info if available
        if tech_stack_info:
            report["tech_stack"] = tech_stack_info
        
        # Add connection strings if available
        if connection_strings:
            report["connection_strings"] = connection_strings
        
        # Format as JSON
        json_data = json.dumps(report, indent=2)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_data)
        
        return json_data
    
    def generate_html_report(self, queries: List[SQLQuery], tech_stack_info: Dict = None, connection_strings: List[str] = None, output_file: str = None) -> str:
        """
        Generate an HTML report of SQL queries with Oracle feature detection
        
        Args:
            queries: List of SQL query objects
            tech_stack_info: Dictionary with tech stack detection results
            connection_strings: List of detected connection strings
            output_file: Path to save the HTML report
            
        Returns:
            HTML string of the report
        """
        # Count types
        query_types = self._count_query_types(queries)
        
        # Get Oracle statistics
        oracle_queries = [q for q in queries if q.is_oracle_specific]
        oracle_features = self._summarize_oracle_features(queries)
        
        # Start building HTML content
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SQL Query Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
                h1, h2, h3 { color: #1a73e8; }
                .summary { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .query { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
                .query-text { background-color: #f8f9fa; padding: 10px; border-left: 3px solid #1a73e8; 
                              font-family: monospace; white-space: pre-wrap; overflow-x: auto; }
                .oracle-feature { background-color: #fff3cd; padding: 5px; margin: 5px 0; 
                                  border-left: 3px solid #ffc107; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .chart { width: 100%; height: 300px; margin-bottom: 20px; }
                .oracle-badge { background-color: #ff9800; color: white; padding: 3px 8px; 
                                border-radius: 12px; font-size: 0.85rem; }
                .conn-string { background-color: #e8f5e9; padding: 8px; border-left: 3px solid #4caf50;
                              font-family: monospace; margin: 5px 0; }
                .nav-tabs { display: flex; margin-bottom: 20px; overflow-x: auto; }
                .tab { padding: 10px 15px; cursor: pointer; border: 1px solid #ddd; 
                       background-color: #f8f9fa; white-space: nowrap; }
                .tab.active { background-color: #fff; border-bottom: none; 
                             font-weight: bold; color: #1a73e8; }
                .tab-content { display: none; }
                .tab-content.active { display: block; }
                .file-list { list-style-type: none; padding: 0; }
                .file-list li { padding: 5px 0; border-bottom: 1px solid #eee; }
                .oracle-summary { margin-top: 20px; }
                .tech-item { margin-bottom: 10px; }
                .tech-files { font-size: 0.9em; color: #666; margin-left: 15px; }
                .tech-files code {
                    display: block;
                    padding: 3px 0;
                }
                
                /* New styles for interactive components */
                .filter-controls {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                }
                
                .filter-group {
                    display: flex;
                    flex-direction: column;
                }
                
                .filter-group label {
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                .filter-select, .filter-input {
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    min-width: 150px;
                }
                
                .clear-filters {
                    margin-left: auto;
                    align-self: flex-end;
                    background-color: #f1f1f1;
                    border: 1px solid #ddd;
                    padding: 8px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                }
                
                .clear-filters:hover {
                    background-color: #e9e9e9;
                }
                
                /* Expandable sections */
                .expandable .toggle-icon {
                    cursor: pointer;
                    margin-left: 5px;
                    transition: transform 0.3s;
                    display: inline-block;
                }
                
                .expandable.collapsed .content {
                    display: none;
                }
                
                .expandable.collapsed .toggle-icon {
                    transform: rotate(-90deg);
                }
            </style>
        </head>
        <body>
            <h1>SQL Query Analysis Report</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Queries: <strong>""" + str(len(queries)) + """</strong></p>
                <p>Oracle-Specific Queries: <strong>""" + str(len(oracle_queries)) + """</strong></p>
                
                <h3>Query Types</h3>
                <table>
                    <tr>
                        <th>Type</th>
                        <th>Count</th>
                    </tr>
        """
        
        # Add query types to table
        for qtype, count in query_types.items():
            html += f"""
                    <tr>
                        <td>{qtype}</td>
                        <td>{count}</td>
                    </tr>
            """
            
        html += """
                </table>
        """
        
        # Add Oracle features if any were found
        if oracle_features:
            html += """
                <h3>Oracle Features</h3>
                <table>
                    <tr>
                        <th>Feature</th>
                        <th>Count</th>
                        <th>Description</th>
                    </tr>
            """
            
            # Add Oracle features to table
            for feature in oracle_features:
                html += f"""
                        <tr>
                            <td>{feature['name']}</td>
                            <td>{feature['count']}</td>
                            <td>{feature['description']}</td>
                        </tr>
                """
                
            html += """
                </table>
            """
        
        html += """
            </div>
            
            <div class="nav-tabs">
                <div class="tab active" onclick="showTab('all-queries')">All Queries</div>
                <div class="tab" onclick="showTab('oracle-queries')">Oracle Queries</div>
                <div class="tab" onclick="showTab('files')">Files</div>
                <div class="tab" onclick="showTab('oracle-features')">Oracle Features</div>
                <div class="tab" onclick="showTab('tech-stack')">Tech Stack</div>
                <div class="tab" onclick="showTab('connection-strings')">Connection Strings</div>
                <div class="tab" onclick="showTab('high-risk-tables')">High-Risk Tables</div>
            </div>
            
            <div id="all-queries" class="tab-content active">
                <h2>All SQL Queries</h2>
                
                <!-- Add filter controls -->
                <div class="filter-controls">
                    <div class="filter-group">
                        <label for="query-type-filter">Query Type:</label>
                        <select id="query-type-filter" class="filter-select">
                            <option value="all">All Types</option>
"""
        # Add options for each query type
        for qtype in query_types.keys():
            html += f'<option value="{qtype}">{qtype}</option>\n'

        html += """
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label for="table-filter">Table Name:</label>
                        <input type="text" id="table-filter" class="filter-input" placeholder="Filter by table">
                    </div>
                    
                    <div class="filter-group">
                        <label for="file-filter">Source File:</label>
                        <input type="text" id="file-filter" class="filter-input" placeholder="Filter by file path">
                    </div>
                    
                    <div class="filter-group">
                        <label for="text-filter">SQL Text:</label>
                        <input type="text" id="text-filter" class="filter-input" placeholder="Search in SQL text">
                    </div>
                    
                    <button class="clear-filters" onclick="clearFilters()">Clear Filters</button>
                </div>
        """
        
        # Add all queries with expandable sections and data attributes for filtering
        for i, query in enumerate(queries, 1):
            oracle_badge = f'<span class="oracle-badge">Oracle: {query.oracle_feature_count}</span>' if query.is_oracle_specific else ''
            tables_str = ', '.join(query.tables) if query.tables else 'Unknown'
            query_type = query.query_type if hasattr(query, 'query_type') else "UNKNOWN"
            
            html += f"""
                <div class="query expandable" 
                     data-query-type="{query_type}" 
                     data-tables="{tables_str.lower()}" 
                     data-file="{query.source_file.lower()}" 
                     id="query-{i}">
                    <h3 onclick="toggleExpand(this.parentElement)">
                        Query #{i} [{query_type}] {oracle_badge}
                        <span class="toggle-icon">▼</span>
                    </h3>
                    <div class="content">
                        <p>File: {query.source_file}</p>
                        <p>Tables: {tables_str}</p>
                        <pre class="query-text">{query.query_text}</pre>
            """
            
            if query.is_oracle_specific:
                html += """
                        <h4>Oracle Features</h4>
                """
                
                for feature in query.oracle_features:
                    html += f"""
                        <div class="oracle-feature">
                            <strong>{feature['name']}</strong>: {feature['description']}
                            <p>Example: <code>{feature['example']}</code></p>
                        </div>
                    """
            
            html += """
                    </div>
                </div>
            """
        
        html += """
            </div>
        """
        
        # Oracle Queries tab
        html += """
            <div id="oracle-queries" class="tab-content">
                <h2>Oracle-Specific Queries</h2>
        """
        
        # Add Oracle queries
        if oracle_queries:
            for i, query in enumerate(oracle_queries, 1):
                html += f"""
                    <div class="query">
                        <h3>Oracle Query #{i} [{query.query_type}]</h3>
                        <p>File: {query.source_file}</p>
                        <p>Oracle Features: {query.oracle_feature_count}</p>
                        <pre class="query-text">{query.query_text}</pre>
                        <h4>Oracle Features</h4>
                """
                
                for feature in query.oracle_features:
                    html += f"""
                        <div class="oracle-feature">
                            <strong>{feature['name']}</strong>: {feature['description']}
                            <p>Example: <code>{feature['example']}</code></p>
                        </div>
                    """
                
                html += """
                    </div>
                """
        else:
            html += """
                <p>No Oracle-specific queries found.</p>
            """
        
        html += """
            </div>
        """
        
        # Files tab
        html += """
            <div id="files" class="tab-content">
                <h2>Files with SQL Queries</h2>
        """
        
        # Group queries by file
        files_dict = {}
        for query in queries:
            if query.source_file not in files_dict:
                files_dict[query.source_file] = []
            files_dict[query.source_file].append(query)
        
        # Add file list
        html += """
                <ul class="file-list">
        """
        
        for file, file_queries in files_dict.items():
            oracle_count = sum(1 for q in file_queries if q.is_oracle_specific)
            oracle_badge = f'<span class="oracle-badge">Oracle: {oracle_count}</span>' if oracle_count else ''
            
            html += f"""
                    <li>
                        <strong>{file}</strong> ({len(file_queries)} queries) {oracle_badge}
                    </li>
            """
        
        html += """
                </ul>
            </div>
        """
        
        # Oracle Features tab (if any features were found)
        if oracle_features:
            html += """
            <div id="oracle-features" class="tab-content">
                <h2>Oracle Features Analysis</h2>
                
                <div class="oracle-summary">
                    <h3>Oracle Feature Usage</h3>
                    <table>
                        <tr>
                            <th>Feature</th>
                            <th>Count</th>
                            <th>Description</th>
                            <th>Files</th>
                        </tr>
            """
            
            # Get files per Oracle feature
            feature_files = {}
            for query in queries:
                if not query.is_oracle_specific:
                    continue
                    
                for feature in query.oracle_features:
                    feature_name = feature['name']
                    if feature_name not in feature_files:
                        feature_files[feature_name] = set()
                    feature_files[feature_name].add(query.source_file)
            
            # Add Oracle features with file counts
            for feature in oracle_features:
                feature_name = feature['name']
                files = feature_files.get(feature_name, set())
                file_count = len(files)
                
                html += f"""
                            <tr>
                                <td>{feature_name}</td>
                                <td>{feature['count']}</td>
                                <td>{feature['description']}</td>
                                <td>{file_count} {'' if file_count == 1 else 'files'}</td>
                            </tr>
                """
            
            html += """
                    </table>
                </div>
            </div>
            """
        
        # Tech Stack tab (if info was provided)
        if tech_stack_info:
            html += """
            <div id="tech-stack" class="tab-content">
                <h2>Technology Stack</h2>
            """
            
            # Java tech stack
            if "java" in tech_stack_info or "spring" in tech_stack_info or "hibernate" in tech_stack_info:
                html += """
                <h3>Java Technologies</h3>
                """
                
                # Check for specific Java technologies
                for tech_name in ["java", "spring", "hibernate", "jpa", "mybatis", "jdbc_direct"]:
                    if tech_name in tech_stack_info and tech_stack_info[tech_name].get("detected", False):
                        tech_info = tech_stack_info[tech_name]
                        files = tech_info.get("files", [])
                        
                        html += f"""
                        <div class="tech-item">
                            <strong>{tech_name.replace('_', ' ').title()}</strong>: Detected
                        """
                        
                        if files:
                            html += """
                            <div class="tech-files">
                                Files:<br>
                            """
                            for file in files[:10]:  # Show first 10 files
                                html += f"<code>{file}</code><br>"
                            if len(files) > 10:
                                html += f"... and {len(files)-10} more files"
                            html += """
                            </div>
                            """
                            
                        html += """
                        </div>
                        """
                
                # Check for build systems
                for build_system in ["maven", "gradle"]:
                    if build_system in tech_stack_info and tech_stack_info[build_system].get("detected", False):
                        html += f"""
                        <div class="tech-item">
                            <strong>{build_system.title()} Build</strong>: Detected
                        </div>
                        """
            
            # .NET tech stack
            if "dotnet_framework" in tech_stack_info or "dotnet_core" in tech_stack_info:
                html += """
                <h3>.NET Technologies</h3>
                """
                
                # Check for specific .NET technologies
                for tech_name in ["dotnet_framework", "dotnet_core", "asp_net", "entity_framework", "dapper", "ado_net"]:
                    if tech_name in tech_stack_info and tech_stack_info[tech_name].get("detected", False):
                        tech_info = tech_stack_info[tech_name]
                        files = tech_info.get("files", [])
                        
                        html += f"""
                        <div class="tech-item">
                            <strong>{tech_name.replace('_', ' ').title()}</strong>: Detected
                        """
                        
                        if files:
                            html += """
                            <div class="tech-files">
                                Files:<br> 
                            """
                            for file in files[:10]:  # Show first 10 files instead of 3
                                html += f"<code>{file}</code><br>"  # Use <br> instead of commas
                            if len(files) > 10:
                                html += f"... and {len(files)-10} more files"  # Adjusted count
                            html += """
                            </div>
                            """
                            
                        html += """
                        </div>
                        """
            
            html += """
            </div>
            """
        
        # Connection Strings tab (if any were provided)
        html += """
        <div id="connection-strings" class="tab-content">
            <h2>Connection Strings</h2>
        """
        
        if connection_strings:
            for conn in connection_strings:
                # Safely handle both dictionary and string formats
                if isinstance(conn, dict):
                    name = conn.get('name', 'Unnamed Connection')
                    source = conn.get('source_file', 'Unknown')
                    db_type = conn.get('database_type', 'Unknown database')
                    conn_string = conn.get('connection_string', '')
                else:
                    # If it's not a dictionary (e.g., a string), use defaults
                    name = 'Unnamed Connection'
                    source = 'Unknown'
                    db_type = 'Unknown database'
                    conn_string = str(conn) if conn else ''
                
                # Display the connection string
                html += f"""
                <div class="conn-string-item">
                    <h3>{name}</h3>
                    <p><strong>Source:</strong> {source}</p>
                    <p><strong>Type:</strong> {db_type}</p>
                    <div class="conn-string">{self._sanitize_connection_string(conn_string)}</div>
                </div>
                """
        else:
            html += "<p>No connection strings found in this project.</p>"
            
        html += """
        </div>
        
        <!-- High-Risk Tables tab -->
        <div id="high-risk-tables" class="tab-content">
            <h2>High-Risk Tables</h2>
            <p>Tables referenced in multiple queries represent potential migration risks, especially in complex applications.</p>
            
            <table>
                <tr>
                    <th>Table Name</th>
                    <th>Query Count</th>
                    <th>Query Types</th>
                    <th>Risk Level</th>
                </tr>
"""

        # Calculate table statistics
        table_stats = {}
        for query in queries:
            if hasattr(query, 'tables') and query.tables:
                for table in query.tables:
                    if table not in table_stats:
                        table_stats[table] = {
                            'count': 0,
                            'query_types': set()
                        }
                    table_stats[table]['count'] += 1
                    table_stats[table]['query_types'].add(query.query_type if hasattr(query, 'query_type') else "UNKNOWN")

        # Sort tables by query count (highest first)
        sorted_tables = sorted(table_stats.items(), key=lambda x: x[1]['count'], reverse=True)

        # Add top 20 most referenced tables to the table
        for table_name, stats in sorted_tables[:20]:
            query_count = stats['count']
            query_types = ', '.join(stats['query_types'])
            
            # Determine risk level based on query count
            if query_count > 15:
                risk_level = 'High'
                risk_color = '#dc3545'  # Red
            elif query_count > 8:
                risk_level = 'Medium'
                risk_color = '#ffc107'  # Yellow
            else:
                risk_level = 'Low'
                risk_color = '#28a745'  # Green
            
            html += f"""
                        <tr>
                            <td><strong>{table_name}</strong></td>
                            <td>{query_count}</td>
                            <td>{query_types}</td>
                            <td style="color: {risk_color}; font-weight: bold;">{risk_level}</td>
                        </tr>
            """

        html += """
            </table>
            
            <div style="margin-top: 20px;">
                <h3>Risk Assessment Criteria</h3>
                <ul>
                    <li><span style="color: #dc3545; font-weight: bold;">High Risk</span>: Tables referenced in more than 15 queries</li>
                    <li><span style="color: #ffc107; font-weight: bold;">Medium Risk</span>: Tables referenced in 8-15 queries</li>
                    <li><span style="color: #28a745; font-weight: bold;">Low Risk</span>: Tables referenced in fewer than 8 queries</li>
                </ul>
                <p><em>Note: Tables with different query types (SELECT, INSERT, UPDATE, DELETE) may require special attention 
                during migration as they might have more complex dependencies.</em></p>
            </div>
        </div>
        """
        
        # Add JavaScript for tab navigation
        html += """
            <script>
                function showTab(tabId) {
                    // Hide all tab contents
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    
                    // Deactivate all tabs
                    document.querySelectorAll('.tab').forEach(tab => {
                        tab.classList.remove('active');
                    });
                    
                    // Show selected tab content
                    document.getElementById(tabId).classList.add('active');
                    
                    // Activate the clicked tab
                    document.querySelector(`.tab[onclick="showTab('${tabId}')"]`).classList.add('active');
                }
                
                // Toggle expandable sections
                function toggleExpand(element) {
                    element.classList.toggle('collapsed');
                }
                
                // Filtering queries
                function filterQueries() {
                    const queryTypeFilter = document.getElementById('query-type-filter').value;
                    const tableFilter = document.getElementById('table-filter').value.toLowerCase();
                    const fileFilter = document.getElementById('file-filter').value.toLowerCase();
                    const textFilter = document.getElementById('text-filter').value.toLowerCase();
                    
                    document.querySelectorAll('.query').forEach(query => {
                        // Check if query matches all selected filters
                        const matchesType = queryTypeFilter === 'all' || query.getAttribute('data-query-type') === queryTypeFilter;
                        const matchesTable = tableFilter === '' || query.getAttribute('data-tables').includes(tableFilter);
                        const matchesFile = fileFilter === '' || query.getAttribute('data-file').includes(fileFilter);
                        const matchesText = textFilter === '' || query.querySelector('.query-text').textContent.toLowerCase().includes(textFilter);
                        
                        // Show or hide based on filter matches
                        if (matchesType && matchesTable && matchesFile && matchesText) {
                            query.style.display = '';
                        } else {
                            query.style.display = 'none';
                        }
                    });
                }
                
                // Clear all filters
                function clearFilters() {
                    document.getElementById('query-type-filter').value = 'all';
                    document.getElementById('table-filter').value = '';
                    document.getElementById('file-filter').value = '';
                    document.getElementById('text-filter').value = '';
                    
                    document.querySelectorAll('.query').forEach(query => {
                        query.style.display = '';
                    });
                }
                
                // Initialize event listeners
                document.addEventListener('DOMContentLoaded', function() {
                    // Set up filter change listeners
                    document.getElementById('query-type-filter').addEventListener('change', filterQueries);
                    document.getElementById('table-filter').addEventListener('input', filterQueries);
                    document.getElementById('file-filter').addEventListener('input', filterQueries);
                    document.getElementById('text-filter').addEventListener('input', filterQueries);
                    
                    // Collapse all query sections initially except first 3
                    const queries = document.querySelectorAll('.query.expandable');
                    for (let i = 3; i < queries.length; i++) {
                        queries[i].classList.add('collapsed');
                    }
                });
            </script>
        </body>
        </html>
        """
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(html)
        
        return html
    
    def _count_query_types(self, queries: List[SQLQuery]) -> Dict[str, int]:
        """Count the number of queries by type"""
        result = {}
        for query in queries:
            query_type = query.query_type or "UNKNOWN"
            if query_type in result:
                result[query_type] += 1
            else:
                result[query_type] = 1
        return result
    
    def _summarize_oracle_features(self, queries: List[SQLQuery]) -> List[Dict[str, Any]]:
        """Summarize Oracle features across all queries"""
        # Count features
        feature_counts = {}
        oracle_detector = OracleFeatureDetector()  # For descriptions
        
        for query in queries:
            if not query.is_oracle_specific:
                continue
                
            for feature in query.oracle_features:
                name = feature['name']
                if name in feature_counts:
                    feature_counts[name] += 1
                else:
                    feature_counts[name] = 1
        
        # Create summary list
        summary = []
        for name, count in feature_counts.items():
            summary.append({
                "name": name,
                "count": count,
                "description": oracle_detector.get_oracle_feature_details(name)
            })
        
        # Sort by frequency
        summary.sort(key=lambda x: x['count'], reverse=True)
        
        return summary
    
    def _sanitize_connection_string(self, conn_str: str) -> str:
        """Sanitize connection string to hide sensitive information"""
        if not conn_str or not isinstance(conn_str, str):
            return ""
            
        # Replace password in JDBC URLs
        sanitized = re.sub(r'password=([^;]+)', r'password=*****', conn_str, flags=re.IGNORECASE)
        
        # Replace password in key-value formatted strings
        sanitized = re.sub(r'Password=([^;]+)', r'Password=*****', sanitized, flags=re.IGNORECASE)
        
        # Replace password in connection strings with embedded credentials
        sanitized = re.sub(r'://[^:]+:([^@]+)@', r'://*****:*****@', sanitized)
        
        return sanitized