# coverage_report.py
import pytest
import os
import sys

def run_coverage():
    """Run pytest with coverage and generate report."""
    # Run tests with coverage
    pytest.main(['--cov=app', '--cov-report=term', '--cov-report=html', 'tests/'])
    
    # Print location of the HTML report
    print("\nHTML coverage report generated at: htmlcov/index.html")
    
    # Optional: Open the report in browser
    try:
        import webbrowser
        webbrowser.open('htmlcov/index.html')
    except:
        pass

if __name__ == '__main__':
    run_coverage()