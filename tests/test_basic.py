# tests/test_basic.py
"""Basic tests to verify the forensic image transformation project setup"""

def test_pytest_working():
    """Test that pytest is working correctly"""
    assert True

def test_basic_math():
    """Test basic mathematical operations"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5

def test_string_operations():
    """Test basic string operations"""
    test_string = "forensic_analysis"
    assert len(test_string) == 17
    assert test_string.startswith("forensic")
    assert test_string.endswith("analysis")

def test_list_operations():
    """Test basic list operations"""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    assert max(test_list) == 5 
