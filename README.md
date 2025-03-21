# Testing Your Wedding Website

This README explains how to run tests for your wedding website application.

## Test Structure

The tests are organized as follows:

- **Unit Tests**: Testing individual components like models and utility functions
- **Integration Tests**: Testing route handlers and database interactions
- **Functional Tests**: End-to-end testing with browser automation

## Setting Up for Testing

### 1. Install Testing Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- pytest and related plugins
- Code quality tools (flake8, black, isort, mypy, pylint)
- Testing tools (coverage, tox)

### 2. Test Configuration

Tests use a separate configuration defined in `tests/conftest.py` that:
- Uses an in-memory SQLite database
- Disables CSRF protection
- Configures test email settings

## Running the Tests

### Running All Tests

To run all tests (except functional tests):

```bash
pytest -v
```

### Running Specific Test Files

```bash
# Run model tests only
pytest -v tests/test_models.py

# Run route tests only
pytest -v tests/test_routes.py

# Run utility tests only
pytest -v tests/test_utils.py
```

### Running Tests with Coverage Report

```bash
pytest --cov=app tests/
```

For a detailed HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

This will create a `htmlcov` directory with coverage reports.

## Code Quality Tools

The project uses several tools to maintain code quality:

### Linting and Formatting

```bash
# Run flake8 for PEP 8 compliance
flake8 app tests

# Run black for code formatting
black app tests

# Run isort for import sorting
isort app tests

# Run mypy for type checking
mypy app tests

# Run pylint for code analysis
pylint app tests
```

### Running All Code Quality Checks

```bash
tox -e lint
```

## Functional Tests

Functional tests use Selenium to automate browser-based testing. These tests are disabled by default.

### Requirements for Functional Tests

1. Install a WebDriver:
   - For Chrome: [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)
   - For Firefox: [GeckoDriver](https://github.com/mozilla/geckodriver/releases)

2. Make sure the WebDriver is in your system PATH

### Running Functional Tests

Enable and run functional tests with:

```bash
RUN_FUNCTIONAL_TESTS=1 pytest -v tests/test_functional.py
```

Note: Functional tests might be brittle if your web interface changes. They're primarily for regression testing after your UI is stable.

## Continuous Integration

The project uses GitHub Actions for CI/CD. The workflow:
1. Runs tests against Python 3.9, 3.10, and 3.11
2. Generates and uploads coverage reports to Codecov
3. Runs all code quality checks
4. Triggers on push to main/develop and pull requests

## Best Practices

1. **Test Coverage**: Aim for at least 80% test coverage
2. **Isolation**: Each test should be isolated and not depend on other tests
3. **Fixtures**: Use fixtures for setting up test data
4. **Mocking**: Use mocking for external services (email, etc.)
5. **Maintenance**: Update tests when your application changes
6. **Code Quality**: Run all linting tools before committing changes
7. **Type Hints**: Use type hints and run mypy to catch type-related issues

Happy testing!