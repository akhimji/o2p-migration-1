import re
from typing import List, Pattern
from pathlib import Path
import logging

logger = logging.getLogger('ConnectionStringDetector')

class ConnectionStringDetector:
    """Detector for database connection strings in source code"""
    
    def __init__(self):
        # Common connection string patterns
        self.connection_patterns = [
            # JDBC connection strings
            re.compile(r'jdbc:(?:oracle|mysql|postgresql|sqlserver|db2|mariadb):[^";\n]+'),
            
            # ADO.NET connection strings
            re.compile(r'(?:Data Source|Server)=[^;]+;(?:Initial Catalog|Database)=[^;]+;.*?(?:User ID|UID)=[^;]+;.*?(?:Password|PWD)=[^;]*'),
            re.compile(r'(?:Data Source|Server)=[^;]+;(?:Initial Catalog|Database)=[^;]+;.*?Integrated Security=(?:SSPI|True)'),
            
            # Entity Framework connection strings
            re.compile(r'name=\w+connectionstring\s+connectionstring\s*=\s*"[^"]+"', re.IGNORECASE),
            
            # Connection strings in config files
            re.compile(r'<add\s+name="[^"]+"\s+connectionString="[^"]+"', re.IGNORECASE),
            
            # Spring Database URL properties
            re.compile(r'(?:spring\.datasource\.url|database\.url|jdbc\.url|hibernate\.connection\.url)\s*=\s*[^;\n]+'),
            
            # Common connection string building patterns
            re.compile(r'(?:connection|conn)String(?:\s*=\s*|\s*\+=\s*)(?:"[^"]+"|\'[^\']+\')'),
            
            # Key-value pairs that suggest connection strings
            re.compile(r'(?:username|user|uid|password|pwd|host|server|database|db|port)\s*=\s*(?:"[^"]+"|\'[^\']+\')')
        ]
    
    def scan_file_for_connections(self, file_path: Path) -> List[str]:
        """
        Scan a single file for connection strings
        """
        connections = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern in self.connection_patterns:
                matches = pattern.findall(content)
                if matches:
                    for match in matches:
                        # Clean up the connection string (remove quotes, etc.)
                        cleaned = match.strip()
                        if cleaned and len(cleaned) > 10:  # Minimum reasonable length
                            connections.append(cleaned)
        except Exception as e:
            logger.warning(f"Error scanning {file_path} for connection strings: {e}")
            
        return connections
    
    def scan_directory(self, base_path: Path) -> List[str]:
        """
        Scan a directory for files that might contain connection strings
        """
        all_connections = []
        
        # Focus on files that are likely to contain connection strings
        config_patterns = [
            "**/*.config", "**/*.xml", "**/*.properties", "**/*.yml", "**/*.yaml",
            "**/*.json", "**/*.ini", "**/*.conf", "**/*.cfg", "**/*.settings",
            "**/application.properties", "**/hibernate.cfg.xml", "**/web.config",
            "**/app.config", "**/settings.py", "**/database.php"
        ]
        
        # Find config files
        config_files = []
        for pattern in config_patterns:
            config_files.extend(base_path.glob(pattern))
        
        # Scan config files first (they're most likely to have connection strings)
        for file_path in config_files:
            if file_path.is_file():
                connections = self.scan_file_for_connections(file_path)
                all_connections.extend(connections)
        
        # Also check source code files if needed
        source_patterns = ["**/*.java", "**/*.cs", "**/*.py", "**/*.rb", "**/*.php", "**/*.js"]
        source_files = []
        for pattern in source_patterns:
            source_files.extend(base_path.glob(pattern))
        
        # Limit to a reasonable sample size for performance
        sample_size = min(200, len(source_files))
        for file_path in source_files[:sample_size]:
            if file_path.is_file():
                connections = self.scan_file_for_connections(file_path)
                all_connections.extend(connections)
        
        # Remove duplicates and return
        return list(set(all_connections))