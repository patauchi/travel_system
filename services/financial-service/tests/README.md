# Financial Service Tests

This directory contains comprehensive test suites for the Financial Service modular architecture.

## Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_integration.py      # Integration tests for all modules
├── README.md               # This file
└── __pycache__/            # Python cache files
```

## Test Categories

### 1. Health Check Tests (`TestHealthChecks`)
- **Purpose**: Verify service health endpoints and basic connectivity
- **Coverage**: Main health, financial health, authentication test endpoints
- **Runtime**: ~2-5 seconds

### 2. Module-Specific Tests
Each module has dedicated test classes:

#### Orders Module (`TestOrdersModule`)
- **Models**: Order, OrderLine, PassengerDocument
- **Endpoints**: CRUD operations, order lines, passenger documents
- **Features**: Order lifecycle, document management

#### Expenses Module (`TestExpensesModule`)
- **Models**: Expense, ExpenseCategory
- **Endpoints**: CRUD, approval workflow, reimbursement, reporting
- **Features**: Category management, approval workflow, expense reporting

#### Petty Cash Module (`TestPettyCashModule`)
- **Models**: PettyCash, PettyCashTransaction
- **Endpoints**: Fund management, transactions, reconciliation, replenishment
- **Features**: Fund lifecycle, transaction tracking, reconciliation

#### Voucher Module (`TestVoucherModule`)
- **Models**: Voucher
- **Endpoints**: CRUD, approval, payment processing, bulk operations
- **Features**: Payment voucher workflow, bulk processing

#### Invoices Module (`TestInvoicesModule`)
- **Models**: Invoice, InvoiceLine, AccountsReceivable, AccountsPayable
- **Endpoints**: Invoice management, AR/AP, payment recording
- **Features**: Invoice lifecycle, payment tracking, AR/AP management

#### Payments Module (`TestPaymentsModule`)
- **Models**: Payment, PaymentGateway, PaymentAttempt
- **Endpoints**: Payment processing, gateway management, refunds
- **Features**: Payment processing, gateway integration, transaction management

### 3. Cross-Module Integration Tests (`TestCrossModuleIntegration`)
- **Purpose**: Test workflows that span multiple modules
- **Examples**: 
  - Order → Invoice → Payment flow
  - Expense → Voucher flow
- **Coverage**: End-to-end business processes

### 4. Error Handling Tests (`TestErrorHandling`)
- **Purpose**: Verify proper error responses and validation
- **Coverage**: 404 errors, validation errors, authorization errors
- **Features**: Comprehensive error scenario testing

### 5. Performance Tests (`TestPerformance`)
- **Purpose**: Basic performance and load testing
- **Coverage**: Bulk operations, pagination, summary endpoints
- **Metrics**: Response times, throughput

## Running Tests

### Prerequisites

1. **Python Dependencies**:
   ```bash
   pip install pytest pytest-cov fastapi sqlalchemy pydantic
   ```

2. **Database Setup**:
   - PostgreSQL running on localhost:5432
   - Test database: `financial_test_db`
   ```sql
   CREATE DATABASE financial_test_db;
   ```

3. **Environment Variables**:
   ```bash
   export TESTING=true
   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_test_db
   ```

### Test Execution Options

#### 1. Using the Test Runner (Recommended)
```bash
# Run all tests
python run_tests.py

# Quick tests only
python run_tests.py --quick

# Integration tests only
python run_tests.py --integration

# Specific module tests
python run_tests.py --module orders
python run_tests.py --module expenses

# With coverage report
python run_tests.py --coverage

# Performance tests
python run_tests.py --performance
```

#### 2. Using pytest directly
```bash
# All tests
pytest tests/ -v

# Integration tests only
pytest tests/test_integration.py -v

# Specific test class
pytest tests/test_integration.py::TestOrdersModule -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific markers
pytest tests/ -m "orders" -v
pytest tests/ -m "integration" -v
```

#### 3. Individual Test Classes
```bash
# Orders module tests
pytest tests/test_integration.py::TestOrdersModule -v

# Expenses module tests
pytest tests/test_integration.py::TestExpensesModule -v

