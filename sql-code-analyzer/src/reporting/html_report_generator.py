import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger('HTMLReportGenerator')

class HTMLReportGenerator:
    """Generate HTML reports from analysis results"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
    
    def generate_html_report(self, 
                           sql_queries: List[Dict],
                           tech_stack: Dict[str, Any], 
                           connection_strings: List[Dict],
                           dependencies: Dict[str, List],
                           project_type: str,
                           project_path: str) -> str:
        """
        Generate an HTML report from the analysis data
        """
        logger.info("Generating HTML report")
        
        # Create basic stats
        query_count = len(sql_queries)
        query_types = {}
        tables = {}
        
        for query in sql_queries:
            query_type = query.get('query_type', 'UNKNOWN')
            query_types[query_type] = query_types.get(query_type, 0) + 1
            
            for table in query.get('tables', []):
                tables[table] = tables.get(table, 0) + 1
        
        # Sort tables by usage count
        sorted_tables = sorted(tables.items(), key=lambda x: x[1], reverse=True)
        
        # Date and time for the report
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create HTML content
        html = self._generate_html_structure(
            project_path=project_path,
            project_type=project_type,
            timestamp=now,
            sql_stats={
                'query_count': query_count,
                'query_types': query_types,
                'tables': sorted_tables[:20]  # Top 20 tables
            },
            tech_stack=tech_stack,
            connection_strings=connection_strings,
            dependencies=dependencies,
            queries=sql_queries[:100]  # Limit to 100 queries for performance
        )
        
        return html
    
    def write_html_report(self, html_content: str, output_path: Path) -> Path:
        """Write HTML report to file"""
        output_file = output_path
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report written to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error writing HTML report: {e}")
            return None
    
    def _generate_html_structure(self, 
                               project_path: str,
                               project_type: str,
                               timestamp: str,
                               sql_stats: Dict[str, Any],
                               tech_stack: Dict[str, Any],
                               connection_strings: List[Dict],
                               dependencies: Dict[str, List],
                               queries: List[Dict]) -> str:
        """Generate the full HTML document"""
        
        # Databases found
        databases = []
        if "databases" in tech_stack and isinstance(tech_stack["databases"], dict):
            databases = tech_stack["databases"].get("types", [])
        
        # Create HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Code Analysis - {os.path.basename(project_path)}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SQL Code Analysis Report</h1>
            <div class="project-info">
                <p><strong>Project:</strong> {os.path.basename(project_path)}</p>
                <p><strong>Type:</strong> {project_type.upper()}</p>
                <p><strong>Generated:</strong> {timestamp}</p>
            </div>
        </header>
        
        <main>
            <!-- Dashboard -->
            <section class="dashboard">
                <h2>Dashboard</h2>
                <div class="stats-container">
                    <div class="stat-card">
                        <h3>{sql_stats['query_count']}</h3>
                        <p>SQL Queries</p>
                    </div>
                    <div class="stat-card">
                        <h3>{len(sql_stats['tables'])}</h3>
                        <p>Tables Used</p>
                    </div>
                    <div class="stat-card">
                        <h3>{len(databases)}</h3>
                        <p>Databases</p>
                    </div>
                    <div class="stat-card">
                        <h3>{len(connection_strings)}</h3>
                        <p>Connection Strings</p>
                    </div>
                </div>
            </section>
            
            <!-- SQL Analysis -->
            <section>
                <div class="section-header collapsible" onclick="toggleSection(this)">
                    <h2>SQL Analysis</h2>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="section-content">
                    <h3>Query Types</h3>
                    <div class="chart-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Count</th>
                                    <th>Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_query_type_rows(sql_stats['query_types'], sql_stats['query_count'])}
                            </tbody>
                        </table>
                    </div>
                    
                    <h3>Top Tables Used</h3>
                    <div class="chart-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Table Name</th>
                                    <th>Query Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_table_rows(sql_stats['tables'])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
            
            <!-- Technology Stack -->
            <section>
                <div class="section-header collapsible" onclick="toggleSection(this)">
                    <h2>Technology Stack</h2>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="section-content">
                    <div class="tech-stack">
                        {self._generate_tech_stack_html(tech_stack)}
                    </div>
                    
                    <h3>Detected Databases</h3>
                    <div class="database-list">
                        {self._generate_database_list(databases)}
                    </div>
                </div>
            </section>
            
            <!-- Connection Strings -->
            <section>
                <div class="section-header collapsible" onclick="toggleSection(this)">
                    <h2>Connection Strings</h2>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="section-content">
                    {self._generate_connection_strings_html(connection_strings)}
                </div>
            </section>
            
            <!-- Dependencies -->
            <section>
                <div class="section-header collapsible" onclick="toggleSection(this)">
                    <h2>Dependencies</h2>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="section-content">
                    {self._generate_dependencies_html(dependencies)}
                </div>
            </section>
            
            <!-- SQL Queries -->
            <section>
                <div class="section-header collapsible" onclick="toggleSection(this)">
                    <h2>SQL Queries</h2>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="section-content">
                    <div class="query-filter">
                        <label for="query-type-filter">Filter by type:</label>
                        <select id="query-type-filter" onchange="filterQueries()">
                            <option value="">All Types</option>
                            {self._generate_query_type_options(sql_stats['query_types'])}
                        </select>
                        
                        <label for="query-search">Search:</label>
                        <input type="text" id="query-search" onkeyup="filterQueries()" placeholder="Search queries...">
                    </div>
                    
                    <div class="queries-container">
                        {self._generate_queries_html(queries)}
                    </div>
                </div>
            </section>
        </main>
        
        <footer>
            <p>Generated by SQL Code Analyzer</p>
            <p>&copy; {datetime.now().year}</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        return html
    
    def _generate_query_type_rows(self, query_types: Dict[str, int], total_count: int) -> str:
        """Generate HTML rows for query types"""
        html = ""
        for q_type, count in sorted(query_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            html += f"""
                <tr>
                    <td>{q_type or "UNKNOWN"}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>"""
        return html
    
    def _generate_table_rows(self, tables: List[tuple]) -> str:
        """Generate HTML rows for tables"""
        html = ""
        for table_name, count in tables:
            html += f"""
                <tr>
                    <td>{table_name}</td>
                    <td>{count}</td>
                </tr>"""
        return html
    
    def _generate_tech_stack_html(self, tech_stack: Dict[str, Any]) -> str:
        """Generate HTML for tech stack"""
        html = "<div class='tech-grid'>"
        
        # Process frameworks and build tools
        for tech, info in tech_stack.items():
            if tech in ("databases", "connection_strings"):
                continue  # Handle these separately
                
            if isinstance(info, dict) and info.get("detected", False):
                html += f"""
                    <div class="tech-item detected">
                        <span class="tech-name">{tech.replace('_', ' ').title()}</span>
                        <span class="tech-check">✓</span>
                    </div>"""
            elif isinstance(info, bool) and info:
                html += f"""
                    <div class="tech-item detected">
                        <span class="tech-name">{tech.replace('_', ' ').title()}</span>
                        <span class="tech-check">✓</span>
                    </div>"""
        
        html += "</div>"
        return html
    
    def _generate_database_list(self, databases: List[str]) -> str:
        """Generate HTML for database list"""
        if not databases:
            return "<p>No databases detected</p>"
            
        html = "<div class='database-grid'>"
        for db in sorted(databases):
            html += f"""
                <div class="database-item">
                    <span class="database-name">{db.upper()}</span>
                </div>"""
        html += "</div>"
        return html
    
    def _generate_connection_strings_html(self, connection_strings: List[Dict]) -> str:
        """Generate HTML for connection strings"""
        if not connection_strings:
            return "<p>No connection strings found</p>"
        
        html = "<div class='conn-string-list'>"
        
        for i, conn in enumerate(connection_strings):
            sanitized_conn_str = self._sanitize_connection_string(conn.get('connection_string', ''))
            db_type = conn.get('database_type', 'Unknown').upper()
            source_file = conn.get('source_file', 'Unknown')
            name = conn.get('name', f'Connection {i+1}')
            
            html += f"""
                <div class="conn-item collapsible-card">
                    <div class="conn-header" onclick="toggleCard(this)">
                        <div class="conn-title">
                            <span class="db-type">{db_type}</span>
                            <span class="conn-name">{name}</span>
                        </div>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="conn-details">
                        <p><strong>Source:</strong> {source_file}</p>
                        <pre class="conn-string">{sanitized_conn_str}</pre>
                    </div>
                </div>"""
        
        html += "</div>"
        return html
    
    def _sanitize_connection_string(self, conn_str: str) -> str:
        """Sanitize connection string to hide sensitive information"""
        import re
        
        # Replace password in JDBC URLs
        sanitized = re.sub(r'password=([^;]+)', r'password=*****', conn_str, flags=re.IGNORECASE)
        
        # Replace password in key-value formatted strings
        sanitized = re.sub(r'Password=([^;]+)', r'Password=*****', sanitized, flags=re.IGNORECASE)
        
        # Replace password in connection strings with embedded credentials
        sanitized = re.sub(r'://[^:]+:([^@]+)@', r'://*****:*****@', sanitized)
        
        return sanitized
    
    def _generate_dependencies_html(self, dependencies: Dict[str, List]) -> str:
        """Generate HTML for dependencies"""
        if not dependencies:
            return "<p>No dependencies found</p>"
        
        html = ""
        
        for dep_type, deps in dependencies.items():
            if not deps:
                continue
                
            html += f"""
                <div class="dependency-section">
                    <div class="dep-header collapsible-card">
                        <div class="dep-title" onclick="toggleCard(this)">
                            <h3>{dep_type.upper()} Dependencies</h3>
                            <span class="toggle-icon">▼</span>
                        </div>
                    </div>
                    <div class="dep-content">"""
            
            # For Maven/Gradle dependencies
            if dep_type in ['maven', 'gradle']:
                # Group by groupId
                groups = {}
                for dep in deps:
                    group = dep.get('groupId', 'unknown')
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(dep)
                
                html += '<div class="dep-groups">'
                for group, group_deps in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                    html += f"""
                        <div class="dep-group collapsible-card">
                            <div class="group-header" onclick="toggleCard(this)">
                                <span class="group-name">{group}</span>
                                <span class="group-count">{len(group_deps)}</span>
                                <span class="toggle-icon">▼</span>
                            </div>
                            <div class="group-details">
                                <ul class="dep-list">"""
                    
                    for dep in group_deps[:20]:  # Limit to 20 deps per group
                        artifact = dep.get('artifactId', '')
                        version = dep.get('version', '')
                        html += f'<li>{artifact} <span class="version">{version}</span></li>'
                    
                    if len(group_deps) > 20:
                        html += f'<li class="more">...and {len(group_deps) - 20} more</li>'
                        
                    html += """
                                </ul>
                            </div>
                        </div>"""
                html += '</div>'
            
            # For npm dependencies
            elif dep_type == 'npm':
                prod_deps = [d for d in deps if d.get('type') == 'dependencies']
                dev_deps = [d for d in deps if d.get('type') == 'devDependencies']
                
                html += '<div class="npm-deps">'
                
                # Production dependencies
                if prod_deps:
                    html += """
                        <div class="npm-dep-section collapsible-card">
                            <div class="npm-dep-header" onclick="toggleCard(this)">
                                <span class="npm-dep-type">Production Dependencies</span>
                                <span class="npm-dep-count">{len(prod_deps)}</span>
                                <span class="toggle-icon">▼</span>
                            </div>
                            <div class="npm-dep-details">
                                <ul class="dep-list">"""
                    
                    for dep in sorted(prod_deps, key=lambda x: x.get('name', ''))[:30]:  # Limit to 30
                        name = dep.get('name', '')
                        version = dep.get('version', '')
                        html += f'<li>{name} <span class="version">{version}</span></li>'
                    
                    if len(prod_deps) > 30:
                        html += f'<li class="more">...and {len(prod_deps) - 30} more</li>'
                        
                    html += """
                                </ul>
                            </div>
                        </div>"""
                
                # Dev dependencies
                if dev_deps:
                    html += """
                        <div class="npm-dep-section collapsible-card">
                            <div class="npm-dep-header" onclick="toggleCard(this)">
                                <span class="npm-dep-type">Development Dependencies</span>
                                <span class="npm-dep-count">{len(dev_deps)}</span>
                                <span class="toggle-icon">▼</span>
                            </div>
                            <div class="npm-dep-details">
                                <ul class="dep-list">"""
                    
                    for dep in sorted(dev_deps, key=lambda x: x.get('name', ''))[:20]:  # Limit to 20
                        name = dep.get('name', '')
                        version = dep.get('version', '')
                        html += f'<li>{name} <span class="version">{version}</span></li>'
                    
                    if len(dev_deps) > 20:
                        html += f'<li class="more">...and {len(dev_deps) - 20} more</li>'
                        
                    html += """
                                </ul>
                            </div>
                        </div>"""
                
                html += '</div>'
            
            html += """
                    </div>
                </div>"""
        
        return html
    
    def _generate_query_type_options(self, query_types: Dict[str, int]) -> str:
        """Generate HTML options for query types"""
        html = ""
        for q_type in sorted(query_types.keys()):
            html += f'<option value="{q_type or "UNKNOWN"}">{q_type or "UNKNOWN"}</option>'
        return html
    
    def _generate_queries_html(self, queries: List[Dict]) -> str:
        """Generate HTML for SQL queries"""
        if not queries:
            return "<p>No SQL queries found</p>"
        
        html = ""
        for i, query in enumerate(queries):
            query_text = query.get('query_text', '').replace('<', '&lt;').replace('>', '&gt;')
            source_file = query.get('source_file', 'Unknown')
            query_type = query.get('query_type', 'UNKNOWN') or 'UNKNOWN'
            tables = ", ".join(query.get('tables', []))
            
            html += f"""
                <div class="query-card" data-type="{query_type}">
                    <div class="query-header collapsible-card">
                        <div class="query-title" onclick="toggleCard(this)">
                            <span class="query-num">#{i+1}</span>
                            <span class="query-type">{query_type}</span>
                            <span class="query-file">{source_file}</span>
                            <span class="toggle-icon">▼</span>
                        </div>
                    </div>
                    <div class="query-details">
                        <div class="query-info">
                            <p><strong>Tables:</strong> {tables or 'None detected'}</p>
                        </div>
                        <pre class="query-text">{query_text}</pre>
                    </div>
                </div>"""
        
        return html
    
    def _get_css(self) -> str:
        """Get CSS styles for the HTML report"""
        return """
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #3498db;
                --accent-color: #e74c3c;
                --bg-color: #ecf0f1;
                --card-bg: #ffffff;
                --text-color: #333333;
                --border-color: #ddd;
                --select-bg: #f0f4f8;
                --select-text: #34495e;
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: var(--text-color);
                background-color: var(--bg-color);
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: var(--card-bg);
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            header {
                background-color: var(--primary-color);
                color: white;
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }
            
            header h1 {
                margin: 0;
                font-size: 24px;
            }
            
            .project-info {
                font-size: 14px;
                margin-top: 10px;
            }
            
            main {
                padding: 20px;
            }
            
            section {
                margin-bottom: 30px;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                overflow: hidden;
            }
            
            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background-color: var(--select-bg);
                cursor: pointer;
            }
            
            .section-header h2 {
                margin: 0;
                font-size: 18px;
                color: var(--primary-color);
            }
            
            .section-content {
                padding: 20px;
                background-color: white;
                border-top: 1px solid var(--border-color);
            }
            
            .toggle-icon {
                font-size: 12px;
                transition: transform 0.3s ease;
            }
            
            .collapsed .toggle-icon {
                transform: rotate(-90deg);
            }
            
            .collapsible-card {
                cursor: pointer;
            }
            
            /* Dashboard */
            .dashboard {
                background-color: white;
                border: none !important;
            }
            
            .stats-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }
            
            .stat-card {
                background-color: var(--select-bg);
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            
            .stat-card h3 {
                font-size: 32px;
                color: var(--secondary-color);
                margin-bottom: 10px;
            }
            
            /* Tables */
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            
            .data-table th, .data-table td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
            }
            
            .data-table th {
                background-color: var(--select-bg);
                color: var(--select-text);
                font-weight: 600;
            }
            
            .data-table tr:hover {
                background-color: #f9f9f9;
            }
            
            /* Tech Stack */
            .tech-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .tech-item {
                padding: 12px 15px;
                border-radius: 6px;
                background-color: #f1f1f1;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .tech-item.detected {
                background-color: #e3f2fd;
                border-left: 4px solid var(--secondary-color);
            }
            
            .tech-check {
                color: #4caf50;
                font-weight: bold;
            }
            
            /* Databases */
            .database-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .database-item {
                padding: 12px 15px;
                border-radius: 6px;
                background-color: #e8f5e9;
                border-left: 4px solid #4caf50;
                text-align: center;
            }
            
            /* Connection Strings */
            .conn-string-list {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .conn-item {
                border: 1px solid var(--border-color);
                border-radius: 6px;
                overflow: hidden;
            }
            
            .conn-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                background-color: var(--select-bg);
            }
            
            .conn-title {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .db-type {
                background-color: var(--secondary-color);
                color: white;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .conn-name {
                font-weight: 500;
            }
            
            .conn-details {
                padding: 15px;
                border-top: 1px solid var(--border-color);
                display: none;
            }
            
            .conn-string {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                margin-top: 10px;
                font-family: monospace;
                font-size: 13px;
                white-space: pre-wrap;
                word-break: break-all;
            }
            
            /* Dependencies */
            .dependency-section {
                margin-bottom: 20px;
            }
            
            .dep-groups {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .dep-group {
                border: 1px solid var(--border-color);
                border-radius: 6px;
                overflow: hidden;
            }
            
            .group-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                background-color: var(--select-bg);
            }
            
            .group-name {
                font-weight: 500;
            }
            
            .group-count {
                background-color: var(--primary-color);
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
            }
            
            .group-details {
                padding: 15px;
                display: none;
                border-top: 1px solid var(--border-color);
            }
            
            .dep-list {
                list-style-type: none;
            }
            
            .dep-list li {
                padding: 5px 0;
                border-bottom: 1px solid #eee;
            }
            
            .dep-list li:last-child {
                border-bottom: none;
            }
            
            .version {
                color: #888;
                font-size: 90%;
            }
            
            .npm-deps {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .npm-dep-section {
                border: 1px solid var(--border-color);
                border-radius: 6px;
                overflow: hidden;
            }
            
            .npm-dep-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                background-color: var(--select-bg);
            }
            
            .npm-dep-count {
                background-color: var(--primary-color);
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
            }
            
            .npm-dep-details {
                padding: 15px;
                display: none;
                border-top: 1px solid var(--border-color);
            }
            
            /* SQL Queries */
            .query-filter {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 20px;
                align-items: center;
            }
            
            .query-filter select, .query-filter input {
                padding: 8px 12px;
                border: 1px solid var(--border-color);
                border-radius: 4px;
                font-size: 14px;
            }
            
            .query-filter select {
                background-color: var(--select-bg);
                color: var(--select-text);
            }
            
            .query-filter input {
                flex-grow: 1;
                min-width: 200px;
            }
            
            .queries-container {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .query-card {
                border: 1px solid var(--border-color);
                border-radius: 6px;
                overflow: hidden;
            }
            
            .query-header {
                background-color: var(--select-bg);
                padding: 12px 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .query-title {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-grow: 1;
            }
            
            .query-num {
                color: #888;
                font-size: 14px;
            }
            
            .query-type {
                background-color: var(--secondary-color);
                color: white;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
            }
            
            .query-file {
                font-size: 14px;
                color: #555;
                margin-left: auto;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 300px;
            }
            
            .query-details {
                padding: 15px;
                display: none;
                border-top: 1px solid var(--border-color);
            }
            
            .query-text {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 4px;
                margin-top: 10px;
                font-family: monospace;
                font-size: 13px;
                white-space: pre-wrap;
                overflow-x: auto;
            }
            
            /* Footer */
            footer {
                background-color: var(--primary-color);
                color: white;
                text-align: center;
                padding: 15px;
                font-size: 14px;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .tech-grid, .database-grid {
                    grid-template-columns: 1fr 1fr;
                }
                
                .dep-groups {
                    grid-template-columns: 1fr;
                }
                
                .query-title {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .query-file {
                    margin-left: 0;
                    margin-top: 5px;
                }
            }
            
            @media (max-width: 480px) {
                .tech-grid, .database-grid {
                    grid-template-columns: 1fr;
                }
                
                .stats-container {
                    grid-template-columns: 1fr;
                }
            }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for the HTML report"""
        return """
            // Toggle sections
            function toggleSection(element) {
                const content = element.nextElementSibling;
                element.classList.toggle('collapsed');
                
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                } else {
                    content.style.display = 'none';
                }
            }
            
            // Toggle cards
            function toggleCard(element) {
                const card = element.closest('.collapsible-card');
                const details = card.nextElementSibling;
                
                if (details.style.display === 'block') {
                    details.style.display = 'none';
                    if (card.querySelector('.toggle-icon')) {
                        card.querySelector('.toggle-icon').textContent = '▼';
                    }
                } else {
                    details.style.display = 'block';
                    if (card.querySelector('.toggle-icon')) {
                        card.querySelector('.toggle-icon').textContent = '▲';
                    }
                }
            }
            
            // Filter queries
            function filterQueries() {
                const typeFilter = document.getElementById('query-type-filter').value;
                const searchFilter = document.getElementById('query-search').value.toLowerCase();
                const queries = document.querySelectorAll('.query-card');
                
                queries.forEach(query => {
                    const queryType = query.getAttribute('data-type');
                    const queryText = query.querySelector('.query-text').textContent.toLowerCase();
                    const typeMatch = !typeFilter || queryType === typeFilter;
                    const searchMatch = !searchFilter || queryText.includes(searchFilter);
                    
                    if (typeMatch && searchMatch) {
                        query.style.display = 'block';
                    } else {
                        query.style.display = 'none';
                    }
                });
            }
            
            // Initialize collapsible sections
            document.addEventListener('DOMContentLoaded', function() {
                // Keep first section expanded, collapse others
                const sections = document.querySelectorAll('.section-header');
                
                sections.forEach((section, index) => {
                    if (index > 0) {
                        section.classList.add('collapsed');
                        section.nextElementSibling.style.display = 'none';
                    }
                });
            });
        """