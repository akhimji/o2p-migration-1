def format_sql_report(sql_usage):
    report = "SQL Usage Report\n"
    report += "=" * 50 + "\n"
    for query in sql_usage:
        report += f"Query: {query['query']}\n"
        report += f"Operation: {query['operation']}\n"
        report += f"Tables: {', '.join(query['tables'])}\n"
        report += f"Columns: {', '.join(query['columns'])}\n"
        report += "-" * 50 + "\n"
    return report


def format_tech_stack_report(tech_stack):
    report = "Tech Stack Report\n"
    report += "=" * 50 + "\n"
    for component in tech_stack:
        report += f"Component: {component['name']}\n"
        report += f"Version: {component['version']}\n"
        report += "-" * 50 + "\n"
    return report


def format_summary_report(sql_usage, tech_stack):
    report = "Summary Report\n"
    report += "=" * 50 + "\n"
    report += f"Total SQL Queries: {len(sql_usage)}\n"
    report += f"Total Tech Components: {len(tech_stack)}\n"
    report += "-" * 50 + "\n"
    return report