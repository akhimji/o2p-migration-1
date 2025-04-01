import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

from models.sql_query import SQLQuery

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DotNetScanner')

class DotNetScanner:
    """Scanner for extracting SQL queries from .NET source files"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.dotnet_files = []
        self.sql_queries = []
        
        # Extensions to scan
        self.file_extensions = ['.cs', '.vb', '.cshtml', '.vbhtml', '.aspx', '.ascx']
        
        # SQL patterns specific to .NET codebases
        self.sql_patterns = [
            # C# string assignments with SQL
            r'string\s+\w+\s*=\s*@?"(SELECT\s+.*?)"[;\)]',
            r'string\s+\w+\s*=\s*@?"(INSERT\s+.*?)"[;\)]',
            r'string\s+\w+\s*=\s*@?"(UPDATE\s+.*?)"[;\)]',
            r'string\s+\w+\s*=\s*@?"(DELETE\s+.*?)"[;\)]',
            r'string\s+\w+\s*=\s*@?"(CREATE\s+.*?)"[;\)]',
            r'string\s+\w+\s*=\s*@?"(ALTER\s+.*?)"[;\)]',
            r'string\s+\w+\s*=\s*@?"(DROP\s+.*?)"[;\)]',
            
            # ADO.NET and related patterns
            r'SqlCommand\(.+?"(.*?)"[,\)]',
            r'new\s+SqlCommand\(\s*@?"(.*?)"[,\)]',
            r'ExecuteReader\(\s*@?"(.*?)"[,\)]',
            r'ExecuteNonQuery\(\s*@?"(.*?)"[,\)]',
            r'ExecuteScalar\(\s*@?"(.*?)"[,\)]',
            
            # ORM-related patterns (Entity Framework, Dapper)
            r'FromSql(?:Raw)?\(\s*@?"(.*?)"[,\)]',
            r'Query(?:<.*?>)?\(\s*@?"(.*?)"[,\)]',
            r'Execute(?:Scalar|Reader|NonQuery)?(?:<.*?>)?\(\s*@?"(.*?)"[,\)]',
            
            # Named SQL query variables
            r'(?:sql|query|sqlQuery|sqlStatement|commandText)\s*=\s*@?"(SELECT\s+.*?)"[;\)]',
            r'(?:sql|query|sqlQuery|sqlStatement|commandText)\s*=\s*@?"(INSERT\s+.*?)"[;\)]',
            r'(?:sql|query|sqlQuery|sqlStatement|commandText)\s*=\s*@?"(UPDATE\s+.*?)"[;\)]',
            r'(?:sql|query|sqlQuery|sqlStatement|commandText)\s*=\s*@?"(DELETE\s+.*?)"[;\)]',
            
            # Dapper specific
            r'(?:Query|Execute|QueryFirst|QuerySingle|QueryMultiple)\(\s*@?"(.*?)"[,\)]',
        ]
        
        # Verbatim string patterns (to handle @"..." in C#)
        self.verbatim_patterns = [
            r'@"(SELECT\s+.*?)"',
            r'@"(INSERT\s+.*?)"',
            r'@"(UPDATE\s+.*?)"',
            r'@"(DELETE\s+.*?)"',
        ]
        
        # Pattern to identify common SQL keywords to qualify a string as SQL
        self.sql_keyword_pattern = re.compile(
            r'SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP BY|ORDER BY|HAVING', 
            re.IGNORECASE
        )
    
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
    
    def is_valid_sql_query(self, query_text: str) -> bool:
        """Validate if a string is likely a SQL query"""
        # Basic validation - check if it contains common SQL keywords
        if not query_text or len(query_text) < 10:
            return False
            
        return bool(self.sql_keyword_pattern.search(query_text))
    
    def extract_sql_from_file(self, file_path: Path) -> List[SQLQuery]:
        """Extract SQL queries from a .NET file"""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Handle C# string concatenation patterns
            content = re.sub(r'"\s*\+\s*@?"', '', content)
            content = re.sub(r'"\s*\+\s*"', '', content)
            
            # Process regular patterns
            for pattern in self.sql_patterns:
                found_queries = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for query_text in found_queries:
                    # Clean and validate the query
                    clean_query = query_text.strip().replace('\n', ' ').replace('\r', '')
                    
                    if self.is_valid_sql_query(clean_query):
                        # Create SQLQuery object
                        relative_path = file_path.relative_to(self.base_path)
                        query = SQLQuery(
                            query_text=clean_query,
                            source_file=str(relative_path),
                            language=".NET"
                        )
                        queries.append(query)
            
            # Special handling for verbatim strings (@"...") which may contain SQL
            for pattern in self.verbatim_patterns:
                found_queries = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for query_text in found_queries:
                    clean_query = query_text.strip()
                    
                    if self.is_valid_sql_query(clean_query):
                        relative_path = file_path.relative_to(self.base_path)
                        query = SQLQuery(
                            query_text=clean_query,
                            source_file=str(relative_path),
                            language=".NET"
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
        if web_config_files or aspx_files or mvc_files:
            tech_info["asp_net"]["detected"] = True
            files = []
            if web_config_files:
                files.append(str(web_config_files[0].relative_to(self.base_path)))
            if aspx_files and len(files) < 5:
                files.append(str(aspx_files[0].relative_to(self.base_path)))
            if mvc_files and len(files) < 5:
                files.append(str(mvc_files[0].relative_to(self.base_path)))
            tech_info["asp_net"]["files"] = files
        
        # Sample files to check for ORM frameworks
        sample_size = min(100, len(self.dotnet_files))  # Limit to 100 files for performance
        framework_patterns = {
            "entity_framework": re.compile(r'using\s+(?:Microsoft\.EntityFrameworkCore|System\.Data\.Entity)', re.IGNORECASE),
            "dapper": re.compile(r'using\s+Dapper', re.IGNORECASE),
        }
        
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