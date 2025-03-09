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
pip install pytest pytest-flask pytest-cov pytest-flask-sqlalchemy selenium
```

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

For CI/CD pipelines (like GitHub Actions, GitLab CI, etc.), create a workflow that:

1. Sets up Python
2. Installs dependencies  
3. Runs tests
4. Generates coverage reports

## Best Practices

1. **Test Coverage**: Aim for at least 80% test coverage
2. **Isolation**: Each test should be isolated and not depend on other tests
3. **Fixtures**: Use fixtures for setting up test data
4. **Mocking**: Use mocking for external services (email, etc.)
5. **Maintenance**: Update tests when your application changes

Happy testing!