# Cross-module integration
pytest tests/test_integration.py::TestCrossModuleIntegration -v
```

## Test Configuration

### Fixtures (`conftest.py`)

#### Database Fixtures
- `setup_test_database`: Creates/drops test database tables
- `db_session`: Provides isolated database session per test

#### Authentication Fixtures
- `mock_current_user`: Mock authenticated user with full permissions
- `mock_current_tenant`: Mock tenant context for multi-tenancy

#### Data Fixtures
- `sample_order_data`: Sample order for testing
- `sample_expense_data`: Sample expense data
- `sample_invoice_data`: Sample invoice data
- And more...

#### Client Fixture
- `client`: TestClient with mocked dependencies

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only authentication tests
pytest -m auth

# Run only database tests
pytest -m database

# Run only API tests
pytest -m api

# Run specific module tests
pytest -m orders
pytest -m expenses
pytest -m payments
```

## Coverage Reports

### HTML Coverage Report
After running tests with coverage:
```bash
python run_tests.py --coverage
# or
pytest --cov=. --cov-report=html
```

Open `htmlcov/index.html` in your browser to view detailed coverage.

### Coverage Targets
- **Overall Coverage**: > 80%
- **Module Coverage**: > 85%
- **Critical Paths**: > 95%

## Test Data Management

### Test Database
- Separate test database (`financial_test_db`)
- Automatic table creation/cleanup
- Transaction rollback per test for isolation

### Sample Data
- Realistic test data in fixtures
- Consistent data relationships
- Edge cases covered

### Data Cleanup
- Automatic cleanup after each test
- No test data pollution
- Fresh state for each test

## Authentication Testing

### Mock Authentication
Tests use mocked authentication with:
- Test user ID: `test-user-123`
- Test tenant ID: `test-tenant-456`
- Full permissions for all modules

### Permission Testing
- Tests verify permission requirements
- Error handling for insufficient permissions
- Multi-tenant data isolation

## Integration Scenarios

### Complete Business Flows

#### 1. Order-to-Payment Flow
```
Order Creation → Invoice Generation → Invoice Sending → Payment Processing
```

#### 2. Expense-to-Reimbursement Flow
```
Expense Creation → Approval → Voucher Creation → Payment
```

#### 3. Petty Cash Management Flow
```
Fund Creation → Transactions → Reconciliation → Replenishment
```

## Performance Benchmarks

### Response Time Targets
- Simple CRUD operations: < 100ms
- Complex operations (approval, payment): < 500ms
- Summary/reporting endpoints: < 2s
- Bulk operations: < 5s

### Load Testing
- Bulk creation: 100 records/request
- Pagination: up to 1000 records/page
- Concurrent requests: simulated load

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify database exists
psql -U postgres -l | grep financial_test_db
```

#### 2. Import Errors
```bash
# Add project root to Python path
export PYTHONPATH=$PYTHONPATH:/path/to/financial-service
```

#### 3. Permission Errors
```bash
# Ensure test user has required permissions
# Check mock_current_user fixture in conftest.py
```

#### 4. Timeout Issues
```bash
# Increase timeout for slow tests
pytest tests/ --timeout=600
```

### Debug Mode
```bash
# Run with verbose output and no capture
pytest tests/ -v -s --tb=long

# Run specific failing test
pytest tests/test_integration.py::TestClass::test_method -v -s
```

### Test Database Reset
```bash
# Drop and recreate test database
dropdb financial_test_db
createdb financial_test_db
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Financial Service Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: python run_tests.py --coverage
```

## Best Practices

### Writing Tests
1. **Isolation**: Each test should be independent
2. **Clarity**: Clear test names and documentation
3. **Coverage**: Test both success and error paths
4. **Realism**: Use realistic test data
5. **Performance**: Keep tests fast when possible

### Test Organization
1. **Modularity**: Separate concerns by module
2. **Fixtures**: Reuse common test data
3. **Markers**: Use markers for test categorization
4. **Documentation**: Comment complex test scenarios

### Maintenance
1. **Regular Updates**: Keep tests in sync with code changes
2. **Cleanup**: Remove obsolete tests
3. **Performance**: Monitor test execution times
4. **Coverage**: Maintain high coverage levels

## Contributing

### Adding New Tests
1. Follow existing test patterns
2. Use appropriate fixtures
3. Add markers for categorization
4. Update this documentation

### Test Review Checklist
- [ ] Tests are isolated and independent
- [ ] Both success and error paths are covered
- [ ] Realistic test data is used
- [ ] Appropriate assertions are made
- [ ] Tests run quickly (< 30s per test class)
- [ ] Documentation is updated

## Support

For questions or issues with tests:
1. Check this documentation
2. Review existing test patterns
3. Check test output and logs
4. Contact the development team

---

**Last Updated**: 2024-01-15
**Test Framework**: pytest 6.0+
**Coverage Tool**: pytest-cov
**Database**: PostgreSQL 13+