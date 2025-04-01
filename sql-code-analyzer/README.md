# SQL Code Analyzer

## Overview
SQL Code Analyzer is a modular Python application designed to scan source code repositories, primarily focusing on Java and .NET projects. The application detects and extracts SQL queries, analyzes technology stack components, and provides insights into SQL usage and schema patterns.

## Features
- **Code Scanning**: 
  - Traverses project files to extract raw SQL queries using regex or AST parsing.
  - Detects presence of WebLogic and Maven dependencies.

- **SQL Processing**: 
  - Cleans and normalizes SQL statements.
  - Splits multi-statement SQL.
  - Identifies SQL operations (SELECT, INSERT, etc.).
  - Extracts schema elements like table names and columns.

- **Tech Stack Insights**: 
  - Parses `pom.xml` for Maven-based Java projects.
  - Detects WebLogic usage via configuration files and source patterns.

- **Data Transformation**: 
  - Aggregates and enriches scan results for reporting.
  - Supports Oracle-specific SQL features (to be expanded for .NET).

- **Report Generation**: 
  - Produces summaries of SQL usage, technologies detected, and schema patterns.
  - Can be extended for visualization or export.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sql-code-analyzer.git
   ```
2. Navigate to the project directory:
   ```
   cd sql-code-analyzer
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application, execute the following command:
```
python src/main.py <path_to_project>
```
Replace `<path_to_project>` with the path to the source code repository you want to analyze.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.