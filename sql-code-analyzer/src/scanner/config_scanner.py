import os
import re
import logging
import xml.etree.ElementTree as ET
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ConfigScanner')

class ConfigScanner:
    """
    Scanner that extracts configuration information from various file types:
    - XML files (pom.xml, web.config, app.config, etc.)
    - YAML files (docker-compose.yaml, application.yml, etc.)
    - JSON files (package.json, appsettings.json, etc.)
    - Properties files (.properties, application.properties)
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.config_files = {}
        self.scan_results = {
            "connection_strings": [],
            "databases": set(),
            "dependencies": {},
            "frameworks": {},
            "build_tools": {},
            "environment_configs": {}
        }
    
    def scan(self) -> Dict[str, Any]:
        """
        Scan the repository for configuration files and extract relevant information
        """
        logger.info(f"Scanning {self.base_path} for configuration files...")
        
        # Find all relevant config files
        self._find_config_files()
        
        # Process different file types
        self._process_xml_files()
        self._process_yaml_files()
        self._process_json_files()
        self._process_properties_files()
        self._process_config_files()
        
        # Convert sets to lists for JSON serialization
        self.scan_results["databases"] = list(self.scan_results["databases"])
        
        logger.info(f"Config scan complete. Found {len(self.scan_results['connection_strings'])} connection strings")
        return self.scan_results
    
    def _find_config_files(self) -> None:
        """Find configuration files in the repository"""
        # XML files
        self.config_files["xml"] = []
        for pattern in ["**/*.xml", "**/*.config"]:
            for path in self.base_path.glob(pattern):
                if path.is_file() and path.stat().st_size < 5000000:  # Skip files over 5MB
                    self.config_files["xml"].append(path)
        
        # YAML files
        self.config_files["yaml"] = []
        for pattern in ["**/*.yaml", "**/*.yml"]:
            for path in self.base_path.glob(pattern):
                if path.is_file() and path.stat().st_size < 1000000:  # Skip files over 1MB
                    self.config_files["yaml"].append(path)
        
        # JSON files
        self.config_files["json"] = []
        for pattern in ["**/*.json"]:
            for path in self.base_path.glob(pattern):
                if path.is_file() and path.stat().st_size < 1000000:  # Skip files over 1MB
                    self.config_files["json"].append(path)
        
        # Properties files
        self.config_files["properties"] = []
        for pattern in ["**/*.properties"]:
            for path in self.base_path.glob(pattern):
                if path.is_file():
                    self.config_files["properties"].append(path)
        
        # .NET specific config files
        self.config_files["dotnet_config"] = []
        for pattern in ["**/app.config", "**/web.config", "**/appsettings.json"]:
            for path in self.base_path.glob(pattern):
                if path.is_file():
                    self.config_files["dotnet_config"].append(path)
        
        logger.info(f"Found configuration files: "
                   f"{len(self.config_files['xml'])} XML, "
                   f"{len(self.config_files['yaml'])} YAML, "
                   f"{len(self.config_files['json'])} JSON, "
                   f"{len(self.config_files['properties'])} Properties, "
                   f"{len(self.config_files['dotnet_config'])} .NET config")
    
    def _process_xml_files(self) -> None:
        """Process XML configuration files"""
        pom_files = [p for p in self.config_files["xml"] if p.name.lower() == "pom.xml"]
        web_config_files = [p for p in self.config_files["xml"] if p.name.lower() == "web.config"]
        app_config_files = [p for p in self.config_files["xml"] if p.name.lower() == "app.config"]
        
        # Process Maven POM files
        for pom_file in pom_files:
            self._process_pom_file(pom_file)
        
        # Process .NET config files
        for config_file in web_config_files + app_config_files:
            self._process_dotnet_config_file(config_file)
        
        # Process remaining XML files for connection strings
        other_xml_files = [p for p in self.config_files["xml"] 
                          if p not in pom_files and p not in web_config_files and p not in app_config_files]
        for xml_file in other_xml_files[:50]:  # Limit to first 50 files
            self._extract_connection_strings_from_xml(xml_file)
    
    def _process_pom_file(self, pom_file: Path) -> None:
        """Extract information from Maven POM file"""
        try:
            rel_path = str(pom_file.relative_to(self.base_path))
            logger.info(f"Processing Maven POM file: {rel_path}")
            
            # Parse the XML
            tree = ET.parse(pom_file)
            root = tree.getroot()
            
            # Get namespace if present
            ns = {'': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
            ns_prefix = '{' + next(iter(ns.values())) + '}' if ns else ''
            
            # Extract project info
            project_info = {}
            elements = ['groupId', 'artifactId', 'version', 'name', 'description']
            for elem in elements:
                node = root.find(f"{ns_prefix}{elem}")
                if node is not None and node.text:
                    project_info[elem] = node.text.strip()
            
            # Extract dependencies
            dependencies = []
            deps_node = root.find(f"{ns_prefix}dependencies")
            if deps_node is not None:
                for dep in deps_node.findall(f"{ns_prefix}dependency"):
                    dep_info = {}
                    for elem in ['groupId', 'artifactId', 'version', 'scope']:
                        node = dep.find(f"{ns_prefix}{elem}")
                        if node is not None and node.text:
                            dep_info[elem] = node.text.strip()
                    if 'groupId' in dep_info and 'artifactId' in dep_info:
                        dependencies.append(dep_info)
            
            # Extract build plugins
            build_node = root.find(f"{ns_prefix}build")
            plugins = []
            if build_node is not None:
                plugins_node = build_node.find(f"{ns_prefix}plugins")
                if plugins_node is not None:
                    for plugin in plugins_node.findall(f"{ns_prefix}plugin"):
                        plugin_info = {}
                        for elem in ['groupId', 'artifactId', 'version']:
                            node = plugin.find(f"{ns_prefix}{elem}")
                            if node is not None and node.text:
                                plugin_info[elem] = node.text.strip()
                        if 'groupId' in plugin_info and 'artifactId' in plugin_info:
                            plugins.append(plugin_info)
            
            # Add to scan results
            self.scan_results["build_tools"]["maven"] = {
                "detected": True,
                "files": [rel_path],
                "project_info": project_info
            }
            
            # Process dependencies to identify frameworks
            for dep in dependencies:
                group_id = dep.get('groupId', '')
                artifact_id = dep.get('artifactId', '')
                
                # Identify common frameworks and libraries
                if 'spring' in group_id or 'spring' in artifact_id:
                    self.scan_results["frameworks"].setdefault("spring", {
                        "detected": True, 
                        "files": [rel_path],
                        "components": []
                    })
                    self.scan_results["frameworks"]["spring"]["components"].append(f"{group_id}:{artifact_id}")
                
                if 'hibernate' in group_id or 'hibernate' in artifact_id:
                    self.scan_results["frameworks"].setdefault("hibernate", {
                        "detected": True, 
                        "files": [rel_path],
                        "components": []
                    })
                    self.scan_results["frameworks"]["hibernate"]["components"].append(f"{group_id}:{artifact_id}")
                
                # Database drivers
                if 'mysql' in artifact_id:
                    self.scan_results["databases"].add("mysql")
                elif 'postgresql' in artifact_id:
                    self.scan_results["databases"].add("postgresql")
                elif 'oracle' in artifact_id:
                    self.scan_results["databases"].add("oracle")
                elif 'sqlserver' in artifact_id or 'mssql' in artifact_id:
                    self.scan_results["databases"].add("sqlserver")
                elif 'db2' in artifact_id:
                    self.scan_results["databases"].add("db2")
            
            # Store all dependencies
            self.scan_results["dependencies"]["maven"] = dependencies
            
        except Exception as e:
            logger.error(f"Error processing POM file {pom_file}: {e}")
    
    def _process_dotnet_config_file(self, config_file: Path) -> None:
        """Extract information from .NET config files (app.config, web.config)"""
        try:
            rel_path = str(config_file.relative_to(self.base_path))
            logger.info(f"Processing .NET config file: {rel_path}")
            
            # Parse the XML
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # Extract connection strings
            cs_node = root.find(".//connectionStrings")
            if cs_node is not None:
                for add_node in cs_node.findall(".//add"):
                    if 'connectionString' in add_node.attrib:
                        conn_str = add_node.attrib['connectionString']
                        name = add_node.attrib.get('name', 'unnamed')
                        provider = add_node.attrib.get('providerName', 'unknown')
                        
                        conn_info = {
                            "name": name,
                            "connection_string": conn_str,
                            "provider": provider,
                            "source_file": rel_path,
                            "database_type": self._detect_database_from_connection_string(conn_str, provider)
                        }
                        self.scan_results["connection_strings"].append(conn_info)
                        
                        # Add to databases list
                        if conn_info["database_type"]:
                            self.scan_results["databases"].add(conn_info["database_type"])
            
            # Extract framework version
            framework_node = root.find(".//compilation")
            if framework_node is not None and 'targetFramework' in framework_node.attrib:
                framework = framework_node.attrib['targetFramework']
                self.scan_results["frameworks"].setdefault("dotnet", {
                    "detected": True,
                    "version": framework,
                    "files": [rel_path]
                })
            
            # Look for specific configuration sections to identify technologies
            if root.find(".//hibernate-configuration") is not None:
                self.scan_results["frameworks"].setdefault("nhibernate", {
                    "detected": True,
                    "files": [rel_path]
                })
            
            if root.find(".//entityFramework") is not None:
                self.scan_results["frameworks"].setdefault("entity_framework", {
                    "detected": True,
                    "files": [rel_path]
                })
            
        except Exception as e:
            logger.error(f"Error processing .NET config file {config_file}: {e}")
    
    def _extract_connection_strings_from_xml(self, xml_file: Path) -> None:
        """Look for connection strings in arbitrary XML files"""
        try:
            with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple regex patterns for common connection string formats
            conn_patterns = [
                r'(?:connectionString|connection-string|jdbc:url)=["\'](.*?)["\']',
                r'<(?:connection-url|connection-string|url)>(.*?)</(?:connection-url|connection-string|url)>',
                r'jdbc:(?:mysql|oracle|sqlserver|postgresql|db2):.*?(?:[:;/].*?){2,}'
            ]
            
            rel_path = str(xml_file.relative_to(self.base_path))
            
            for pattern in conn_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    conn_str = match.strip()
                    if len(conn_str) > 15:  # Minimum reasonable connection string length
                        db_type = self._detect_database_from_connection_string(conn_str)
                        if db_type:
                            conn_info = {
                                "name": "extracted",
                                "connection_string": conn_str,
                                "provider": "unknown",
                                "source_file": rel_path,
                                "database_type": db_type
                            }
                            self.scan_results["connection_strings"].append(conn_info)
                            self.scan_results["databases"].add(db_type)
        
        except Exception as e:
            logger.debug(f"Error extracting connection strings from XML file {xml_file}: {e}")
    
    def _process_yaml_files(self) -> None:
        """Process YAML configuration files"""
        docker_compose_files = [p for p in self.config_files["yaml"] 
                               if p.name.lower() in ("docker-compose.yml", "docker-compose.yaml")]
        
        # Process all YAML files
        for yaml_file in self.config_files["yaml"][:50]:  # Limit to first 50 files
            try:
                rel_path = str(yaml_file.relative_to(self.base_path))
                
                with open(yaml_file, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        data = yaml.safe_load(f)
                        if data and isinstance(data, dict):
                            # Extract connection information
                            self._extract_connections_from_dict(data, rel_path)
                            
                            # Special handling for docker-compose files
                            if yaml_file in docker_compose_files:
                                self._process_docker_compose(data, rel_path)
                            
                            # Check for Spring Boot application.yml
                            if 'spring' in data:
                                self.scan_results["frameworks"].setdefault("spring_boot", {
                                    "detected": True,
                                    "files": [rel_path]
                                })
                                
                                # Extract datasource information from Spring Boot config
                                if 'datasource' in data.get('spring', {}):
                                    ds = data['spring']['datasource']
                                    if 'url' in ds:
                                        url = ds['url']
                                        db_type = self._detect_database_from_connection_string(url)
                                        
                                        conn_info = {
                                            "name": ds.get('name', 'spring-datasource'),
                                            "connection_string": url,
                                            "username": ds.get('username', ''),
                                            "password_present": 'password' in ds,
                                            "source_file": rel_path,
                                            "database_type": db_type
                                        }
                                        self.scan_results["connection_strings"].append(conn_info)
                                        if db_type:
                                            self.scan_results["databases"].add(db_type)
                    
                    except yaml.YAMLError as e:
                        logger.debug(f"Error parsing YAML file {yaml_file}: {e}")
            
            except Exception as e:
                logger.debug(f"Error processing YAML file {yaml_file}: {e}")
    
    def _process_docker_compose(self, data: Dict, file_path: str) -> None:
        """Extract database information from docker-compose.yml"""
        if 'services' in data and isinstance(data['services'], dict):
            for service_name, service in data['services'].items():
                # Check if service is a database
                image = service.get('image', '')
                if any(db in image.lower() for db in ['mysql', 'postgres', 'postgresql', 'oracle', 'sqlserver', 'mongo', 'mariadb']):
                    # Determine database type
                    db_type = None
                    if 'mysql' in image.lower() or 'mariadb' in image.lower():
                        db_type = 'mysql'
                    elif 'postgres' in image.lower():
                        db_type = 'postgresql'
                    elif 'oracle' in image.lower():
                        db_type = 'oracle'
                    elif 'sqlserver' in image.lower() or 'mssql' in image.lower():
                        db_type = 'sqlserver'
                    elif 'mongo' in image.lower():
                        db_type = 'mongodb'
                    
                    if db_type:
                        self.scan_results["databases"].add(db_type)
                        
                        # Extract environment variables for connection info
                        if 'environment' in service:
                            env = service['environment']
                            conn_info = {
                                "name": service_name,
                                "database_type": db_type,
                                "source_file": file_path,
                                "docker_image": image
                            }
                            
                            # Extract credentials from environment variables
                            if isinstance(env, dict):
                                for env_var in ['MYSQL_DATABASE', 'POSTGRES_DB', 'ORACLE_SID', 'MSSQL_DATABASE', 'MONGO_INITDB_DATABASE']:
                                    if env_var in env:
                                        conn_info["database_name"] = env[env_var]
                                        break
                                
                                for env_var in ['MYSQL_USER', 'POSTGRES_USER', 'ORACLE_USER', 'MSSQL_USER', 'MONGO_INITDB_ROOT_USERNAME']:
                                    if env_var in env:
                                        conn_info["username"] = env[env_var]
                                        break
                                
                                conn_info["password_present"] = any(pwd_var in env for pwd_var in 
                                                                ['MYSQL_PASSWORD', 'POSTGRES_PASSWORD', 'ORACLE_PASSWORD', 'SA_PASSWORD', 'MONGO_INITDB_ROOT_PASSWORD'])
                            
                            elif isinstance(env, list):
                                for item in env:
                                    if isinstance(item, str) and '=' in item:
                                        key, value = item.split('=', 1)
                                        if key in ['MYSQL_DATABASE', 'POSTGRES_DB', 'ORACLE_SID', 'MSSQL_DATABASE', 'MONGO_INITDB_DATABASE']:
                                            conn_info["database_name"] = value
                                        elif key in ['MYSQL_USER', 'POSTGRES_USER', 'ORACLE_USER', 'MSSQL_USER', 'MONGO_INITDB_ROOT_USERNAME']:
                                            conn_info["username"] = value
                                        elif key in ['MYSQL_PASSWORD', 'POSTGRES_PASSWORD', 'ORACLE_PASSWORD', 'SA_PASSWORD', 'MONGO_INITDB_ROOT_PASSWORD']:
                                            conn_info["password_present"] = True
                            
                            self.scan_results["connection_strings"].append(conn_info)
    
    def _process_json_files(self) -> None:
        """Process JSON configuration files"""
        package_json_files = [p for p in self.config_files["json"] if p.name.lower() == "package.json"]
        appsettings_files = [p for p in self.config_files["json"] if p.name.lower().startswith("appsettings")]
        
        # Process package.json for Node.js/npm projects
        for pkg_file in package_json_files:
            self._process_package_json(pkg_file)
        
        # Process .NET appsettings.json
        for settings_file in appsettings_files:
            self._process_appsettings_json(settings_file)
        
        # Process other JSON files for connection strings
        other_json_files = [p for p in self.config_files["json"] 
                           if p not in package_json_files and p not in appsettings_files]
        
        for json_file in other_json_files[:50]:  # Limit to first 50 files
            try:
                rel_path = str(json_file.relative_to(self.base_path))
                
                with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        data = json.load(f)
                        if data and isinstance(data, dict):
                            # Extract connection information
                            self._extract_connections_from_dict(data, rel_path)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                pass
    
    def _process_package_json(self, pkg_file: Path) -> None:
        """Extract information from package.json files"""
        try:
            rel_path = str(pkg_file.relative_to(self.base_path))
            logger.info(f"Processing package.json: {rel_path}")
            
            with open(pkg_file, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    data = json.load(f)
                    
                    # Add to build tools
                    self.scan_results["build_tools"]["npm"] = {
                        "detected": True,
                        "files": [rel_path],
                        "project_info": {
                            "name": data.get("name", ""),
                            "version": data.get("version", ""),
                            "description": data.get("description", "")
                        }
                    }
                    
                    # Extract dependencies
                    dependencies = []
                    for dep_section in ["dependencies", "devDependencies"]:
                        if dep_section in data:
                            for name, version in data[dep_section].items():
                                dependencies.append({
                                    "name": name,
                                    "version": version,
                                    "type": dep_section
                                })
                    
                    # Store all dependencies
                    self.scan_results["dependencies"]["npm"] = dependencies
                    
                    # Detect frontend frameworks
                    if "dependencies" in data:
                        deps = data["dependencies"]
                        if "react" in deps:
                            self.scan_results["frameworks"]["react"] = {
                                "detected": True,
                                "version": deps["react"],
                                "files": [rel_path]
                            }
                        if "vue" in deps:
                            self.scan_results["frameworks"]["vue"] = {
                                "detected": True,
                                "version": deps["vue"],
                                "files": [rel_path]
                            }
                        if "angular" in deps or "@angular/core" in deps:
                            self.scan_results["frameworks"]["angular"] = {
                                "detected": True,
                                "version": deps.get("angular", deps.get("@angular/core", "")),
                                "files": [rel_path]
                            }
                            
                        # Check for database packages
                        db_packages = {
                            "mysql": ["mysql", "mysql2"],
                            "postgresql": ["pg", "postgres", "postgresql"],
                            "mongodb": ["mongodb", "mongoose"],
                            "oracle": ["oracledb"],
                            "sqlserver": ["mssql", "tedious"]
                        }
                        
                        for db_type, packages in db_packages.items():
                            if any(pkg in deps for pkg in packages):
                                self.scan_results["databases"].add(db_type)
                
                except json.JSONDecodeError as e:
                    logger.debug(f"Error parsing JSON in {pkg_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error processing package.json {pkg_file}: {e}")
    
    def _process_appsettings_json(self, settings_file: Path) -> None:
        """Extract information from .NET appsettings.json files"""
        try:
            rel_path = str(settings_file.relative_to(self.base_path))
            logger.info(f"Processing .NET appsettings.json: {rel_path}")
            
            with open(settings_file, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    data = json.load(f)
                    
                    # Look for connection strings
                    if "ConnectionStrings" in data:
                        for name, conn_str in data["ConnectionStrings"].items():
                            db_type = self._detect_database_from_connection_string(conn_str)
                            conn_info = {
                                "name": name,
                                "connection_string": conn_str,
                                "source_file": rel_path,
                                "database_type": db_type
                            }
                            self.scan_results["connection_strings"].append(conn_info)
                            if db_type:
                                self.scan_results["databases"].add(db_type)
                    
                    # Extract other configurations recursively
                    self._extract_connections_from_dict(data, rel_path)
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"Error parsing JSON in {settings_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error processing appsettings.json {settings_file}: {e}")
    
    def _process_properties_files(self) -> None:
        """Process Java .properties files"""
        for prop_file in self.config_files["properties"][:50]:  # Limit to first 50 files
            try:
                rel_path = str(prop_file.relative_to(self.base_path))
                
                with open(prop_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Look for JDBC URLs or connection strings
                    conn_patterns = [
                        r'(?:jdbc\.url|hibernate\.connection\.url|spring\.datasource\.url|connection\.url)\s*=\s*(.*)',
                        r'(?:jdbc\.connection\.string|connection\.string|connectionString)\s*=\s*(.*)'
                    ]
                    
                    for pattern in conn_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            conn_str = match.strip()
                            if conn_str:
                                db_type = self._detect_database_from_connection_string(conn_str)
                                conn_info = {
                                    "name": "properties-extracted",
                                    "connection_string": conn_str,
                                    "source_file": rel_path,
                                    "database_type": db_type
                                }
                                
                                # Look for username in the same file
                                username_match = re.search(r'(?:jdbc\.username|hibernate\.connection\.username|spring\.datasource\.username|username)\s*=\s*(.*)', content)
                                if username_match:
                                    conn_info["username"] = username_match.group(1).strip()
                                
                                # Check if password is present
                                password_match = re.search(r'(?:jdbc\.password|hibernate\.connection\.password|spring\.datasource\.password|password)\s*=\s*(.*)', content)
                                if password_match:
                                    conn_info["password_present"] = True
                                
                                self.scan_results["connection_strings"].append(conn_info)
                                if db_type:
                                    self.scan_results["databases"].add(db_type)
                    
                    # Detect Spring Boot
                    if 'spring.application.name' in content:
                        self.scan_results["frameworks"].setdefault("spring_boot", {
                            "detected": True,
                            "files": [rel_path]
                        })
                    
                    # Detect Hibernate
                    if 'hibernate.dialect' in content:
                        self.scan_results["frameworks"].setdefault("hibernate", {
                            "detected": True,
                            "files": [rel_path]
                        })
                        
                        # Extract dialect which can indicate database type
                        dialect_match = re.search(r'hibernate\.dialect\s*=\s*(.*)', content)
                        if dialect_match:
                            dialect = dialect_match.group(1).lower().strip()
                            if 'mysql' in dialect:
                                self.scan_results["databases"].add("mysql")
                            elif 'postgresql' in dialect:
                                self.scan_results["databases"].add("postgresql")
                            elif 'oracle' in dialect:
                                self.scan_results["databases"].add("oracle")
                            elif 'sqlserver' in dialect:
                                self.scan_results["databases"].add("sqlserver")
                            elif 'db2' in dialect:
                                self.scan_results["databases"].add("db2")
            
            except Exception as e:
                logger.debug(f"Error processing properties file {prop_file}: {e}")
    
    def _process_config_files(self) -> None:
        """Process special config files like .env, etc."""
        try:
            # Look for .env files
            env_files = list(self.base_path.glob("**/.env"))
            for env_file in env_files:
                if env_file.is_file():
                    rel_path = str(env_file.relative_to(self.base_path))
                    
                    with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Look for environment variables that might contain connection info
                        conn_patterns = [
                            r'(?:DATABASE_URL|DB_URL|CONNECTION_STRING)\s*=\s*(.*)',
                            r'(?:JDBC_URL|SPRING_DATASOURCE_URL)\s*=\s*(.*)'
                        ]
                        
                        for pattern in conn_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                            for match in matches:
                                conn_str = match.strip()
                                if conn_str:
                                    db_type = self._detect_database_from_connection_string(conn_str)
                                    conn_info = {
                                        "name": "env-extracted",
                                        "connection_string": conn_str,
                                        "source_file": rel_path,
                                        "database_type": db_type
                                    }
                                    self.scan_results["connection_strings"].append(conn_info)
                                    if db_type:
                                        self.scan_results["databases"].add(db_type)
        
        except Exception as e:
            logger.debug(f"Error processing config files: {e}")
    
    def _extract_connections_from_dict(self, data: Dict[str, Any], file_path: str, path: str = "") -> None:
        """Recursively extract connection strings from dictionaries (used for YAML/JSON)"""
        if not isinstance(data, dict):
            return
        
        # Connection string related keys
        conn_keys = ['connectionString', 'connection-string', 'connection_string', 'url', 'jdbc-url', 'jdbc_url', 'connection-url']
        
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if this key contains connection string
            if isinstance(value, str) and key.lower() in [k.lower() for k in conn_keys] and len(value) > 15:
                db_type = self._detect_database_from_connection_string(value)
                if db_type:
                    conn_info = {
                        "name": key,
                        "connection_string": value,
                        "source_file": file_path,
                        "path": current_path,
                        "database_type": db_type
                    }
                    self.scan_results["connection_strings"].append(conn_info)
                    self.scan_results["databases"].add(db_type)
            
            # If this is a nested dictionary, recurse
            elif isinstance(value, dict):
                self._extract_connections_from_dict(value, file_path, current_path)
            
            # If this is a list, check each item if it's a dictionary
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        item_path = f"{current_path}[{i}]"
                        self._extract_connections_from_dict(item, file_path, item_path)
    
    def _detect_database_from_connection_string(self, conn_str: str, provider: str = None) -> Optional[str]:
        """Detect database type from connection string"""
        conn_str = conn_str.lower()
        
        if provider:
            provider = provider.lower()
            if 'mysql' in provider:
                return 'mysql'
            elif 'postgresql' in provider or 'npgsql' in provider:
                return 'postgresql'
            elif 'oracle' in provider:
                return 'oracle'
            elif 'sqlserver' in provider or 'system.data.sqlclient' in provider:
                return 'sqlserver'
            elif 'sqlite' in provider:
                return 'sqlite'
            elif 'db2' in provider:
                return 'db2'
        
        # Check JDBC URLs
        if 'jdbc:' in conn_str:
            if 'mysql' in conn_str:
                return 'mysql'
            elif 'postgresql' in conn_str or 'postgres' in conn_str:
                return 'postgresql'
            elif 'oracle' in conn_str:
                return 'oracle'
            elif 'sqlserver' in conn_str:
                return 'sqlserver'
            elif 'db2' in conn_str:
                return 'db2'
            elif 'sqlite' in conn_str:
                return 'sqlite'
        
        # Check connection strings
        if 'server=' in conn_str or 'data source=' in conn_str:
            if 'mysql' in conn_str:
                return 'mysql'
            elif 'initial catalog=' in conn_str or 'database=' in conn_str:
                return 'sqlserver'  # Most likely SQL Server
        
        # Check for SQLite connections
        if '.db' in conn_str and ('sqlite' in conn_str or 'data source=' in conn_str):
            return 'sqlite'
        
        # Check for PostgreSQL
        if 'postgresql' in conn_str or 'postgres://' in conn_str:
            return 'postgresql'
        
        # Check for MongoDB connection strings
        if 'mongodb://' in conn_str or 'mongodb+srv://' in conn_str:
            return 'mongodb'
        
        return None