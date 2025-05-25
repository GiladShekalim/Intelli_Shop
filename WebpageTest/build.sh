#!/bin/bash

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_SH="$SCRIPT_DIR/common.sh"

if [ -f "$COMMON_SH" ]; then
    source "$COMMON_SH"
else
    echo "$(date +%Y-%m-%d\ %H:%M:%S,%3N) - Build - ERROR - Common utilities file not found: $COMMON_SH" >&2
    exit 1
fi

# Script variables
VENV_DIR="venv"
PROJECT_DIR="mysite"
ENV_FILE=".env"
SCRIPT_NAME="Build"
LOG_LEVEL=${LOG_LEVEL:-1}  # Default to INFO level (1)

# ===== Helper Functions =====

cleanup() {
    log "Cleaning up resources" 1 "$SCRIPT_NAME"
    
    # Kill any remaining background processes
    for job in $(jobs -p); do
        log "Killing background process $job" 2 "$SCRIPT_NAME"
        kill $job 2>/dev/null || true
    done
    
    # If we're in a virtual environment, deactivate it
    if is_in_virtualenv; then
        deactivate 2>/dev/null || true
        log "Deactivated virtual environment" 1 "$SCRIPT_NAME"
    fi
}

# ===== MongoDB Configuration =====

setup_mongodb_config() {
    log "Setting up MongoDB configuration" 1 "$SCRIPT_NAME"
    
    # Create .env file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log "Creating new environment file $ENV_FILE" 1 "$SCRIPT_NAME"
        cat > "$ENV_FILE" << EOF
# MongoDB Connection Settings
MONGODB_URI=mongodb+srv://giladshkalim:Gilad1212@intellidb.yuauj7i.mongodb.net/IntelliDB?retryWrites=true&w=majority
MONGODB_NAME=IntelliDB

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
        log "Created environment file with MongoDB settings" 1 "$SCRIPT_NAME"
    else
        log "Environment file $ENV_FILE already exists" 1 "$SCRIPT_NAME"
    fi
    
    # Load environment variables
    log "Loading configuration from $ENV_FILE" 1 "$SCRIPT_NAME"
    if [ -f "$ENV_FILE" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ $line =~ ^[A-Za-z0-9_]+=.* ]]; then
                export "$line"
            fi
        done < "$ENV_FILE"
    fi
}

test_mongodb_connection() {
    log "Testing MongoDB connection..." 1 "$SCRIPT_NAME"
    python manage.py test_mongodb
}

# Function to run database update
run_database_update() {
    log "Running database update script..." 1 "$SCRIPT_NAME"
    
    # Use relative paths based on script location
    local base_dir="$SCRIPT_DIR"
    local script_path="$base_dir/$PROJECT_DIR/update_database.py"
    
    if [[ -f "$script_path" ]]; then
        log "Found update_database.py at $script_path" 1 "$SCRIPT_NAME"
        # Set PYTHONPATH to include the project directory for imports
        PYTHONPATH="$base_dir/$PROJECT_DIR" python "$script_path"
        return $?
    else
        log "update_database.py not found at $script_path" 0 "$SCRIPT_NAME"
        return 1
    fi
}

# Set up trap for cleanup on script exit
trap cleanup EXIT

# ===== Main Script =====

log "Starting IntelliShop setup" 1 "$SCRIPT_NAME"

# Setup virtual environment using function from common.sh
setup_virtual_environment "$VENV_DIR"

log "Successfully activated virtual environment: $VIRTUAL_ENV" 1 "$SCRIPT_NAME"

# Update pip to latest version
log "Updating pip to latest version" 1 "$SCRIPT_NAME"
python -m pip install --upgrade pip

# Install dependencies from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    log "Installing dependencies from requirements.txt" 1 "$SCRIPT_NAME"
    python -m pip install -r requirements.txt
else
    # Install Django and MongoDB dependencies
    log "Installing Django and MongoDB dependencies" 1 "$SCRIPT_NAME"
    python -m pip install django pymongo[srv] dnspython
fi

# Set up MongoDB configuration
setup_mongodb_config

# Change to the Django project directory
if [ ! -d "$PROJECT_DIR" ]; then
    error "Django project directory '$PROJECT_DIR' not found" "$SCRIPT_NAME"
fi

cd $PROJECT_DIR || error "Failed to change to project directory" "$SCRIPT_NAME"

# Test MongoDB connection
test_mongodb_connection || log "Warning: MongoDB connection test failed. Please check your MongoDB configuration." 0 "$SCRIPT_NAME"

# Run database migrations
log "Running database migrations" 1 "$SCRIPT_NAME"
python manage.py makemigrations
python manage.py migrate

# Run database update if parameter is 1
if [ "$1" = "1" ]; then
    log "Running database update as requested" 1 "$SCRIPT_NAME"
    run_database_update
    if [ $? -ne 0 ]; then
        log "Database update failed" 0 "$SCRIPT_NAME"
        exit 1
    fi
    log "Database update completed successfully" 1 "$SCRIPT_NAME"
fi

# Collect static files
log "Collecting static files" 1 "$SCRIPT_NAME"
python manage.py collectstatic --noinput

# Check for Django configuration errors
log "Checking for configuration errors" 1 "$SCRIPT_NAME"
python manage.py check

# Start Django development server
log "Starting Django development server" 1 "$SCRIPT_NAME"
python manage.py runserver 0.0.0.0:8000
