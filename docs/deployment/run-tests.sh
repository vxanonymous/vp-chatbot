#!/bin/bash

# Comprehensive Test Runner for Vacation Planning System
# This script runs all tests and generates coverage reports
# 
# NOTE: This script is designed for macOS systems only.
# For other operating systems, please adapt the commands accordingly.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
REPORTS_DIR="$PROJECT_ROOT/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}🧪 Starting Comprehensive Test Suite for Vacation Planning System${NC}"
echo -e "${BLUE}Reports will be saved to: $REPORTS_DIR${NC}"
echo ""

# Function to log test results
log_result() {
    local test_type="$1"
    local status="$2"
    local message="$3"
    
    case $status in
        "PASS")
            color=$GREEN
            icon="✅"
            ;;
        "FAIL")
            color=$RED
            icon="❌"
            ;;
        "SKIP")
            color=$YELLOW
            icon="⏭️"
            ;;
        "INFO")
            color=$BLUE
            icon="ℹ️"
            ;;
    esac
    
    echo -e "${color}${icon} $test_type: $message${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Backend Tests
echo -e "${BLUE}🐍 Running Backend Tests...${NC}"

if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_result "Backend" "FAIL" "Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check if pytest is installed
    if ! command_exists pytest; then
        log_result "Backend" "FAIL" "pytest not found. Please install: pip install pytest pytest-asyncio pytest-cov"
        exit 1
    fi
    
    # Run unit tests
    echo "Running unit tests..."
    if pytest tests/ -v --tb=short --cov=app --cov-report=html:"$REPORTS_DIR/backend_coverage_$TIMESTAMP" --cov-report=term-missing; then
        log_result "Backend Unit Tests" "PASS" "All unit tests passed"
    else
        log_result "Backend Unit Tests" "FAIL" "Some unit tests failed"
        BACKEND_TESTS_FAILED=true
    fi
    
    # Run API tests
    echo "Running API tests..."
    if pytest tests/test_api_comprehensive.py -v --tb=short; then
        log_result "Backend API Tests" "PASS" "All API tests passed"
    else
        log_result "Backend API Tests" "FAIL" "Some API tests failed"
        BACKEND_TESTS_FAILED=true
    fi
    
    # Run service tests
    echo "Running service tests..."
    if pytest tests/test_services_comprehensive.py -v --tb=short; then
        log_result "Backend Service Tests" "PASS" "All service tests passed"
    else
        log_result "Backend Service Tests" "FAIL" "Some service tests failed"
        BACKEND_TESTS_FAILED=true
    fi
    
    # Run integration tests
    echo "Running integration tests..."
    if pytest tests/test_integration.py -v --tb=short; then
        log_result "Backend Integration Tests" "PASS" "All integration tests passed"
    else
        log_result "Backend Integration Tests" "FAIL" "Some integration tests failed"
        BACKEND_TESTS_FAILED=true
    fi
    
    # Run security tests
    echo "Running security tests..."
    if pytest tests/test_security_audit.py -v --tb=short; then
        log_result "Backend Security Tests" "PASS" "All security tests passed"
    else
        log_result "Backend Security Tests" "FAIL" "Some security tests failed"
        BACKEND_TESTS_FAILED=true
    fi
    
    # Run performance tests
    echo "Running performance tests..."
    if pytest tests/test_performance.py -v --tb=short; then
        log_result "Backend Performance Tests" "PASS" "All performance tests passed"
    else
        log_result "Backend Performance Tests" "FAIL" "Some performance tests failed"
        BACKEND_TESTS_FAILED=true
    fi
    
    # Generate coverage report
    echo "Generating coverage report..."
    coverage_file="$REPORTS_DIR/backend_coverage_$TIMESTAMP.txt"
    pytest tests/ --cov=app --cov-report=term-missing > "$coverage_file" 2>&1 || true
    
    log_result "Backend Coverage" "INFO" "Coverage report saved to: $coverage_file"
    
else
    log_result "Backend" "SKIP" "Backend directory not found"
fi

