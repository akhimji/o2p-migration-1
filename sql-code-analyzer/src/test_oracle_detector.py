#!/usr/bin/env python3
import os
import sys
from parsers.oracle_detector import OracleFeatureDetector

def test_oracle_detector():
    print("Testing Oracle Feature Detector...")
    
    # Initialize detector
    detector = OracleFeatureDetector()
    
    # Test cases - pairs of [query, expected_oracle_specific]
    test_cases = [
        # Oracle-specific queries
        ["SELECT * FROM employees WHERE ROWNUM < 10", True],
        ["SELECT e.*, ROWID FROM employees e", True],
        ["SELECT * FROM employees CONNECT BY PRIOR emp_id = manager_id START WITH manager_id IS NULL", True],
        ["SELECT * FROM employees WHERE hire_date = TO_DATE('2022-01-01', 'YYYY-MM-DD')", True],
        ["SELECT NVL(salary, 0) FROM employees", True],
        ["SELECT DECODE(status, 'A', 'Active', 'I', 'Inactive', 'Unknown') FROM employees", True],
        ["SELECT /*+ INDEX(employees emp_idx) */ * FROM employees", True],
        ["SELECT employee_id, MONTHS_BETWEEN(SYSDATE, hire_date) tenure FROM employees", True],
        ["SELECT * FROM employees e WHERE e.dept_id(+) = d.dept_id", True],
        ["SELECT * FROM employees PIVOT (COUNT(*) FOR status IN ('A', 'I', 'P'))", True],
        ["INSERT INTO employees VALUES (emp_seq.NEXTVAL, 'John', 'Doe')", True],
        ["MERGE INTO target_table t USING source_table s ON (t.id = s.id)", True],
        ["SELECT * FROM TABLE(my_collection)", True],
        ["SELECT * FROM employees AS OF TIMESTAMP SYSTIMESTAMP - INTERVAL '1' HOUR", True],
        ["SELECT * FROM DUAL", True],
        ["SELECT COUNT(*) FROM USER_TABLES", True],
        
        # Non-Oracle-specific queries
        ["SELECT * FROM employees WHERE id = 1", False],
        ["INSERT INTO products (name, price) VALUES ('Gadget', 19.99)", False],
        ["UPDATE customers SET status = 'active' WHERE id = 1", False],
        ["DELETE FROM orders WHERE status = 'cancelled'", False],
        ["SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept_id = d.id", False],
        ["CREATE TABLE new_employees (id INT, name VARCHAR(100))", False],
        ["ALTER TABLE products ADD COLUMN description TEXT", False],
        ["SELECT * FROM orders WHERE created_at > '2023-01-01'", False],
        ["WITH cte AS (SELECT * FROM orders) SELECT * FROM cte", False],
    ]
    
    # Run tests
    passed = 0
    
    print("\nRunning Oracle feature detection tests:")
    print("=" * 80)
    
    for i, (query, expected) in enumerate(test_cases, 1):
        # Detect Oracle features
        features = detector.detect_oracle_features(query)
        is_oracle = len(features) > 0
        
        # Check result
        result = "PASS" if is_oracle == expected else "FAIL"
        if is_oracle == expected:
            passed += 1
        
        # Print results
        print(f"{i:2}. {'Oracle' if expected else 'Standard SQL'}: {query[:50] + '...' if len(query) > 50 else query}")
        
        if is_oracle:
            print(f"   Detected features: {', '.join(features.keys())}")
        
        print(f"   Result: {result}")
        
        if result == "FAIL":
            if expected:
                print(f"   ERROR: Expected to find Oracle features but none were detected")
            else:
                print(f"   ERROR: Incorrectly identified as Oracle: {', '.join(features.keys())}")
                
        print("-" * 80)
    
    # Print summary
    total = len(test_cases)
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nAll Oracle detection tests passed!")
    else:
        print("\nSome Oracle detection tests failed.")
        
if __name__ == "__main__":
    # Add parent directory to path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Run tests
    test_oracle_detector()