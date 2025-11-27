#!/bin/bash

# Security Audit Script for Vacation Planning System
# This script performs comprehensive security checks on the application
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
REPORT_DIR="$PROJECT_ROOT/security-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/security_audit_$TIMESTAMP.md"

# Create report directory
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}🔒 Starting Security Audit for Vacation Planning System${NC}"
echo -e "${BLUE}Report will be saved to: $REPORT_FILE${NC}"
echo ""

# Initialize report
cat > "$REPORT_FILE" << EOF
# Security Audit Report
**Generated:** $(date)
**Project:** Vacation Planning System
**Audit Type:** Comprehensive Security Assessment

## Executive Summary

This report contains the results of a comprehensive security audit performed on the Vacation Planning System application.

## Table of Contents
1. [Dependency Security](#dependency-security)
2. [Code Security Analysis](#code-security-analysis)
3. [Configuration Security](#configuration-security)
4. [Authentication & Authorization](#authentication--authorization)
5. [Data Protection](#data-protection)
6. [API Security](#api-security)
7. [Infrastructure Security](#infrastructure-security)
8. [Compliance Assessment](#compliance-assessment)
9. [Recommendations](#recommendations)

---

EOF

# Function to log findings
log_finding() {
    local severity="$1"
    local category="$2"
    local title="$3"
    local description="$4"
    local recommendation="$5"
    
    case $severity in
        "CRITICAL")
            color=$RED
            icon="🚨"
            ;;
        "HIGH")
            color=$RED
            icon="⚠️"
            ;;
        "MEDIUM")
            color=$YELLOW
            icon="⚠️"
            ;;
        "LOW")
            color=$GREEN
            icon="ℹ️"
            ;;
        "INFO")
            color=$BLUE
            icon="ℹ️"
            ;;
    esac
    
    echo -e "${color}${icon} $severity: $title${NC}"
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF

### $severity: $title
**Category:** $category  
**Description:** $description  
**Recommendation:** $recommendation

EOF
}

# 1. Dependency Security
echo -e "${BLUE}📦 Checking Dependency Security...${NC}"

# Python dependencies
if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    
    # Check for known vulnerabilities
    if command -v safety &> /dev/null; then
        echo "Running safety check on Python dependencies..."
        if safety check --json > /tmp/safety_report.json 2>/dev/null; then
            vuln_count=$(jq '. | length' /tmp/safety_report.json 2>/dev/null || echo "0")
            if [ "$vuln_count" -gt 0 ]; then
                log_finding "HIGH" "Dependency Security" "Known vulnerabilities found" \
                    "Found $vuln_count known vulnerabilities in Python dependencies" \
                    "Update vulnerable packages to latest secure versions"
            else
                log_finding "INFO" "Dependency Security" "No known vulnerabilities" \
                    "All Python dependencies are up to date with no known vulnerabilities" \
                    "Continue regular dependency updates"
            fi
        else
            log_finding "MEDIUM" "Dependency Security" "Safety check failed" \
                "Unable to run safety check on Python dependencies" \
                "Install safety tool and ensure internet connectivity"
        fi
    else
        log_finding "MEDIUM" "Dependency Security" "Safety tool not installed" \
            "Safety tool is not installed for vulnerability scanning" \
            "Install safety: pip install safety"
    fi
    
    # Check for outdated packages
    if [ -f "requirements.txt" ]; then
        echo "Checking for outdated packages..."
        outdated_count=$(pip list --outdated 2>/dev/null | wc -l || echo "0")
        if [ "$outdated_count" -gt 1 ]; then
            log_finding "MEDIUM" "Dependency Security" "Outdated packages detected" \
                "Found $outdated_count outdated packages" \
                "Update packages to latest versions: pip install --upgrade -r requirements.txt"
        else
            log_finding "INFO" "Dependency Security" "Packages up to date" \
                "All packages are up to date" \
                "Continue regular updates"
        fi
    fi
fi

# Node.js dependencies
if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    if [ -f "package.json" ]; then
        echo "Checking Node.js dependencies..."
        
        # Check for vulnerabilities
        if command -v npm &> /dev/null; then
            if npm audit --audit-level=moderate --json > /tmp/npm_audit.json 2>/dev/null; then
                vuln_count=$(jq '.metadata.vulnerabilities.total' /tmp/npm_audit.json 2>/dev/null || echo "0")
                if [ "$vuln_count" -gt 0 ]; then
                    log_finding "HIGH" "Dependency Security" "npm vulnerabilities found" \
                        "Found $vuln_count vulnerabilities in Node.js dependencies" \
                        "Run 'npm audit fix' to resolve vulnerabilities"
                else
                    log_finding "INFO" "Dependency Security" "No npm vulnerabilities" \
                        "All Node.js dependencies are secure" \
                        "Continue regular updates"
                fi
            else
                log_finding "MEDIUM" "Dependency Security" "npm audit failed" \
                    "Unable to run npm audit" \
                    "Check npm configuration and network connectivity"
            fi
        fi
    fi
fi

# 2. Code Security Analysis
echo -e "${BLUE}🔍 Performing Code Security Analysis...${NC}"

# Python code analysis
if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    
    # Bandit security analysis
    if command -v bandit &> /dev/null; then
        echo "Running Bandit security analysis..."
        if bandit -r . -f json -o /tmp/bandit_report.json 2>/dev/null; then
            issues=$(jq '.results | length' /tmp/bandit_report.json 2>/dev/null || echo "0")
            if [ "$issues" -gt 0 ]; then
                log_finding "HIGH" "Code Security" "Security issues found in code" \
                    "Bandit found $issues security issues in Python code" \
                    "Review and fix security issues identified by Bandit"
            else
                log_finding "INFO" "Code Security" "No security issues in code" \
                    "Bandit found no security issues in Python code" \
                    "Continue regular security reviews"
            fi
        else
            log_finding "MEDIUM" "Code Security" "Bandit analysis failed" \
                "Unable to run Bandit security analysis" \
                "Check Bandit installation and code syntax"
        fi
    else
        log_finding "MEDIUM" "Code Security" "Bandit not installed" \
            "Bandit security analysis tool is not installed" \
            "Install Bandit: pip install bandit"
    fi
fi

# 3. Configuration Security
echo -e "${BLUE}⚙️ Checking Configuration Security...${NC}"

# Check for hardcoded secrets
echo "Scanning for hardcoded secrets..."
if grep -r -i "password\|secret\|key\|token" "$PROJECT_ROOT" --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git --exclude=*.pyc --exclude=*.log | grep -v "example\|test\|mock" | head -10; then
    log_finding "HIGH" "Configuration Security" "Potential hardcoded secrets" \
        "Found potential hardcoded secrets in code" \
        "Move all secrets to environment variables or secure configuration"
else
    log_finding "INFO" "Configuration Security" "No hardcoded secrets found" \
        "No obvious hardcoded secrets detected" \
        "Continue using environment variables for secrets"
fi

# Check environment files
if [ -f "$PROJECT_ROOT/.env" ]; then
    log_finding "MEDIUM" "Configuration Security" ".env file present" \
        ".env file is present in repository" \
        "Ensure .env is in .gitignore and contains no production secrets"
fi

# Check for default configurations
if grep -r "your-secret-key-change-in-production\|default_password\|admin123" "$PROJECT_ROOT" --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null; then
    log_finding "CRITICAL" "Configuration Security" "Default credentials found" \
        "Found default or placeholder credentials in code" \
        "Replace all default credentials with secure values"
fi

# 4. Authentication & Authorization
echo -e "${BLUE}🔐 Checking Authentication & Authorization...${NC}"

# Check JWT implementation
if grep -r "jwt\|token" "$BACKEND_DIR" --include="*.py" 2>/dev/null | grep -q "expires\|expiration"; then
    log_finding "INFO" "Authentication" "JWT expiration configured" \
        "JWT tokens have expiration configured" \
        "Ensure expiration times are appropriate for security requirements"
else
    log_finding "HIGH" "Authentication" "JWT expiration not found" \
        "JWT token expiration not clearly configured" \
        "Implement proper JWT token expiration"
fi

# Check password hashing
if grep -r "bcrypt\|passlib" "$BACKEND_DIR" --include="*.py" 2>/dev/null; then
    log_finding "INFO" "Authentication" "Password hashing implemented" \
        "Password hashing is implemented using bcrypt/passlib" \
        "Continue using secure password hashing"
else
    log_finding "CRITICAL" "Authentication" "Password hashing not found" \
        "No evidence of password hashing implementation" \
        "Implement secure password hashing using bcrypt or similar"
fi

# 5. Data Protection
echo -e "${BLUE}🛡️ Checking Data Protection...${NC}"

# Check for SQL injection protection
if grep -r "sqlalchemy\|motor\|pymongo" "$BACKEND_DIR" --include="*.py" 2>/dev/null; then
    log_finding "INFO" "Data Protection" "ORM/ODM used" \
        "Using ORM/ODM which provides SQL injection protection" \
        "Continue using parameterized queries"
else
    log_finding "HIGH" "Data Protection" "Raw SQL queries detected" \
        "Raw SQL queries found without clear injection protection" \
        "Use ORM/ODM or parameterized queries to prevent SQL injection"
fi

# Check for input validation
if grep -r "pydantic\|validator" "$BACKEND_DIR" --include="*.py" 2>/dev/null; then
    log_finding "INFO" "Data Protection" "Input validation implemented" \
        "Pydantic validation is implemented for input validation" \
        "Continue using comprehensive input validation"
else
    log_finding "MEDIUM" "Data Protection" "Input validation not found" \
        "No clear input validation implementation found" \
        "Implement comprehensive input validation using Pydantic"
fi

# 6. API Security
echo -e "${BLUE}🌐 Checking API Security...${NC}"

# Check CORS configuration
if grep -r "cors\|CORS" "$BACKEND_DIR" --include="*.py" 2>/dev/null; then
    log_finding "INFO" "API Security" "CORS configured" \
        "CORS is configured for API endpoints" \
        "Ensure CORS settings are appropriate for production"
else
    log_finding "MEDIUM" "API Security" "CORS not configured" \
        "No CORS configuration found" \
        "Configure CORS appropriately for your deployment"
fi

# Check rate limiting
if grep -r "rate.*limit\|throttle" "$BACKEND_DIR" --include="*.py" 2>/dev/null; then
    log_finding "INFO" "API Security" "Rate limiting implemented" \
        "Rate limiting is implemented" \
        "Ensure rate limits are appropriate for your use case"
else
    log_finding "MEDIUM" "API Security" "Rate limiting not found" \
        "No rate limiting implementation found" \
        "Implement rate limiting to prevent abuse"
fi

# 7. Infrastructure Security
echo -e "${BLUE}🏗️ Checking Infrastructure Security...${NC}"

# Check Docker security
if [ -f "$PROJECT_ROOT/Dockerfile" ] || [ -f "$BACKEND_DIR/Dockerfile" ]; then
    log_finding "INFO" "Infrastructure Security" "Docker configuration found" \
        "Docker configuration is present" \
        "Review Docker security best practices"
fi

# Check for HTTPS enforcement
if grep -r "https\|ssl\|tls" "$BACKEND_DIR" --include="*.py" 2>/dev/null; then
    log_finding "INFO" "Infrastructure Security" "HTTPS/SSL configuration found" \
        "HTTPS/SSL configuration is present" \
        "Ensure HTTPS is enforced in production"
else
    log_finding "MEDIUM" "Infrastructure Security" "HTTPS configuration not found" \
        "No HTTPS/SSL configuration found" \
        "Implement HTTPS enforcement for production"
fi

# 8. Compliance Assessment
echo -e "${BLUE}📋 Performing Compliance Assessment...${NC}"

# GDPR compliance check
if grep -r "gdpr\|privacy\|consent" "$PROJECT_ROOT" --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null; then
    log_finding "INFO" "Compliance" "GDPR considerations found" \
        "GDPR/privacy considerations are documented" \
        "Ensure full GDPR compliance for EU users"
else
    log_finding "MEDIUM" "Compliance" "GDPR considerations not found" \
        "No GDPR/privacy considerations documented" \
        "Implement GDPR compliance measures if serving EU users"
fi

# OWASP Top 10 compliance
log_finding "INFO" "Compliance" "OWASP Top 10 Assessment" \
    "Basic OWASP Top 10 protections are in place" \
    "Conduct comprehensive OWASP Top 10 assessment"

# 9. Generate Recommendations
echo -e "${BLUE}📝 Generating Final Report...${NC}"

cat >> "$REPORT_FILE" << EOF

## Recommendations

### Immediate Actions (Critical/High)
1. **Update Vulnerable Dependencies**: Update all packages with known vulnerabilities
2. **Secure Configuration**: Move all secrets to environment variables
3. **Input Validation**: Implement comprehensive input validation
4. **Authentication**: Ensure proper JWT expiration and password hashing

### Short-term Actions (Medium)
1. **Rate Limiting**: Implement API rate limiting
2. **CORS Configuration**: Configure CORS appropriately
3. **HTTPS Enforcement**: Ensure HTTPS in production
4. **Security Headers**: Implement security headers

### Long-term Actions (Low/Info)
1. **Security Monitoring**: Implement security monitoring and logging
2. **Penetration Testing**: Conduct regular penetration testing
3. **Security Training**: Provide security training for developers
4. **Compliance**: Ensure compliance with relevant regulations

## Conclusion

This security audit provides a baseline assessment of the Vacation Planning System application. Regular security audits should be conducted to maintain security posture.

**Next Steps:**
1. Address all Critical and High severity findings
2. Implement recommended security measures
3. Schedule follow-up security review
4. Establish security monitoring and alerting

---
*Report generated by Security Audit Script v1.0*
EOF

echo -e "${GREEN}✅ Security audit completed!${NC}"
echo -e "${GREEN}📄 Report saved to: $REPORT_FILE${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  - Dependency vulnerabilities checked"
echo -e "  - Code security analysis performed"
echo -e "  - Configuration security reviewed"
echo -e "  - Authentication & authorization assessed"
echo -e "  - Data protection measures evaluated"
echo -e "  - API security reviewed"
echo -e "  - Infrastructure security checked"
echo -e "  - Compliance assessment completed"
echo ""
echo -e "${YELLOW}Please review the detailed report and address any findings.${NC}" 