# 2. Frontend Tests
echo -e "${BLUE}⚛️ Running Frontend Tests...${NC}"

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_result "Frontend" "FAIL" "node_modules not found. Please run: npm install"
        exit 1
    fi
    
    # Check if npm is available
    if ! command_exists npm; then
        log_result "Frontend" "FAIL" "npm not found. Please install Node.js and npm"
        exit 1
    fi
    
    # Run unit tests
    echo "Running unit tests..."
    if npm test -- --watchAll=false --coverage --coverageReporters=text --coverageReporters=html --coverageDirectory="$REPORTS_DIR/frontend_coverage_$TIMESTAMP" 2>/dev/null; then
        log_result "Frontend Unit Tests" "PASS" "All unit tests passed"
    else
        log_result "Frontend Unit Tests" "FAIL" "Some unit tests failed"
        FRONTEND_TESTS_FAILED=true
    fi
    
    # Run linting
    echo "Running linting..."
    if npm run lint 2>/dev/null; then
        log_result "Frontend Linting" "PASS" "All linting checks passed"
    else
        log_result "Frontend Linting" "FAIL" "Some linting checks failed"
        FRONTEND_TESTS_FAILED=true
    fi
    
    # Run type checking (if TypeScript)
    if [ -f "tsconfig.json" ]; then
        echo "Running type checking..."
        if npm run type-check 2>/dev/null; then
            log_result "Frontend Type Checking" "PASS" "All type checks passed"
        else
            log_result "Frontend Type Checking" "FAIL" "Some type checks failed"
            FRONTEND_TESTS_FAILED=true
        fi
    fi
    
else
    log_result "Frontend" "SKIP" "Frontend directory not found"
fi

# 3. End-to-End Tests
echo -e "${BLUE}🔗 Running End-to-End Tests...${NC}"

# Check if both backend and frontend are available
if [ -d "$BACKEND_DIR" ] && [ -d "$FRONTEND_DIR" ]; then
    echo "Starting backend server for E2E tests..."
    
    # Start backend server in background
    cd "$BACKEND_DIR"
    source venv/bin/activate
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 5
    
    # Check if backend is running
    if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        log_result "Backend Server" "PASS" "Backend server started successfully"
        
        # Run E2E tests (if they exist)
        if [ -f "$PROJECT_ROOT/tests/test_e2e.py" ]; then
            cd "$PROJECT_ROOT"
            if pytest tests/test_e2e.py -v; then
                log_result "E2E Tests" "PASS" "All E2E tests passed"
            else
                log_result "E2E Tests" "FAIL" "Some E2E tests failed"
                E2E_TESTS_FAILED=true
            fi
        else
            log_result "E2E Tests" "SKIP" "No E2E tests found"
        fi
        
        # Stop backend server
        kill $BACKEND_PID 2>/dev/null || true
    else
        log_result "Backend Server" "FAIL" "Backend server failed to start"
        kill $BACKEND_PID 2>/dev/null || true
    fi
else
    log_result "E2E Tests" "SKIP" "Both backend and frontend required for E2E tests"
fi

# 4. Security Tests
echo -e "${BLUE}🔒 Running Security Tests...${NC}"

# Run security audit script if it exists
if [ -f "$PROJECT_ROOT/scripts/security-audit.sh" ]; then
    echo "Running security audit..."
    if bash "$PROJECT_ROOT/scripts/security-audit.sh"; then
        log_result "Security Audit" "PASS" "Security audit completed"
    else
        log_result "Security Audit" "FAIL" "Security audit failed"
        SECURITY_TESTS_FAILED=true
    fi
else
    log_result "Security Audit" "SKIP" "Security audit script not found"
fi

# 5. Performance Tests
echo -e "${BLUE}⚡ Running Performance Tests...${NC}"

# Run performance tests if they exist
if [ -f "$BACKEND_DIR/tests/test_performance.py" ]; then
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    echo "Running performance tests..."
    if pytest tests/test_performance.py -v --tb=short; then
        log_result "Performance Tests" "PASS" "All performance tests passed"
    else
        log_result "Performance Tests" "FAIL" "Some performance tests failed"
        PERFORMANCE_TESTS_FAILED=true
    fi
else
    log_result "Performance Tests" "SKIP" "Performance tests not found"
fi

# 6. Code Quality Checks
echo -e "${BLUE}📊 Running Code Quality Checks...${NC}"

