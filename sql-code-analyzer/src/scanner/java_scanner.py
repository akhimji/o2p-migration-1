import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

from models.sql_query import SQLQuery

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JavaScanner')

class JavaScanner:
    """Scanner for extracting SQL queries from Java source files"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.java_files = []
        self.sql_queries = []
        
        # Expanded SQL patterns to catch more variations
        self.sql_patterns = [
            # String assignments with SQL
            r'String\s+\w+\s*=\s*"(SELECT\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(INSERT\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(UPDATE\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(DELETE\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(CREATE\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(ALTER\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(DROP\s+.*?)"[;\)]',
            r'String\s+\w+\s*=\s*"(MERGE\s+.*?)"[;\)]',
            
            # Generic string with SQL
            r'"(SELECT\s+.*?)"',
            r'"(INSERT\s+.*?)"',
            r'"(UPDATE\s+.*?)"',
            r'"(DELETE\s+.*?)"',
            
            # JDBC method calls
            r'executeQuery\(\s*"(.*?)"\s*\)',
            r'executeUpdate\(\s*"(.*?)"\s*\)',
            r'prepareStatement\(\s*"(.*?)"\s*\)',
            r'createStatement\(\s*"(.*?)"\s*\)',
            
            # String builder/buffer with SQL
            r'append\(\s*"(SELECT\s+.*?)"\s*\)',
            r'append\(\s*"(INSERT\s+.*?)"\s*\)',
            r'append\(\s*"(UPDATE\s+.*?)"\s*\)',
            r'append\(\s*"(DELETE\s+.*?)"\s*\)',
            
            # Named SQL query variables
            r'(?:sql|query|sqlQuery|sqlStatement)\s*=\s*"(SELECT\s+.*?)"[;\)]',
            r'(?:sql|query|sqlQuery|sqlStatement)\s*=\s*"(INSERT\s+.*?)"[;\)]',
            r'(?:sql|query|sqlQuery|sqlStatement)\s*=\s*"(UPDATE\s+.*?)"[;\)]',
            r'(?:sql|query|sqlQuery|sqlStatement)\s*=\s*"(DELETE\s+.*?)"[;\)]',
            
            # Hibernate/JPA queries
            r'createQuery\(\s*"(.*?)"\s*\)',
            r'createNativeQuery\(\s*"(.*?)"\s*\)',
            r'createSQLQuery\(\s*"(.*?)"\s*\)',
        ]
        
        # Pattern to identify common SQL keywords to qualify a string as SQL
        self.sql_keyword_pattern = re.compile(
            r'SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP BY|ORDER BY|HAVING', 
            re.IGNORECASE
        )
    
    def find_java_files(self) -> List[Path]:
        """Find all Java files in the project directory"""
        java_files = []
        logger.info(f"Scanning {self.base_path} for Java files...")
        
        # Count total files for progress reporting
        try:
            for path in self.base_path.glob("**/*.java"):
                if path.is_file():
                    java_files.append(path)
            
            logger.info(f"Found {len(java_files)} Java files")
            
            # If no Java files found, look for any code files that might contain SQL
            if not java_files:
                logger.info("No Java files found. Searching for other potential code files...")
                code_extensions = ['.cs', '.ts', '.js', '.py', '.sql', '.xml', '.jsp', '.asp', '.php']
                
                for ext in code_extensions:
                    for path in self.base_path.glob(f"**/*{ext}"):
                        if path.is_file():
                            java_files.append(path)
                
                logger.info(f"Found {len(java_files)} potential code files")
                
            return java_files
        except Exception as e:
            logger.error(f"Error finding files: {e}")
            return []
    
    def is_valid_sql_query(self, query_text: str) -> bool:
        """Validate if a string is likely a SQL query"""
        # Basic validation - check if it contains common SQL keywords
        if not query_text or len(query_text) < 10:
            return False
            
        return bool(self.sql_keyword_pattern.search(query_text))
    
    def extract_sql_from_file(self, file_path: Path) -> List[SQLQuery]:
        """Extract SQL queries from a file"""
        queries = []
        file_extension = file_path.suffix.lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # For SQL files, treat the whole content as a SQL query
            if file_extension == '.sql':
                # Split by semicolons to get individual statements
                sql_statements = [s.strip() for s in content.split(';') if s.strip()]
                for stmt in sql_statements:
                    if self.is_valid_sql_query(stmt):
                        relative_path = file_path.relative_to(self.base_path)
                        query = SQLQuery(
                            query_text=stmt,
                            source_file=str(relative_path),
                            language="SQL"
                        )
                        queries.append(query)
                return queries
            
            # Multi-line strings handling
            # Replace line breaks within quotes to help with regex pattern matching
            content = re.sub(r'"\s*\+\s*"', '', content)
            content = re.sub(r'"\s*\+\s*[\'"](.+?)[\'"]', r'\1', content)
            
            for pattern in self.sql_patterns:
                try:
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
                                language="Java"
                            )
                            queries.append(query)
                except Exception as e:
                    logger.error(f"Error extracting SQL from {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            
        return queries
    
    def scan(self) -> List[SQLQuery]:
        """Scan all Java files and extract SQL queries"""
        self.java_files = self.find_java_files()
        self.sql_queries = []
        
        if not self.java_files:
            logger.warning("No Java files found to scan")
            return []
            
        logger.info(f"Beginning to scan {len(self.java_files)} files for SQL queries")
        
        # Track progress
        total_files = len(self.java_files)
        processed = 0
        last_percent = 0
        
        for file_path in self.java_files:
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
        
        logger.info(f"Scan complete. Extracted {len(self.sql_queries)} SQL queries from {len(self.java_files)} files")
        return self.sql_queries
    
    def get_tech_stack_info(self) -> Dict[str, Any]:
        """Extract information about the tech stack in the repository"""
        tech_info = {
            "weblogic": {
                "detected": False,
                "files": []
            },
            "spring": {
                "detected": False,
                "files": []
            },
            "hibernate": {
                "detected": False,
                "files": []
            },
            "jpa": {
                "detected": False, 
                "files": []
            }
        }
        
        # Check for Maven
        pom_files = list(self.base_path.glob("**/pom.xml"))
        if pom_files:
            tech_info["maven"] = {
                "detected": True,
                "files": [str(f.relative_to(self.base_path)) for f in pom_files]
            }
        
        # Check for Gradle
        gradle_files = list(self.base_path.glob("**/*.gradle"))
        if gradle_files:
            tech_info["gradle"] = {
                "detected": True,
                "files": [str(f.relative_to(self.base_path)) for f in gradle_files]
            }
        
        # Look for WebLogic configuration files
        weblogic_files = list(self.base_path.glob("**/weblogic*.xml"))
        if weblogic_files:
            tech_info["weblogic"]["detected"] = True
            tech_info["weblogic"]["files"] = [str(f.relative_to(self.base_path)) for f in weblogic_files]
        
        # Scan import statements in files for common frameworks
        framework_patterns = {
            "spring": re.compile(r'import\s+org\.springframework', re.IGNORECASE),
            "hibernate": re.compile(r'import\s+org\.hibernate', re.IGNORECASE),
            "jpa": re.compile(r'import\s+javax\.persistence', re.IGNORECASE),
            "weblogic": re.compile(r'import\s+weblogic\.', re.IGNORECASE)
        }
        
        # Sample a subset of files to check for framework imports
        sample_size = min(100, len(self.java_files))  # Limit to 100 files for performance
        for file_path in self.java_files[:sample_size]:
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