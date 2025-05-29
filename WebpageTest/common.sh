#!/bin/bash

# Common utility functions for IntelliShop scripts

# ===== Logging Functions =====
log() {
    local message=$1
    local level=$2
    local script_name=$3
    local log_level_name="INFO"
    
    # If level is not specified, assume level 1 (normal)
    level=${level:-1}
    script_name=${script_name:-"Script"}
    
    # Convert numeric level to name
    if [ "$level" = "0" ]; then
        log_level_name="ERROR"
    elif [ "$level" = "2" ]; then
        log_level_name="DEBUG"
    fi
    
    # Only print if current log level is >= the message's level
    if [ ${LOG_LEVEL:-1} -ge $level ]; then
        echo "$(date +%Y-%m-%d\ %H:%M:%S,%3N) - $script_name - $log_level_name - $message"
    fi
}

error() {
    local message=$1
    local script_name=${2:-"Script"}
    echo "$(date +%Y-%m-%d\ %H:%M:%S,%3N) - $script_name - ERROR - $message" >&2
    exit 1
}

# ===== Display Functions =====
show_spinner() {
    local pid=$1
    local message=$2
    local spin='-\|/'
    local i=0
    
    # Save cursor position and hide cursor
    tput sc
    tput civis
    
    echo -n "$message "
    
    # Track if we need to handle an interrupt
    local interrupted=false
    
    # Define a function to handle interrupts
    interrupt_handler() {
        interrupted=true
        # Kill the monitored process if still running
        kill -0 $pid 2>/dev/null && kill $pid 2>/dev/null
        return 1
    }
    
    # Set up temporary trap for this function
    trap interrupt_handler INT
    
    while kill -0 $pid 2>/dev/null && ! $interrupted; do
        i=$(( (i+1) % 4 ))
        printf "\r$message ${spin:$i:1}"
        sleep 0.1
    done
    
    # Restore original trap
    trap - INT
    
    # Only show completion message if not interrupted
    if ! $interrupted; then
        # Clear line, restore cursor position and show cursor
        printf "\r\033[K$message Complete!"
        echo
    else
        # Clear the spinner line
        printf "\r\033[K"
    fi
    
    tput cnorm
    
    # If interrupted, propagate the signal to parent
    if $interrupted; then
        return 1
    fi
    return 0
}

show_progress_bar() {
    local pid=$1
    local message=$2
    local width=40
    
    # Save cursor position and hide cursor
    tput sc
    tput civis
    
    echo -n "$message "
    
    # Track if we need to handle an interrupt
    local interrupted=false
    
    # Define a function to handle interrupts
    interrupt_handler() {
        interrupted=true
        # Kill the monitored process if still running
        kill -0 $pid 2>/dev/null && kill $pid 2>/dev/null
        return 1
    }
    
    # Set up temporary trap for this function
    trap interrupt_handler INT
    
    local i=0
    while kill -0 $pid 2>/dev/null && ! $interrupted; do
        i=$(( (i+1) % (width+1) ))
        # Create the progress bar
        printf "\r$message ["
        printf "%${i}s" | tr ' ' '='
        printf "%$(( width - i ))s" | tr ' ' ' '
        printf "] %d%%" $(( (i * 100) / width ))
        sleep 0.1
    done
    
    # Restore original trap
    trap - INT
    
    # Only show completed progress bar if not interrupted
    if ! $interrupted; then
        # Show completed progress bar
        printf "\r$message ["
        printf "%${width}s" | tr ' ' '='
        printf "] 100%%"
        echo
    else
        # Clear the progress bar line
        printf "\r\033[K"
    fi
    
    tput cnorm
    
    # If interrupted, propagate the signal to parent
    if $interrupted; then
        return 1
    fi
    return 0
}

# ===== Environment Functions =====
is_in_virtualenv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        return 1  # Not in a virtual environment
    else
        return 0  # In a virtual environment
    fi
}

check_port_in_use() {
    local port=$1
    
    # Try different commands based on what's available
    if command -v netstat &>/dev/null; then
        netstat -tuln | grep ":$port " > /dev/null 2>&1
        return $?
    elif command -v ss &>/dev/null; then
        ss -tuln | grep ":$port " > /dev/null 2>&1
        return $?
    elif command -v lsof &>/dev/null; then
        lsof -i :$port > /dev/null 2>&1
        return $?
    else
        # If no tool is available, we can't check - assume it's not in use
        log "Warning: Cannot check if port is in use (netstat, ss, and lsof not found)"
        return 1
    fi
}

# ===== Python Environment Functions =====
setup_virtual_environment() {
    local venv_dir=$1
    
    # If we're already in a virtual environment but not our target one, warn and deactivate
    if is_in_virtualenv && [[ "$VIRTUAL_ENV" != *"$venv_dir"* ]]; then
        log "Warning: Already in a different virtual environment. Deactivating."
        deactivate 2>/dev/null || true
    fi

    # Setup or verify virtual environment
    if [ -d "$venv_dir" ]; then
        log "Virtual environment directory exists, activating"
        source $venv_dir/bin/activate || error "Failed to activate existing virtual environment"
        
        # Double-check activation succeeded
        if ! is_in_virtualenv; then
            log "Virtual environment activation failed. Recreating environment."
            rm -rf $venv_dir
            python3 -m venv $venv_dir || error "Failed to create virtual environment"
            source $venv_dir/bin/activate || error "Failed to activate new virtual environment"
        fi
    else
        log "Creating new virtual environment"
        python3 -m venv $venv_dir || error "Failed to create virtual environment"
        source $venv_dir/bin/activate || error "Failed to activate new virtual environment"
    fi

    # Verify we're now in a virtual environment
    if ! is_in_virtualenv; then
        error "Failed to properly activate virtual environment"
    fi

    log "Successfully activated virtual environment: $VIRTUAL_ENV"
}