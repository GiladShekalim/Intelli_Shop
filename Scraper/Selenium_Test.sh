#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Set the directories for the tests
SELENIUM_TEST_DIR="$SCRIPT_DIR/pages/tests/jemix"
API_TEST_DIR="$SCRIPT_DIR/pages/tests/potter_api"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if a parameter was provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a parameter:"
    echo "  0 - Run all Selenium tests"
    echo "  1 - Run API tests"
    echo "  3 - Run only coupon data collection test (creates jemix_coupons_data.json)"
    echo "  4 - Run comprehensive coupon extraction test (creates comprehensive results JSON)"
    exit 1
fi

# Check for required browser if running Selenium tests
if [ "$1" = "0" ] || [ "$1" = "3" ] || [ "$1" = "4" ]; then
    if [ -f /etc/debian_version ]; then
        # WSL environment
        if ! command -v chromium-browser &> /dev/null && ! command -v google-chrome &> /dev/null; then
            echo "Error: Neither Chromium nor Google Chrome is installed."
            echo "Please install either browser using your system package manager:"
            echo "sudo apt update && sudo apt install -y chromium-browser"
            exit 1
        fi
    fi
fi

# Set PYTHONPATH to include the project root
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Create and activate a virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Install required packages based on test type
if [ "$1" = "0" ] || [ "$1" = "3" ] || [ "$1" = "4" ]; then
    pip install selenium webdriver-manager colorama
elif [ "$1" = "1" ]; then
    pip install requests
else
    echo "Error: Invalid parameter. Use:"
    echo "  0 - Run all Selenium tests"
    echo "  1 - Run API tests"
    echo "  3 - Run only coupon data collection test"
    echo "  4 - Run comprehensive coupon extraction test"
    exit 1
fi

# Create necessary directories and __init__.py files
mkdir -p "$PROJECT_ROOT/Scraper/pages/tests/jemix"
mkdir -p "$PROJECT_ROOT/Scraper/pages/tests/potter_api"
touch "$PROJECT_ROOT/Scraper/__init__.py"
touch "$PROJECT_ROOT/Scraper/pages/__init__.py"
touch "$PROJECT_ROOT/Scraper/pages/tests/__init__.py"
touch "$PROJECT_ROOT/Scraper/pages/tests/jemix/__init__.py"
touch "$PROJECT_ROOT/Scraper/pages/tests/potter_api/__init__.py"

# Run tests based on parameter
cd "$PROJECT_ROOT"
echo "Running tests..."

if [ "$1" = "0" ]; then
    # Run all Selenium tests
    echo "Running all Selenium tests..."
    python3 "$SELENIUM_TEST_DIR/execute_tests.py"
elif [ "$1" = "1" ]; then
    # Run API tests
    echo "Running API tests..."
    python3 "$API_TEST_DIR/execute_tests.py"
elif [ "$1" = "3" ]; then
    # Run only coupon data collection test
    echo "Running coupon data collection test..."
    python3 "$SELENIUM_TEST_DIR/test_coupon_data_collection.py"
elif [ "$1" = "4" ]; then
    # Run comprehensive coupon extraction test
    echo "Running comprehensive coupon extraction test..."
    python3 "$SELENIUM_TEST_DIR/test_comprehensive_coupon_extraction.py"
fi

# Store the test result
TEST_RESULT=$?

# Deactivate virtual environment
deactivate

# Exit with the test result
exit $TEST_RESULT
