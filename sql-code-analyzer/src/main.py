import sys
import logging
import json
import os
from pathlib import Path

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, str(Path(__file__).parent))

from scanner.java_scanner import JavaScanner
from scanner.dotnet_scanner import DotNetScanner
from scanner.config_scanner import ConfigScanner
from parsers.sql_parser import SQLParser
from analyzers.sql_analyzer import SQLAnalyzer
from reporting.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SQLCodeAnalyzer')

def detect_project_type(project_path: Path) -> str:
    """
    Detect the primary technology of the project
    Returns: 'java', 'dotnet', or 'unknown'
    """
    logger.info(f"Detecting project type in {project_path}")
    
    # Count relevant files for each technology
    java_files = list(project_path.glob("**/*.java"))
    pom_files = list(project_path.glob("**/pom.xml"))
    gradle_files = list(project_path.glob("**/*.gradle"))
    
    dotnet_files = list(project_path.glob("**/*.cs"))
    dotnet_files.extend(project_path.glob("**/*.vb"))
    csproj_files = list(project_path.glob("**/*.csproj"))
    vbproj_files = list(project_path.glob("**/*.vbproj"))
    sln_files = list(project_path.glob("**/*.sln"))
    
    # Score each technology
    java_score = len(java_files) * 1 + len(pom_files) * 10 + len(gradle_files) * 10
    dotnet_score = len(dotnet_files) * 1 + len(csproj_files) * 10 + len(vbproj_files) * 10 + len(sln_files) * 10
    
    logger.info(f"Project type detection - Java score: {java_score}, .NET score: {dotnet_score}")
    
    # Determine project type
    if java_score > dotnet_score and java_score > 0:
        return 'java'
    elif dotnet_score > 0:
        return 'dotnet'
    else:
        return 'unknown'

def create_appropriate_scanner(project_path: str, project_type: str = None):
    """Create and return the appropriate scanner based on project type"""
    if not project_type:
        project_type = detect_project_type(Path(project_path))
    
    if project_type == 'java':
        logger.info("Using Java scanner for this project")
        return JavaScanner(project_path)
    elif project_type == 'dotnet':
        logger.info("Using .NET scanner for this project")
        return DotNetScanner(project_path)
    else:
        logger.warning("Could not determine project type, defaulting to Java scanner")
        return JavaScanner(project_path)

