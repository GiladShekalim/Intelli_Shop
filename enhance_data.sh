#!/bin/bash

# Discount Data Enhancement Script
# This script sets up and runs the Groq API discount enhancement tool
#
# === USAGE INSTRUCTIONS ===
# How to run:
#   1. Make this script executable: chmod +x enhance_data.sh
#   2. Run the script: ./enhance_data.sh
#
# How to close:
#   - Press Ctrl+C in the terminal to stop the script
# ===========================

# Logging function with timestamp
log() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1"
}

error() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] ERROR: $1" >&2
    exit 1
}

# Loading spinner function
show_spinner() {
    local pid=$1
    local message=$2
    local spin='-\|/'
    local i=0
    
    # Save cursor position and hide cursor
    tput sc
    tput civis
    
    echo -n "$message "
    
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 4 ))
        printf "\r$message ${spin:$i:1}"
        sleep 0.1
    done
    
    # Clear line, restore cursor position and show cursor
    printf "\r\033[K$message Complete!"
    echo
    tput cnorm
}

# Progress bar function
show_progress_bar() {
    local pid=$1
    local message=$2
    local width=40
    
    # Save cursor position and hide cursor
    tput sc
    tput civis
    
    echo -n "$message "
    
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % (width+1) ))
        # Create the progress bar
        printf "\r$message ["
        printf "%${i}s" | tr ' ' '='
        printf "%$(( width - i ))s" | tr ' ' ' '
        printf "] %d%%" $(( (i * 100) / width ))
        sleep 0.1
    done
    
    # Show completed progress bar
    printf "\r$message ["
    printf "%${width}s" | tr ' ' '='
    printf "] 100%%"
    echo
    tput cnorm
}

# Global variables for cleanup
SCRIPT_PID=""
VENV_DIR="venv"
ENV_FILE=".env"
SCRIPT_FILE="groq_chat.py"
REQUIREMENTS_FILE="requirements.txt"
INPUT_FILE="hot_discounts.json"
OUTPUT_FILE="enhanced_discounts.json"

# Cleanup function
cleanup() {
    log "Initiating shutdown procedure..."
    
    # Kill script process if running
    if [ -n "$SCRIPT_PID" ]; then
        log "Stopping script process (PID: $SCRIPT_PID)"
        kill -TERM $SCRIPT_PID 2>/dev/null || true
    fi
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        log "Deactivating virtual environment"
        deactivate 2>/dev/null || true
    fi
    
    log "Cleanup complete"
}

# Check if script is running in a virtual environment
is_in_virtualenv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        return 1  # Not in a virtual environment
    else
        return 0  # In a virtual environment
    fi
}

# Verify the Groq API key
verify_api_key() {
    log "Verifying Groq API key..."
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log "❌ $ENV_FILE file not found."
        log "Creating template .env file..."
        
        # Create template .env file
        cat > "$ENV_FILE" << EOF
GROQ_API_KEY=your_api_key_here
EOF
        
        error "Please update the .env file with your actual Groq API key and run again."
    fi
    
    # Load and check API key
    source "$ENV_FILE" 2>/dev/null
    
    if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_api_key_here" ]; then
        error "Invalid or missing Groq API key in $ENV_FILE. Please update it."
    fi
    
    log "✅ Groq API key found."
}

# Verify input file exists
verify_input_file() {
    log "Checking for input data file..."
    
    if [ ! -f "$INPUT_FILE" ]; then
        error "Input file $INPUT_FILE not found. Please create this file and run again."
    fi
    
    # Check if input file is valid JSON
    if ! python3 -c "import json; json.load(open('$INPUT_FILE'))" 2>/dev/null; then
        error "Input file $INPUT_FILE is not valid JSON. Please check the file format."
    fi
    
    log "✅ Input file $INPUT_FILE is valid."
}

# Set up trap for cleanup on script exit
trap cleanup EXIT INT TERM

log "Starting Discount Data Enhancement Tool"