# Backend code quality
if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Check if black is installed
    if command_exists black; then
        echo "Running code formatting check..."
        if black --check .; then
            log_result "Backend Formatting" "PASS" "Code is properly formatted"
        else
            log_result "Backend Formatting" "FAIL" "Code formatting issues found"
            CODE_QUALITY_FAILED=true
        fi
    fi
    
    # Check if flake8 is installed
    if command_exists flake8; then
        echo "Running code linting..."
        if flake8 . --max-line-length=88 --extend-ignore=E203,W503; then
            log_result "Backend Linting" "PASS" "No linting issues found"
        else
            log_result "Backend Linting" "FAIL" "Linting issues found"
            CODE_QUALITY_FAILED=true
        fi
    fi
    
    # Check if mypy is installed
    if command_exists mypy; then
        echo "Running type checking..."
        if mypy . --ignore-missing-imports; then
            log_result "Backend Type Checking" "PASS" "No type issues found"
        else
            log_result "Backend Type Checking" "FAIL" "Type checking issues found"
            CODE_QUALITY_FAILED=true
        fi
    fi
fi

# Frontend code quality
if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    # Run prettier check
    if npm run format:check 2>/dev/null; then
        log_result "Frontend Formatting" "PASS" "Code is properly formatted"
    else
        log_result "Frontend Formatting" "FAIL" "Code formatting issues found"
        CODE_QUALITY_FAILED=true
    fi
fi

# 7. Generate Summary Report
echo -e "${BLUE}📝 Generating Test Summary Report...${NC}"

SUMMARY_FILE="$REPORTS_DIR/test_summary_$TIMESTAMP.md"

cat > "$SUMMARY_FILE" << EOF
# Test Summary Report
**Generated:** $(date)
**Project:** Vacation Planning System
**Test Run ID:** $TIMESTAMP

## Test Results Summary

### Backend Tests
- **Unit Tests:** ${BACKEND_TESTS_FAILED:-"PASS"}
- **API Tests:** ${BACKEND_TESTS_FAILED:-"PASS"}
- **Service Tests:** ${BACKEND_TESTS_FAILED:-"PASS"}
- **Integration Tests:** ${BACKEND_TESTS_FAILED:-"PASS"}
- **Security Tests:** ${BACKEND_TESTS_FAILED:-"PASS"}
- **Performance Tests:** ${BACKEND_TESTS_FAILED:-"PASS"}

### Frontend Tests
- **Unit Tests:** ${FRONTEND_TESTS_FAILED:-"PASS"}
- **Linting:** ${FRONTEND_TESTS_FAILED:-"PASS"}
- **Type Checking:** ${FRONTEND_TESTS_FAILED:-"PASS"}

### End-to-End Tests
- **E2E Tests:** ${E2E_TESTS_FAILED:-"PASS"}

### Security Tests
- **Security Audit:** ${SECURITY_TESTS_FAILED:-"PASS"}

### Performance Tests
- **Performance Tests:** ${PERFORMANCE_TESTS_FAILED:-"PASS"}

### Code Quality
- **Backend Formatting:** ${CODE_QUALITY_FAILED:-"PASS"}
- **Backend Linting:** ${CODE_QUALITY_FAILED:-"PASS"}
- **Backend Type Checking:** ${CODE_QUALITY_FAILED:-"PASS"}
- **Frontend Formatting:** ${CODE_QUALITY_FAILED:-"PASS"}

## Coverage Reports
- **Backend Coverage:** $REPORTS_DIR/backend_coverage_$TIMESTAMP/
- **Frontend Coverage:** $REPORTS_DIR/frontend_coverage_$TIMESTAMP/

## Next Steps
1. Review any failed tests
2. Address code quality issues
3. Fix security vulnerabilities
4. Improve test coverage if needed

---
*Report generated by Test Runner Script v1.0*
EOF

# 8. Final Summary
echo ""
echo -e "${BLUE}📊 Test Summary:${NC}"

if [ "$BACKEND_TESTS_FAILED" = true ] || [ "$FRONTEND_TESTS_FAILED" = true ] || [ "$E2E_TESTS_FAILED" = true ] || [ "$SECURITY_TESTS_FAILED" = true ] || [ "$PERFORMANCE_TESTS_FAILED" = true ] || [ "$CODE_QUALITY_FAILED" = true ]; then
    echo -e "${RED}❌ Some tests failed. Please review the results above.${NC}"
    echo -e "${YELLOW}📄 Detailed reports saved to: $REPORTS_DIR${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed successfully!${NC}"
    echo -e "${BLUE}📄 Reports saved to: $REPORTS_DIR${NC}"
    echo -e "${GREEN}🎉 Your application is ready for deployment!${NC}"
fi

echo ""
echo -e "${BLUE}Test execution completed at: $(date)${NC}" 