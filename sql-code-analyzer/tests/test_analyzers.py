import unittest
from src.analyzers.sql_analyzer import SQLAnalyzer
from src.analyzers.tech_stack_analyzer import TechStackAnalyzer
from src.analyzers.schema_analyzer import SchemaAnalyzer

class TestSQLAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sql_analyzer = SQLAnalyzer()

    def test_analyze_select_query(self):
        query = "SELECT * FROM users WHERE id = 1;"
        result = self.sql_analyzer.analyze(query)
        self.assertEqual(result['operation'], 'SELECT')
        self.assertIn('users', result['tables'])

    def test_analyze_insert_query(self):
        query = "INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');"
        result = self.sql_analyzer.analyze(query)
        self.assertEqual(result['operation'], 'INSERT')
        self.assertIn('users', result['tables'])

class TestTechStackAnalyzer(unittest.TestCase):
    def setUp(self):
        self.tech_stack_analyzer = TechStackAnalyzer()

    def test_detect_maven_dependency(self):
        pom_content = "<dependencies><dependency><groupId>org.springframework</groupId><artifactId>spring-core</artifactId></dependency></dependencies>"
        result = self.tech_stack_analyzer.detect_dependencies(pom_content)
        self.assertIn('spring-core', result)

class TestSchemaAnalyzer(unittest.TestCase):
    def setUp(self):
        self.schema_analyzer = SchemaAnalyzer()

    def test_extract_schema_elements(self):
        query = "SELECT id, name FROM users;"
        result = self.schema_analyzer.extract_schema_elements(query)
        self.assertIn('users', result['tables'])
        self.assertIn('id', result['columns'])
        self.assertIn('name', result['columns'])

if __name__ == '__main__':
    unittest.main()