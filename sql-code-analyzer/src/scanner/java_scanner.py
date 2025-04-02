import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Pattern
import sys

# Add project root to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.sql_query import SQLQuery
from scanner.enhanced_base_scanner import EnhancedBaseScanner

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JavaScanner')

class JavaScanner(EnhancedBaseScanner):
    """Scanner for extracting SQL queries from Java source files with enhanced detection"""
    
    def __init__(self, base_path: str, use_sqlparse: bool = True):
        super().__init__(base_path, use_sqlparse)
        self.java_files = []
        self.sql_queries = []
        self.sql_patterns = self._create_java_sql_patterns()
    
    def _create_java_sql_patterns(self) -> List[Pattern]:
        """Create regex patterns for detecting SQL in Java code"""
        patterns = []
        
        # Basic SQL string assignment patterns - common Java variable declarations
        for command_prefix in self.sql_command_prefixes:
            # Standard string assignment
            patterns.append(
                re.compile(f'(?:String|var)\\s+\\w+\\s*=\\s*"({command_prefix}.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
            )
            # Raw SQL strings (JDK 15+)
            patterns.append(
                re.compile(f'(?:String|var)\\s+\\w+\\s*=\\s*"""({command_prefix}.*?)"""', re.IGNORECASE | re.DOTALL)
            )
        
        # Common SQL-related variable names
        sql_var_names = [
            'sql', 'query', 'sqlQuery', 'sqlString', 'sqlStatement', 'queryString', 
            'selectSql', 'insertSql', 'updateSql', 'deleteSql', 'ddlQuery', 'sqlText',
            'hql', 'jpql'
        ]
        
        sql_var_pattern = '|'.join(sql_var_names)
        
        # SQL assigned to variables with SQL-related names
        patterns.append(
            re.compile(f'(?:{sql_var_pattern})\\s*=\\s*"(.*?)"[;\\)]', re.IGNORECASE | re.DOTALL)
        )
        
        # JDBC method calls with SQL
        jdbc_methods = [
            'executeQuery', 'executeUpdate', 'execute', 'prepareStatement', 
            'prepareCall', 'createStatement'
        ]
        
        for method in jdbc_methods:
            patterns.append(
                re.compile(f'{method}\\(\\s*"(.*?)"', re.IGNORECASE | re.DOTALL)
            )
        
        # JPA/Hibernate query methods
        orm_methods = [
            'createQuery', 'createNativeQuery', 'createSQLQuery', 'createNamedQuery',
            'getNamedQuery', 'createCriteria', 'createStoredProcedureQuery'
        ]
        
        for method in orm_methods:
            patterns.append(
                re.compile(f'{method}\\(\\s*"(.*?)"', re.IGNORECASE | re.DOTALL)
            )
        
        # String concatenation patterns
        patterns.append(
            re.compile(r'(?:append|concat|format|printf|String\.format)\s*\(\s*"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|MERGE|JOIN|UNION)[^"]*)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # SQL in comments (for named queries, etc.)
        patterns.append(
            re.compile(r'@(?:NamedQuery|Query|NamedNativeQuery|SqlResultSetMapping)\([^)]*query\s*=\s*"(.*?)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # Spring JDBC template
        patterns.append(
            re.compile(r'(?:jdbcTemplate|namedParameterJdbcTemplate)\.(?:query|update|execute|queryForObject|queryForList|queryForMap|queryForRowSet)\(\s*"(.*?)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # MyBatis/iBatis SQL mapper annotations
        patterns.append(
            re.compile(r'@(?:Select|Insert|Update|Delete|SelectProvider|InsertProvider|UpdateProvider|DeleteProvider)\(\s*"(.*?)"', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        # Multi-line string concatenation
        # This is more complex but catches common Java string concatenation patterns
        patterns.append(
            re.compile(r'(?:String|StringBuilder|StringBuffer|var)\s+\w+\s*=\s*(?:"|\+\s*")([^"]*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"]*)"(?:\s*\+\s*"[^"]*")*', 
                     re.IGNORECASE | re.DOTALL)
        )
        
        return patterns
    
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
            return java_files
        except Exception as e:
            logger.error(f"Error finding Java files: {e}")
            return []
    
    def extract_sql_from_file(self, file_path: Path) -> List[SQLQuery]:
        """Extract SQL queries from a Java file"""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Pre-processing for multi-line strings and concatenation
            # Replace common Java string concatenation patterns
            content = re.sub(r'"\s*\+\s*"', '', content)
            content = re.sub(r'"\s*\+\s*\n\s*"', ' ', content)
            
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
                            language="Java",
                            query_type=query_type
                        )
                        queries.append(query)
                    
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
            
        logger.info(f"Beginning to scan {len(self.java_files)} Java files for SQL queries")
        
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
        
        logger.info(f"Scan complete. Extracted {len(self.sql_queries)} SQL queries from {len(self.java_files)} Java files")
        return self.sql_queries
    
    def get_tech_stack_info(self) -> Dict[str, Any]:
        """Extract information about the Java tech stack in the repository"""
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
            },
            "mybatis": {
                "detected": False,
                "files": []  
            },
            "jdbc_direct": {
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
        
        # Scan import statements in Java files for common frameworks
        framework_patterns = {
            "spring": re.compile(r'import\s+org\.springframework', re.IGNORECASE),
            "hibernate": re.compile(r'import\s+org\.hibernate', re.IGNORECASE),
            "jpa": re.compile(r'import\s+javax\.persistence', re.IGNORECASE),
            "weblogic": re.compile(r'import\s+weblogic\.', re.IGNORECASE),
            "mybatis": re.compile(r'import\s+org\.(?:apache\.ibatis|mybatis)', re.IGNORECASE),
            "jdbc_direct": re.compile(r'import\s+java\.sql\.(?:Connection|Statement|PreparedStatement|ResultSet)', re.IGNORECASE)
        }
        
        # Sample a subset of Java files to check for framework imports
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