# Check if Python 3 is installed
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log "✅ Python 3 detected: $PYTHON_VERSION"
else
    log "❌ Python 3 not detected. Installing Python 3..."
    
    # Detect OS and install Python
    if command -v apt-get &>/dev/null; then
        log "Detected Debian/Ubuntu. Installing Python 3..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &>/dev/null; then
        log "Detected Red Hat/CentOS. Installing Python 3..."
        sudo yum install -y python3 python3-pip
    else
        error "Unsupported package manager. Please install Python 3 manually."
    fi
    
    # Verify Python was installed
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log "✅ Python 3 installed successfully: $PYTHON_VERSION"
    else
        error "Failed to install Python 3. Please install manually."
    fi
fi

# If we're already in a virtual environment but not our target one, warn and deactivate
if is_in_virtualenv && [[ "$VIRTUAL_ENV" != *"$VENV_DIR"* ]]; then
    log "Warning: Already in a different virtual environment. Deactivating."
    deactivate 2>/dev/null || true
fi

# Setup or verify virtual environment
if [ -d "$VENV_DIR" ]; then
    log "Virtual environment directory exists, activating"
    source $VENV_DIR/bin/activate || error "Failed to activate existing virtual environment"
    
    # Double-check activation succeeded
    if ! is_in_virtualenv; then
        log "Virtual environment activation failed. Recreating environment."
        rm -rf $VENV_DIR
        python3 -m venv $VENV_DIR || error "Failed to create virtual environment"
        source $VENV_DIR/bin/activate || error "Failed to activate new virtual environment"
    fi
else
    log "Creating new virtual environment"
    python3 -m venv $VENV_DIR || error "Failed to create virtual environment"
    source $VENV_DIR/bin/activate || error "Failed to activate new virtual environment"
fi

# Verify we're now in a virtual environment
if ! is_in_virtualenv; then
    error "Failed to properly activate virtual environment"
fi

log "Successfully activated virtual environment: $VIRTUAL_ENV"

# Update pip to latest version with progress bar
log "Updating pip to latest version"
python -m pip install --upgrade pip > /dev/null 2>&1 &
PIP_PID=$!
show_progress_bar $PIP_PID "Installing pip..."
if wait $PIP_PID; then
    log "✅ Pip updated successfully"
else
    log "⚠️ Warning: Failed to upgrade pip"
fi

# Install dependencies from requirements file with progress bar
if [ -f "$REQUIREMENTS_FILE" ]; then
    log "Installing dependencies from $REQUIREMENTS_FILE"
    python -m pip install -r $REQUIREMENTS_FILE > /dev/null 2>&1 &
    DEP_PID=$!
    show_progress_bar $DEP_PID "Installing dependencies..."
    if wait $DEP_PID; then
        log "✅ Dependencies installed successfully"
    else
        error "Failed to install requirements"
    fi
else
    error "Requirements file $REQUIREMENTS_FILE not found."
fi

# Verify the Groq API key
verify_api_key

# Verify input file
verify_input_file

# Check if the script file exists
if [ ! -f "$SCRIPT_FILE" ]; then
    error "Script file $SCRIPT_FILE not found."
fi

# Run a quick validation test of the script
log "Validating Python script syntax..."
if ! python -m py_compile "$SCRIPT_FILE"; then
    error "Syntax error in $SCRIPT_FILE. Please check the script."
fi
log "✅ Script validation passed."

# Run the script
log "Starting data enhancement process..."
if [ -f "$OUTPUT_FILE" ]; then
    log "Warning: Output file $OUTPUT_FILE already exists. It will be overwritten."
fi

python "$SCRIPT_FILE" &
SCRIPT_PID=$!

log "Process running with PID: $SCRIPT_PID"

# Wait for the script to complete
wait $SCRIPT_PID 2>/dev/null
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    if [ -f "$OUTPUT_FILE" ]; then
        log "✅ Enhancement process completed successfully!"
        log "Enhanced data saved to $OUTPUT_FILE"
        
        # Count items in output file
        ITEM_COUNT=$(python -c "import json; print(len(json.load(open('$OUTPUT_FILE'))))" 2>/dev/null)
        if [ -n "$ITEM_COUNT" ]; then
            log "Processed $ITEM_COUNT items."
        fi
    else
        log "⚠️ Process completed but output file $OUTPUT_FILE was not created."
    fi
else
    log "❌ Enhancement process failed with exit code $EXIT_CODE."
fi

# The cleanup function will be called automatically through the trap
log "Script execution completed."
