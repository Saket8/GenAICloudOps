#!/bin/bash

# Comprehensive Test Running Script for GenAI CloudOps
# Runs all test types: unit, integration, e2e, performance, and accessibility

set -e

echo "🧪 GenAI CloudOps - Comprehensive Testing Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
BACKEND_UNIT_TESTS=0
BACKEND_INTEGRATION_TESTS=0
FRONTEND_UNIT_TESTS=0
FRONTEND_E2E_TESTS=0
TOTAL_FAILURES=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "error") echo -e "${RED}❌ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "info") echo -e "${BLUE}ℹ️  $message${NC}" ;;
    esac
}

# Function to run backend tests
run_backend_tests() {
    print_status "info" "Running Backend Tests..."
    cd backend
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        print_status "info" "Creating Python virtual environment..."
        python -m venv venv
        source venv/bin/activate || source venv/Scripts/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate || source venv/Scripts/activate
    fi
    
    # Run unit tests
    print_status "info" "Running backend unit tests..."
    if pytest tests/unit/ -v --cov=app --cov-report=html:coverage_html --cov-report=term-missing --cov-report=xml -m unit; then
        print_status "success" "Backend unit tests passed"
        BACKEND_UNIT_TESTS=1
    else
        print_status "error" "Backend unit tests failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
    
    # Run integration tests
    print_status "info" "Running backend integration tests..."
    if pytest tests/integration/ -v -m integration; then
        print_status "success" "Backend integration tests passed"
        BACKEND_INTEGRATION_TESTS=1
    else
        print_status "error" "Backend integration tests failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
    
    # Run OCI-specific tests
    print_status "info" "Running OCI integration tests..."
    if pytest tests/ -v -m oci; then
        print_status "success" "OCI integration tests passed"
    else
        print_status "warning" "OCI integration tests failed (might need OCI credentials)"
    fi
    
    # Run vault tests
    print_status "info" "Running vault tests..."
    if pytest tests/ -v -m vault; then
        print_status "success" "Vault tests passed"
    else
        print_status "warning" "Vault tests failed (might need vault setup)"
    fi
    
    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "info" "Running Frontend Tests..."
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "info" "Installing npm dependencies..."
        npm install
    fi
    
    # Run unit tests
    print_status "info" "Running frontend unit tests..."
    if npm run test:unit; then
        print_status "success" "Frontend unit tests passed"
        FRONTEND_UNIT_TESTS=1
    else
        print_status "error" "Frontend unit tests failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
    
    # Run integration tests
    print_status "info" "Running frontend integration tests..."
    if npm run test:integration; then
        print_status "success" "Frontend integration tests passed"
    else
        print_status "warning" "Frontend integration tests failed"
    fi
    
    # Generate coverage report
    print_status "info" "Generating test coverage report..."
    npm run test:coverage
    
    cd ..
}

# Function to run E2E tests
run_e2e_tests() {
    print_status "info" "Running End-to-End Tests..."
    cd frontend
    
    # Check if Playwright is installed
    if ! command -v playwright &> /dev/null; then
        print_status "info" "Installing Playwright..."
        npx playwright install
    fi
    
    # Start backend server in background
    print_status "info" "Starting backend server for E2E tests..."
    cd ../backend
    source venv/bin/activate || source venv/Scripts/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 10
    
    cd ../frontend
    
    # Run E2E tests
    print_status "info" "Running Playwright E2E tests..."
    if npm run test:e2e; then
        print_status "success" "E2E tests passed"
        FRONTEND_E2E_TESTS=1
    else
        print_status "error" "E2E tests failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
    
    # Stop backend server
    kill $BACKEND_PID 2>/dev/null || true
    
    cd ..
}

# Function to run accessibility tests
run_accessibility_tests() {
    print_status "info" "Running Accessibility Tests..."
    cd frontend
    
    if npm run test:accessibility; then
        print_status "success" "Accessibility tests passed"
    else
        print_status "warning" "Accessibility tests failed"
    fi
    
    cd ..
}

# Function to run performance tests
run_performance_tests() {
    print_status "info" "Running Performance Tests..."
    cd backend
    
    source venv/bin/activate || source venv/Scripts/activate
    
    # Run performance tests
    if pytest tests/ -v -m slow; then
        print_status "success" "Performance tests passed"
    else
        print_status "warning" "Performance tests failed"
    fi
    
    cd ..
}

# Function to generate test report
generate_test_report() {
    print_status "info" "Generating comprehensive test report..."
    
    cat > test-report.md << EOF
# GenAI CloudOps - Test Report

Generated: $(date)

## Test Results Summary

| Test Type | Status | Details |
|-----------|--------|---------|
| Backend Unit Tests | $([ $BACKEND_UNIT_TESTS -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") | pytest unit tests with coverage |
| Backend Integration Tests | $([ $BACKEND_INTEGRATION_TESTS -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") | API endpoint integration tests |
| Frontend Unit Tests | $([ $FRONTEND_UNIT_TESTS -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") | Jest + React Testing Library |
| Frontend E2E Tests | $([ $FRONTEND_E2E_TESTS -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") | Playwright end-to-end tests |

## Coverage Reports

- Backend Coverage: \`backend/coverage_html/index.html\`
- Frontend Coverage: \`frontend/coverage/index.html\`

## Test Artifacts

- Backend Test Results: \`backend/test-results/\`
- Frontend Test Results: \`frontend/test-results/\`
- E2E Test Results: \`frontend/test-results/e2e-results.html\`

## Failed Tests

$([ $TOTAL_FAILURES -eq 0 ] && echo "No test failures! 🎉" || echo "$TOTAL_FAILURES test suite(s) failed")

## Next Steps

$([ $TOTAL_FAILURES -eq 0 ] && echo "All tests passed! Ready for deployment." || echo "Please review and fix failing tests before deployment.")
EOF

    print_status "success" "Test report generated: test-report.md"
}

# Main execution
main() {
    # Parse command line arguments
    SKIP_BACKEND=false
    SKIP_FRONTEND=false
    SKIP_E2E=false
    SKIP_ACCESSIBILITY=false
    SKIP_PERFORMANCE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backend) SKIP_BACKEND=true; shift ;;
            --skip-frontend) SKIP_FRONTEND=true; shift ;;
            --skip-e2e) SKIP_E2E=true; shift ;;
            --skip-accessibility) SKIP_ACCESSIBILITY=true; shift ;;
            --skip-performance) SKIP_PERFORMANCE=true; shift ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-backend        Skip backend tests"
                echo "  --skip-frontend       Skip frontend tests"
                echo "  --skip-e2e           Skip end-to-end tests"
                echo "  --skip-accessibility Skip accessibility tests"
                echo "  --skip-performance   Skip performance tests"
                echo "  --help               Show this help message"
                exit 0
                ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done
    
    # Run test suites
    if [ "$SKIP_BACKEND" = false ]; then
        run_backend_tests
    fi
    
    if [ "$SKIP_FRONTEND" = false ]; then
        run_frontend_tests
    fi
    
    if [ "$SKIP_E2E" = false ]; then
        run_e2e_tests
    fi
    
    if [ "$SKIP_ACCESSIBILITY" = false ]; then
        run_accessibility_tests
    fi
    
    if [ "$SKIP_PERFORMANCE" = false ]; then
        run_performance_tests
    fi
    
    # Generate final report
    generate_test_report
    
    # Exit with appropriate code
    if [ $TOTAL_FAILURES -eq 0 ]; then
        print_status "success" "All tests completed successfully! 🎉"
        exit 0
    else
        print_status "error" "$TOTAL_FAILURES test suite(s) failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 