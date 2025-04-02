import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Pattern
import sys

# Add project root to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.sql_query import SQLQuery
from scanner.enhanced_base_scanner import EnhancedBaseScanner

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DotNetScanner')

class DotNetScanner(EnhancedBaseScanner):
    """Scanner for extracting SQL queries from .NET source files with enhanced detection"""
    
    def __init__(self, base_path: str, use_sqlparse: bool = True):
        super().__init__(base_path, use_sqlparse)
        self.dotnet_files = []
        self.sql_queries = []
        
        # Extensions to scan
        self.file_extensions = ['.cs', '.vb', '.cshtml', '.vbhtml', '.aspx', '.ascx', '.razor']
        
        # Create regex patterns
        self.sql_patterns = self._create_dotnet_sql_patterns()
    
    def _create_dotnet_sql_patterns(self) -> List[Pattern]:
        """Create regex patterns for detecting SQL in .NET code"""
        patterns = []
        
        # C# & VB.NET string assignments with SQL keywords
        for command_prefix in self.sql_command_prefixes:
            # Regular string (C#)
            patterns.append(
                re.compile(f'(?:string|var)\\s+\\w+\\s*=\\s*"({command_prefix}.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
            )
            # Verbatim string (C# @"...")
            patterns.append(
                re.compile(f'(?:string|var)\\s+\\w+\\s*=\\s*@"({command_prefix}.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
            )
            # VB.NET string assignment
            patterns.append(
                re.compile(f'(?:Dim|Private|Public)\\s+\\w+\\s+As\\s+String\\s*=\\s*"({command_prefix}.*?)"', re.IGNORECASE | re.DOTALL)
            )
            # Interpolated strings (C# $"...")
            patterns.append(
                re.compile(f'(?:string|var)\\s+\\w+\\s*=\\s*\\$"({command_prefix}.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
            )
        
        # Common SQL-related variable names
        sql_var_names = [
            'sql', 'query', 'sqlQuery', 'sqlString', 'sqlStatement', 'queryString', 
            'selectSql', 'insertSql', 'updateSql', 'deleteSql', 'ddlQuery', 'sqlText',
            'commandText', 'sqlCommand', 'storedProcedure', 'commandString'
        ]
        
        sql_var_pattern = '|'.join(sql_var_names)
        
        # SQL assigned to variables with SQL-related names (C#)
        patterns.append(
            re.compile(f'(?:{sql_var_pattern})\\s*=\\s*"(.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
        )
        
        # SQL assigned to variables with SQL-related names (C# verbatim strings)
        patterns.append(
            re.compile(f'(?:{sql_var_pattern})\\s*=\\s*@"(.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
        )
        
        # SQL assigned to variables with SQL-related names (VB.NET)
        patterns.append(
            re.compile(f'(?:{sql_var_pattern})\\s*=\\s*"(.*?)"(?:\\s*&\\s*".*?")*', re.IGNORECASE | re.DOTALL)
        )
        
        # ADO.NET SqlCommand
        patterns.append(
            re.compile(r'new\s+SqlCommand\s*\(\s*@?"(.*?)"[,\)]', re.IGNORECASE | re.DOTALL)
        )
        patterns.append(
            re.compile(r'new\s+SqlCommand\s*\{\s*CommandText\s*=\s*@?"(.*?)"', re.IGNORECASE | re.DOTALL)
        )
        patterns.append(
            re.compile(r'\.CommandText\s*=\s*@?"(.*?)"', re.IGNORECASE | re.DOTALL)
        )
        
        # ADO.NET method calls
        ado_methods = [
            'ExecuteReader', 'ExecuteNonQuery', 'ExecuteScalar', 'ExecuteDataSet',
            'ExecuteDataTable', 'Execute'
        ]
        
        for method in ado_methods:
            patterns.append(
                re.compile(f'{method}\\(\\s*@?"(.*?)"', re.IGNORECASE | re.DOTALL)
            )
            patterns.append(
                re.compile(f'{method}\\(\\s*\\$"(.*?)"', re.IGNORECASE | re.DOTALL)
            )
        
        # Entity Framework
        ef_methods = [
            'ExecuteSqlCommand', 'ExecuteSqlCommandAsync', 'ExecuteSqlRaw', 
            'ExecuteSqlRawAsync', 'FromSql', 'FromSqlRaw', 'FromSqlInterpolated'
        ]
        
        for method in ef_methods:
            patterns.append(
                re.compile(f'{method}\\(\\s*@?"(.*?)"', re.IGNORECASE | re.DOTALL)
            )
        
        # Dapper methods
        dapper_methods = [
            'Query', 'QueryFirst', 'QueryFirstOrDefault', 'QuerySingle', 'QuerySingleOrDefault',
            'QueryMultiple', 'Execute', 'ExecuteScalar', 'ExecuteReader'
        ]
        
        for method in dapper_methods:
            patterns.append(
                re.compile(f'\\.{method}(?:<.*?>)?\\(\\s*@?"(.*?)"', re.IGNORECASE | re.DOTALL)
            )
        
        # Multi-line string concat in VB.NET
        patterns.append(
            re.compile(r'(?:Dim|Private|Public)\s+\w+\s+As\s+String\s*=\s*"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"]*)(?:"\s*&\s*"[^"]*")+', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # String.Format with SQL
        patterns.append(
            re.compile(r'String\.Format\(\s*@?"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"]*)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # StringBuilder append with SQL
        patterns.append(
            re.compile(r'(?:StringBuilder|StringWriter).*?\.Append(?:Line)?\(\s*@?"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"]*)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # Stored Procedures
        patterns.append(
            re.compile(r'CommandType\s*=\s*CommandType\.StoredProcedure.*?CommandText\s*=\s*@?"(.*?)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        patterns.append(
            re.compile(r'CommandText\s*=\s*@?"(.*?)".*?CommandType\s*=\s*CommandType\.StoredProcedure', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # C# raw string literals (C# 11+)
        for command_prefix in self.sql_command_prefixes:
            patterns.append(
                re.compile(f'(?:string|var)\\s+\\w+\\s*=\\s*"""({command_prefix}.*?)"""', re.IGNORECASE | re.DOTALL)
            )
        
        return patterns
    
    def find_dotnet_files(self) -> List[Path]:
        """Find all .NET related files in the project directory"""
        dotnet_files = []
        logger.info(f"Scanning {self.base_path} for .NET files...")
        
        try:
            for ext in self.file_extensions:
                for path in self.base_path.glob(f"**/*{ext}"):
                    if path.is_file():
                        dotnet_files.append(path)
            
            logger.info(f"Found {len(dotnet_files)} .NET files")
            return dotnet_files
        except Exception as e:
            logger.error(f"Error finding .NET files: {e}")
            return []
    
    def extract_sql_from_file(self, file_path: Path) -> List[SQLQuery]:
        """Extract SQL queries from a .NET file"""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Pre-processing
            # Handle C# string concatenations
            content = re.sub(r'"\s*\+\s*@?"', ' ', content)
            content = re.sub(r'"\s*\+\s*"', ' ', content)
            # Handle VB.NET string concatenations
            content = re.sub(r'"\s*&\s*"', ' ', content)
            
            # Process with all patterns
            for pattern in self.sql_patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):  # Some patterns might return tuples
                        match = match[0] if match else ""
                    
                    # Clean and validate the query
                    clean_query = match.strip().replace('\n', ' ').replace('\r', '')
                    
                    if self.is_valid_sql_query(clean_query):
                        # Create SQLQuery object
                        relative_path = file_path.relative_to(self.base_path)
                        
                        # Detect query type
                        query_type = self.detect_query_type(clean_query)
                        
                        query = SQLQuery(
                            query_text=clean_query,
                            source_file=str(relative_path),
                            language=".NET",
                            query_type=query_type
                        )
                        queries.append(query)
                    
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            
        return queries
    
    def scan(self) -> List[SQLQuery]:
        """Scan all .NET files and extract SQL queries"""
        self.dotnet_files = self.find_dotnet_files()
        self.sql_queries = []
        
        if not self.dotnet_files:
            logger.warning("No .NET files found to scan")
            return []
            
        logger.info(f"Beginning to scan {len(self.dotnet_files)} .NET files for SQL queries")
        
        # Track progress
        total_files = len(self.dotnet_files)
        processed = 0
        last_percent = 0
        
        for file_path in self.dotnet_files:
            queries = self.extract_sql_from_file(file_path)
            if queries:
                self.sql_queries.extend(queries)
            
            # Update progress
            processed += 1
            percent_complete = int((processed / total_files) * 100)
            
            # Log progress at 10% intervals
            if percent_complete >= last_percent + 10:
                logger.info(f"Scanning progress: {percent_complete}% ({processed}/{total_files} files)")
                last_percent = percent_complete
        
        logger.info(f"Scan complete. Extracted {len(self.sql_queries)} SQL queries from {len(self.dotnet_files)} .NET files")
        return self.sql_queries
    
    def get_tech_stack_info(self) -> Dict[str, Any]:
        """Extract information about the .NET tech stack in the repository"""
        tech_info = {
            "dotnet_framework": {
                "detected": False,
                "files": []
            },
            "dotnet_core": {
                "detected": False,
                "files": []
            },
            "asp_net": {
                "detected": False,
                "files": []
            },
            "entity_framework": {
                "detected": False,
                "files": []
            },
            "dapper": {
                "detected": False, 
                "files": []
            },
            "ado_net": {
                "detected": False,
                "files": []
            }
        }
        
        # Check for project files
        csproj_files = list(self.base_path.glob("**/*.csproj"))
        vbproj_files = list(self.base_path.glob("**/*.vbproj"))
        sln_files = list(self.base_path.glob("**/*.sln"))
        
        project_files = csproj_files + vbproj_files
        
        if project_files:
            # Analyze project files to determine .NET Framework vs .NET Core/5+
            for proj_file in project_files[:10]:  # Limit to first 10 for performance
                try:
                    with open(proj_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        
                    if 'sdk="microsoft.net.sdk' in content:
                        tech_info["dotnet_core"]["detected"] = True
                        rel_path = str(proj_file.relative_to(self.base_path))
                        tech_info["dotnet_core"]["files"].append(rel_path)
                    elif '<targetframework' in content:
                        if 'netcoreapp' in content or 'net5' in content or 'net6' in content:
                            tech_info["dotnet_core"]["detected"] = True
                            rel_path = str(proj_file.relative_to(self.base_path))
                            tech_info["dotnet_core"]["files"].append(rel_path)
                        else:
                            tech_info["dotnet_framework"]["detected"] = True
                            rel_path = str(proj_file.relative_to(self.base_path))
                            tech_info["dotnet_framework"]["files"].append(rel_path)
                except Exception as e:
                    logger.error(f"Error analyzing project file {proj_file}: {e}")
        
        if sln_files:
            tech_info["solution_files"] = {
                "detected": True,
                "files": [str(f.relative_to(self.base_path)) for f in sln_files]
            }
        
        # Look for ASP.NET indicators
        web_config_files = list(self.base_path.glob("**/web.config"))
        aspx_files = list(self.base_path.glob("**/*.aspx"))
        mvc_files = list(self.base_path.glob("**/Controllers/*.cs"))
        razor_files = list(self.base_path.glob("**/*.cshtml"))
        
        if web_config_files or aspx_files or mvc_files or razor_files:
            tech_info["asp_net"]["detected"] = True
            files = []
            if web_config_files:
                files.append(str(web_config_files[0].relative_to(self.base_path)))
            if aspx_files and len(files) < 5:
                files.append(str(aspx_files[0].relative_to(self.base_path)))
            if mvc_files and len(files) < 5:
                files.append(str(mvc_files[0].relative_to(self.base_path)))
            if razor_files and len(files) < 5:
                files.append(str(razor_files[0].relative_to(self.base_path)))
            tech_info["asp_net"]["files"] = files
        
        # Sample files to check for ORM frameworks and data access patterns
        framework_patterns = {
            "entity_framework": re.compile(r'using\s+(?:Microsoft\.EntityFrameworkCore|System\.Data\.Entity)', re.IGNORECASE),
            "dapper": re.compile(r'using\s+Dapper', re.IGNORECASE),
            "ado_net": re.compile(r'using\s+System\.Data\.SqlClient|SqlConnection|SqlCommand', re.IGNORECASE)
        }
        
        sample_size = min(100, len(self.dotnet_files))  # Limit to 100 files for performance
        for file_path in self.dotnet_files[:sample_size]:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for framework, pattern in framework_patterns.items():
                    if pattern.search(content):
                        tech_info[framework]["detected"] = True
                        rel_path = str(file_path.relative_to(self.base_path))
                        if rel_path not in tech_info[framework]["files"]:
                            tech_info[framework]["files"].append(rel_path)
                            # Limit the number of files we store
                            if len(tech_info[framework]["files"]) >= 5:
                                break
                                
            except Exception as e:
                logger.error(f"Error checking frameworks in {file_path}: {e}")
        
        return tech_info