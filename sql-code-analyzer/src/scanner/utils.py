def extract_sql_queries(file_content):
    sql_pattern = r"(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\s+.*?;"
    return re.findall(sql_pattern, file_content, re.IGNORECASE)

def normalize_sql(sql_query):
    return sql_query.strip().replace('\n', ' ')

def split_multi_statement_sql(sql_query):
    return [stmt.strip() for stmt in sql_query.split(';') if stmt.strip()]

def extract_table_names(sql_query):
    table_pattern = r"(?i)(FROM|JOIN)\s+([a-zA-Z0-9_\.]+)"
    return re.findall(table_pattern, sql_query)

def extract_columns(sql_query):
    column_pattern = r"SELECT\s+(.*?)\s+FROM"
    match = re.search(column_pattern, sql_query, re.IGNORECASE)
    if match:
        return [col.strip() for col in match.group(1).split(',')]
    return []

def detect_weblogic_usage(config_content):
    weblogic_patterns = [r"weblogic", r"weblogic.xml", r"weblogic.jar"]
    return any(re.search(pattern, config_content, re.IGNORECASE) for pattern in weblogic_patterns)