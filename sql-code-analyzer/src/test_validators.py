#!/usr/bin/env python3
import os
import sys
from validators.sql_validator import SQLValidator
from validators.sqlparse_validator import SqlParseValidator

def test_validators():
    print("Testing SQL Validators...")
    
    # Test cases - pairs of [text, expected_result]
    test_cases = [
        # Valid SQL
        ["SELECT * FROM customers WHERE age > 18", True],
        ["INSERT INTO products (name, price) VALUES ('Widget', 19.99)", True],
        ["UPDATE users SET active = 1 WHERE last_login > '2023-01-01'", True],
        ["DELETE FROM orders WHERE status = 'cancelled'", True],
        ["CREATE TABLE employees (id INT, name VARCHAR(100))", True],
        ["ALTER TABLE products ADD COLUMN description TEXT", True],
        ["DROP TABLE temp_data", True],
        ["MERGE INTO customers USING new_data ON (customers.id = new_data.id)", True],
        ["WITH cte AS (SELECT * FROM orders) SELECT * FROM cte", True],
        ["SELECT o.id, c.name FROM orders o JOIN customers c ON o.customer_id = c.id", True],
        
        # False positives (should be rejected)
        ["createProductDiscountPrice(product, price)", False],
        ["selectAllItems()", False],
        ["updateUserProfile(user)", False],
        ["deleteFromCache(key)", False],
        ["createTable.setHeaders(['Name', 'Email'])", False],
        ["Select an option from the dropdown", False],
        ["Update your profile information", False],
        ["select.options = ['Option 1', 'Option 2']", False],
        ["this.table.insert(row)", False],
        ["<!-- create table layout for responsive design -->", False],
    ]
    
    # Initialize validators
    basic_validator = SQLValidator()
    sqlparse_validator = SqlParseValidator()
    
    # Run tests
    basic_passed = 0
    sqlparse_passed = 0
    
    print("\nRunning validation tests:")
    print("=" * 80)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        # Test basic validator
        is_valid, reason = basic_validator.is_valid_sql(text)
        basic_result = "PASS" if is_valid == expected else "FAIL"
        if is_valid == expected:
            basic_passed += 1
            
        # Test sqlparse validator
        sp_is_valid, sp_reason = sqlparse_validator.is_valid_sql(text)
        sp_result = "PASS" if sp_is_valid == expected else "FAIL"
        if sp_is_valid == expected:
            sqlparse_passed += 1
        
        # Print results
        print(f"{i:2}. {'SQL' if expected else 'NOT SQL'}: {text[:50] + '...' if len(text) > 50 else text}")
        print(f"   Basic Validator: {basic_result} - {reason}")
        print(f"   SQLParse Validator: {sp_result} - {sp_reason}")
        print("-" * 80)
    
    # Print summary
    total = len(test_cases)
    print("\nResults Summary:")
    print(f"Basic Validator: {basic_passed}/{total} tests passed ({basic_passed/total*100:.1f}%)")
    print(f"SQLParse Validator: {sqlparse_passed}/{total} tests passed ({sqlparse_passed/total*100:.1f}%)")
    
    if basic_passed == total and sqlparse_passed == total:
        print("\nAll tests passed! The validators are working correctly.")
    else:
        print("\nSome tests failed. The validators may need adjustment.")
        
if __name__ == "__main__":
    # Add parent directory to path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Run tests
    test_validators()