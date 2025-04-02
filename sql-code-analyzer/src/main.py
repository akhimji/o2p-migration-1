import sys
import logging
import json
import os
from pathlib import Path
from reporting.html_report_generator import HTMLReportGenerator
from reporting.report_generator import ReportGenerator
import argparse

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, str(Path(__file__).parent))

from scanner.java_scanner import JavaScanner
from scanner.dotnet_scanner import DotNetScanner
from scanner.config_scanner import ConfigScanner
from parsers.sql_parser import SQLParser
from analyzers.sql_analyzer import SQLAnalyzer

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

def create_appropriate_scanner(project_path, project_type, use_sqlparse=True):
    """Create the appropriate scanner based on project type"""
    if project_type == "java":
        return JavaScanner(project_path, use_sqlparse=use_sqlparse)
    elif project_type == "dotnet":
        return DotNetScanner(project_path, use_sqlparse=use_sqlparse)
    else:
        # Default to a combined scanner for unknown projects
        return CombinedScanner(project_path, use_sqlparse=use_sqlparse)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='SQL Code Analyzer')
    parser.add_argument('--path', '-p', help='Path to the project directory')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--output', '-o', help='Output directory for reports')
    parser.add_argument('--no-sqlparse', action='store_true', help='Disable sqlparse library for validation')
    parser.add_argument('--json-report', help='Path to save JSON report')
    parser.add_argument('--html-report', help='Path to save HTML report')
    args = parser.parse_args()
    
    print("=== SQL Code Analyzer ===")
    
    # Get project directory from command-line args or user input
    if args.path:
        project_path = args.path
    else:
        project_path = input("Enter the path to the project directory: ")
    
    # Convert to absolute path and verify existence
    project_path = os.path.abspath(project_path)
    if not Path(project_path).exists():
        logger.error(f"Error: Path '{project_path}' does not exist.")
        return
    
    print(f"Analyzing project at: {project_path}")
    
    # Set output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(project_path)
    
    os.makedirs(output_dir, exist_ok=True)
    
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
    use_sqlparse = not args.no_sqlparse
    scanner = create_appropriate_scanner(project_path, project_type, use_sqlparse=use_sqlparse)
    
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
        report_generator = ReportGenerator()
        
        # Generate JSON report
        if args.json_report:
            json_file = args.json_report
            report_generator.generate_json_report(sql_queries, json_file)
            logger.info(f"JSON report saved to {json_file}")
        
        # Generate HTML report
        if args.html_report:
            html_file = args.html_report
            report_generator.generate_html_report(sql_queries, html_file)
            logger.info(f"HTML report saved to {html_file}")
            
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