def main():
    print("=== SQL Code Analyzer ===")
    
    # Get project directory from user or command line
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = input("Enter the path to the project directory: ")
    
    # Convert to absolute path and verify existence
    project_path = os.path.abspath(project_path)
    if not Path(project_path).exists():
        logger.error(f"Error: Path '{project_path}' does not exist.")
        return
    
    print(f"Analyzing project at: {project_path}")
    
    # Detect project type and create appropriate scanner
    project_type = detect_project_type(Path(project_path))
    print(f"Detected project type: {project_type.upper()}")
    
    # Scan for configuration files regardless of project type
    print("Scanning for configuration files...")
    config_scanner = ConfigScanner(project_path)
    config_info = config_scanner.scan()
    
    # Detect project type using config information if available
    if not project_type or project_type == 'unknown':
        # Try to infer project type from config files
        if config_info["build_tools"].get("maven", {}).get("detected", False):
            project_type = 'java'
            print("Project type determined from Maven configuration: JAVA")
        elif any(db.startswith("dot") for db in config_info["frameworks"].keys()):
            project_type = 'dotnet'
            print("Project type determined from .NET configuration: .NET")
    
    # Create the appropriate scanner
    scanner = create_appropriate_scanner(project_path, project_type)
    
    # Initialize components
    sql_parser = SQLParser()
    sql_analyzer = SQLAnalyzer()
    report_gen = ReportGenerator()
    
    # Scan for SQL queries
    print(f"Scanning files in {project_path}...")
    sql_queries = scanner.scan()
    
    # Detect tech stack information
    print("Detecting technology stack...")
    tech_stack = scanner.get_tech_stack_info()
    
    # Merge tech stack information from code scanner and config scanner
    tech_stack.update(config_info["frameworks"])
    tech_stack.update(config_info["build_tools"])
    
    # Add database information
    if config_info["databases"]:
        tech_stack["databases"] = {
            "detected": bool(config_info["databases"]),
            "types": list(config_info["databases"])
        }
    
    # Add connection strings information
    if config_info["connection_strings"]:
        tech_stack["connection_strings"] = {
            "detected": True,
            "count": len(config_info["connection_strings"])
        }
    
    # Display tech stack summary
    print("\n=== Technology Stack ===")
    for tech, info in tech_stack.items():
        if isinstance(info, dict) and info.get("detected", False):
            if tech == "databases":
                db_types = ", ".join(info.get("types", []))
                print(f"✓ Databases detected: {db_types}")
            elif tech == "connection_strings":
                print(f"✓ Connection strings found: {info.get('count', 0)}")
            else:
                print(f"✓ {tech.replace('_', ' ').capitalize()} detected")
        elif isinstance(info, bool) and info:
            print(f"✓ {tech.replace('_', ' ').capitalize()} detected")
        else:
            print(f"✗ {tech.replace('_', ' ').capitalize()} not detected")
    
    # Make sure we have results before proceeding with SQL analysis
    if not sql_queries:
        print("\nNo SQL queries found in the project.")
        return
    
    # Parse and analyze SQL queries
    print(f"\nParsing and analyzing {len(sql_queries)} SQL queries...")
    parsed_queries = []
    for query in sql_queries:
        try:
            parsed_query = sql_parser.parse(query)
            if parsed_query:
                parsed_queries.append(parsed_query)
        except Exception as e:
            logger.warning(f"Failed to parse query: {str(e)[:100]}...")
    
    print(f"Successfully parsed {len(parsed_queries)} out of {len(sql_queries)} queries")
    
    try:
        analyzed_queries = sql_analyzer.analyze_queries(parsed_queries)
        
        # Generate reports
        print("Generating analysis reports...")
        sql_report = report_gen.generate_summary_report(analyzed_queries)
        config_report = report_gen.generate_config_report(config_info)
        
        print("\n=== SQL Analysis Report ===")
        print(sql_report)
        print("\n=== Configuration Analysis ===")
        print(config_report)
        print("===========================")
        
        # Ask user if they want to save the report
        save_report = input("\nWould you like to save the report? (y/n): ").strip()
        if save_report.lower() == 'y':
            report_path = Path(project_path) / "sql_analysis_report.txt"
            with open(report_path, 'w') as f:
                f.write("=== SQL Analysis Report ===\n")
                f.write(sql_report)
                f.write("\n\n=== Configuration Analysis ===\n")
                f.write(config_report)
                f.write("\n\n=== Technology Stack ===\n")
                for tech, info in tech_stack.items():
                    if isinstance(info, dict) and info.get("detected", False):
                        if tech == "databases":
                            db_types = ", ".join(info.get("types", []))
                            f.write(f"✓ Databases detected: {db_types}\n")
                        elif tech == "connection_strings":
                            f.write(f"✓ Connection strings found: {info.get('count', 0)}\n")
                        else:
                            f.write(f"✓ {tech.replace('_', ' ').capitalize()} detected\n")
                    elif isinstance(info, bool) and info:
                        f.write(f"✓ {tech.replace('_', ' ').capitalize()} detected\n")
                    else:
                        f.write(f"✗ {tech.replace('_', ' ').capitalize()} not detected\n")
            print(f"Report saved to {report_path}")
            
            # Save detailed JSON data for further processing
            json_path = Path(project_path) / "sql_analysis_data.json"
            json_data = {
                "project_type": project_type,
                "queries": [query.to_dict() for query in analyzed_queries],
                "tech_stack": tech_stack,
                "connection_strings": config_info["connection_strings"],
                "dependencies": config_info["dependencies"]
            }
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            print(f"Detailed analysis data saved to {json_path}")
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        print(f"\nError during analysis: {e}")
        print("Partial results may be available.")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print("\nAn error occurred during analysis. See log for details.")