class ScanResult:
    def __init__(self):
        self.sql_queries = []
        self.tech_components = []
        self.schema_patterns = {}

    def add_sql_query(self, sql_query):
        self.sql_queries.append(sql_query)

    def add_tech_component(self, tech_component):
        self.tech_components.append(tech_component)

    def add_schema_pattern(self, pattern_name, pattern_details):
        self.schema_patterns[pattern_name] = pattern_details

    def summarize(self):
        return {
            "sql_queries": self.sql_queries,
            "tech_components": self.tech_components,
            "schema_patterns": self.schema_patterns,
        }