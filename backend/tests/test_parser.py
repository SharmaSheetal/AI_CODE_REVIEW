"""
test_parser.py — Unit tests for the Tree-sitter Python parser.

These tests run fully offline — no API key or LLM needed.
They verify that parse_python_file correctly extracts function metadata from the AST.
"""

from backend.core.parser import parse_python_file

SAMPLE_CODE = '''
def add(a, b):
    """Adds two numbers."""
    return a + b

def no_doc(x):
    return x * 2

def no_return(name):
    print(name)
'''


def test_extracts_correct_number_of_functions():
    result = parse_python_file("sample.py", SAMPLE_CODE)
    assert len(result.functions) == 3


def test_detects_docstring():
    result = parse_python_file("sample.py", SAMPLE_CODE)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert add_fn.has_docstring is True


def test_detects_missing_docstring():
    result = parse_python_file("sample.py", SAMPLE_CODE)
    no_doc_fn = next(f for f in result.functions if f.name == "no_doc")
    assert no_doc_fn.has_docstring is False


def test_detects_return_statement():
    result = parse_python_file("sample.py", SAMPLE_CODE)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert add_fn.has_return is True


def test_detects_missing_return():
    result = parse_python_file("sample.py", SAMPLE_CODE)
    no_return_fn = next(f for f in result.functions if f.name == "no_return")
    assert no_return_fn.has_return is False


def test_extracts_parameter_names():
    result = parse_python_file("sample.py", SAMPLE_CODE)
    add_fn = next(f for f in result.functions if f.name == "add")
    assert "a" in add_fn.parameter_names
    assert "b" in add_fn.parameter_names


def test_handles_syntax_error_gracefully():
    bad_code = "def broken(:\n    pass"
    result = parse_python_file("bad.py", bad_code)
    assert result.parse_error is True
