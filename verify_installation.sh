#!/bin/bash

################################################################################
# Sahana Eden Installation Verification Script
#
# This script verifies that Sahana Eden has been installed correctly
# and all components are working properly.
#
# Usage: bash verify_installation.sh [installation_directory]
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="${1:-/opt/sahana}"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to print test results
print_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}[✓]${NC} $test_name"
        ((PASSED++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}[✗]${NC} $test_name"
        if [ -n "$message" ]; then
            echo -e "    ${RED}$message${NC}"
        fi
        ((FAILED++))
    elif [ "$result" = "WARN" ]; then
        echo -e "${YELLOW}[!]${NC} $test_name"
        if [ -n "$message" ]; then
            echo -e "    ${YELLOW}$message${NC}"
        fi
        ((WARNINGS++))
    fi
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Start verification
clear
print_header "Sahana Eden Installation Verification"
echo "Installation directory: $INSTALL_DIR"
echo ""

# Test 1: Check installation directory
print_header "Checking Installation Directory"
if [ -d "$INSTALL_DIR" ]; then
    print_test "Installation directory exists" "PASS"
else
    print_test "Installation directory exists" "FAIL" "Directory $INSTALL_DIR not found"
    exit 1
fi

# Test 2: Check web2py
if [ -d "$INSTALL_DIR/web2py" ]; then
    print_test "web2py directory exists" "PASS"
else
    print_test "web2py directory exists" "FAIL" "web2py not found"
fi

if [ -f "$INSTALL_DIR/web2py/web2py.py" ]; then
    print_test "web2py.py exists" "PASS"
else
    print_test "web2py.py exists" "FAIL"
fi

# Test 3: Check Sahana Eden
if [ -d "$INSTALL_DIR/eden" ]; then
    print_test "Sahana Eden directory exists" "PASS"
else
    print_test "Sahana Eden directory exists" "FAIL" "Eden not found"
fi

if [ -L "$INSTALL_DIR/web2py/applications/eden" ] || [ -d "$INSTALL_DIR/web2py/applications/eden" ]; then
    print_test "Eden linked to web2py applications" "PASS"
else
    print_test "Eden linked to web2py applications" "FAIL"
fi

# Test 4: Check configuration
if [ -f "$INSTALL_DIR/eden/models/000_config.py" ]; then
    print_test "Configuration file exists" "PASS"

    if grep -q "FINISHED_EDITING_CONFIG_FILE = True" "$INSTALL_DIR/eden/models/000_config.py"; then
        print_test "Configuration file is enabled" "PASS"
    else
        print_test "Configuration file is enabled" "FAIL" "FINISHED_EDITING_CONFIG_FILE not set to True"
    fi
else
    print_test "Configuration file exists" "FAIL"
fi

# Test 5: Check web2py routes
if [ -f "$INSTALL_DIR/web2py/routes.py" ]; then
    print_test "web2py routes.py exists" "PASS"
else
    print_test "web2py routes.py exists" "WARN" "Routes file not found"
fi

# Test 6: Check Python version
print_header "Checking Python Environment"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR_VERSION" -ge 3 ] && [ "$MINOR_VERSION" -ge 9 ]; then
    print_test "Python version ($PYTHON_VERSION)" "PASS"
else
    print_test "Python version ($PYTHON_VERSION)" "WARN" "Python 3.9+ recommended"
fi

# Test 7: Check Python packages
print_header "Checking Python Dependencies"

REQUIRED_PACKAGES=("lxml" "dateutil" "requests")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        print_test "Python package: $package" "PASS"
    else
        print_test "Python package: $package" "FAIL"
    fi
done

OPTIONAL_PACKAGES=("openpyxl" "geopy" "shapely" "reportlab" "xlwt" "xlrd")
for package in "${OPTIONAL_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        print_test "Optional package: $package" "PASS"
    else
        print_test "Optional package: $package" "WARN" "Recommended but not required"
    fi
done

# Test 8: Check database
print_header "Checking Database"
if [ -d "$INSTALL_DIR/eden/databases" ]; then
    print_test "Database directory exists" "PASS"

    if [ -f "$INSTALL_DIR/eden/databases/storage.db" ]; then
        print_test "SQLite database exists" "PASS"
        DB_SIZE=$(du -h "$INSTALL_DIR/eden/databases/storage.db" | cut -f1)
        echo "    Database size: $DB_SIZE"
    else
        print_test "Database initialized" "WARN" "Database files not found - may need initialization"
    fi
else
    print_test "Database directory exists" "FAIL"
fi

# Test 9: Check systemd service
print_header "Checking System Service"
if [ -f "/etc/systemd/system/sahana-eden.service" ]; then
    print_test "Systemd service file exists" "PASS"

    if systemctl is-enabled sahana-eden.service &>/dev/null; then
        print_test "Service is enabled" "PASS"
    else
        print_test "Service is enabled" "WARN" "Service not enabled for auto-start"
    fi

    if systemctl is-active sahana-eden.service &>/dev/null; then
        print_test "Service is running" "PASS"
    else
        print_test "Service is running" "WARN" "Service not currently running"
    fi
else
    print_test "Systemd service file exists" "WARN" "Service file not found"
fi

# Test 10: Check helper scripts
print_header "Checking Helper Scripts"
if [ -f "$INSTALL_DIR/start_eden.sh" ]; then
    print_test "start_eden.sh exists" "PASS"

    if [ -x "$INSTALL_DIR/start_eden.sh" ]; then
        print_test "start_eden.sh is executable" "PASS"
    else
        print_test "start_eden.sh is executable" "WARN"
    fi
else
    print_test "start_eden.sh exists" "WARN"
fi

# Test 11: Check port availability
print_header "Checking Network"
if command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":8000 "; then
        print_test "Port 8000 is in use" "PASS" "Application may be running"
    else
        print_test "Port 8000 is available" "PASS" "Ready to start server"
    fi
elif command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":8000 "; then
        print_test "Port 8000 is in use" "PASS" "Application may be running"
    else
        print_test "Port 8000 is available" "PASS" "Ready to start server"
    fi
else
    print_test "Check port availability" "WARN" "netstat/ss not found"
fi

# Test 12: Check PostgreSQL (if configured)
print_header "Checking PostgreSQL"
if command -v psql &> /dev/null; then
    print_test "PostgreSQL client installed" "PASS"

    if systemctl is-active postgresql &>/dev/null; then
        print_test "PostgreSQL service running" "PASS"
    else
        print_test "PostgreSQL service running" "WARN" "Using SQLite or PostgreSQL not running"
    fi
else
    print_test "PostgreSQL client installed" "WARN" "Likely using SQLite"
fi

# Test 13: Check disk space
print_header "Checking System Resources"
AVAILABLE_SPACE=$(df -BG "$INSTALL_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -gt 5 ]; then
    print_test "Disk space (${AVAILABLE_SPACE}GB available)" "PASS"
elif [ "$AVAILABLE_SPACE" -gt 2 ]; then
    print_test "Disk space (${AVAILABLE_SPACE}GB available)" "WARN" "Low disk space"
else
    print_test "Disk space (${AVAILABLE_SPACE}GB available)" "FAIL" "Insufficient disk space"
fi

# Test 14: Check memory
TOTAL_MEM=$(free -g | awk '/^Mem:/ {print $2}')
if [ "$TOTAL_MEM" -ge 2 ]; then
    print_test "Memory (${TOTAL_MEM}GB total)" "PASS"
else
    print_test "Memory (${TOTAL_MEM}GB total)" "WARN" "Low memory, 2GB+ recommended"
fi

# Test 15: Quick web2py test
print_header "Testing web2py Functionality"
cd "$INSTALL_DIR/web2py" 2>/dev/null
if python3 -c "import gluon" 2>/dev/null; then
    print_test "web2py modules can be imported" "PASS"
else
    print_test "web2py modules can be imported" "FAIL"
fi

# Summary
print_header "Verification Summary"
echo ""
echo -e "${GREEN}Tests Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Tests Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Installation verification completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start the server: sudo systemctl start sahana-eden"
    echo "2. Access Eden: http://localhost:8000/eden"
    echo "3. Login with: admin@example.com / testing"
    exit 0
else
    echo -e "${RED}✗ Installation verification found issues.${NC}"
    echo ""
    echo "Please review the failed tests above and:"
    echo "1. Check the installation log"
    echo "2. Verify all dependencies are installed"
    echo "3. Re-run the installation script if necessary"
    exit 1
fi
