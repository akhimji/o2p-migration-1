import unittest
from src.parsers.sql_parser import SQLParser

class TestSQLParser(unittest.TestCase):

    def setUp(self):
        self.parser = SQLParser()

    def test_clean_sql(self):
        raw_sql = "SELECT * FROM users WHERE id = 1;"
        cleaned_sql = self.parser.clean_sql(raw_sql)
        self.assertEqual(cleaned_sql, "SELECT * FROM users WHERE id = 1")

    def test_split_multi_statement_sql(self):
        multi_sql = "SELECT * FROM users; SELECT * FROM orders;"
        split_sql = self.parser.split_multi_statement_sql(multi_sql)
        self.assertEqual(split_sql, ["SELECT * FROM users", "SELECT * FROM orders"])

    def test_identify_operations(self):
        sql = "INSERT INTO users (name, age) VALUES ('Alice', 30);"
        operation = self.parser.identify_operation(sql)
        self.assertEqual(operation, "INSERT")

    def test_extract_schema_elements(self):
        sql = "SELECT name, age FROM users;"
        tables, columns = self.parser.extract_schema_elements(sql)
        self.assertEqual(tables, ["users"])
        self.assertEqual(columns, ["name", "age"])

if __name__ == '__main__':
    unittest.main()