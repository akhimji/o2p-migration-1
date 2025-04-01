class CodeScanner:
    def __init__(self, project_path):
        self.project_path = project_path
        self.sql_queries = []
        self.dependencies = []

    def scan(self):
        self.traverse_files(self.project_path)

    def traverse_files(self, path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.java'):
                    self.scan_java_file(os.path.join(root, file))

    def scan_java_file(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            self.extract_sql_queries(content)
            self.detect_dependencies(content)

    def extract_sql_queries(self, content):
        sql_pattern = r'(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+.*?;'
        queries = re.findall(sql_pattern, content, re.DOTALL)
        self.sql_queries.extend(queries)

    def detect_dependencies(self, content):
        if '<dependency>' in content:
            self.dependencies.append('Maven dependency detected')

    def get_sql_queries(self):
        return self.sql_queries

    def get_dependencies(self):
        return self.dependencies