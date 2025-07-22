# Groq Enhancement Process Improvements

## Overview
This document describes the improvements made to the Groq enhancement process to fix duplicate processing issues and improve rate limiting.

## Key Improvements

### 1. Duplicate Processing Prevention
- **Problem**: The same discount was being processed multiple times, causing unnecessary API calls and delays
- **Solution**: Added global tracking sets (`processed_discounts`, `failed_discounts`) to track which discounts have been successfully processed or failed
- **Benefits**: 
  - Prevents duplicate API calls for the same discount
  - Saves API costs and processing time
  - Provides better progress tracking

### 2. Enhanced Rate Limiting
- **Problem**: 429 (Too Many Requests) errors were frequent due to insufficient delays
- **Solution**: Implemented configurable rate limiting with different delay strategies:
  - `REQUEST_DELAY`: 3 seconds between successful requests
  - `RETRY_DELAY`: 5 seconds between retry attempts
  - `MODEL_SWITCH_DELAY`: 10 seconds when switching models
  - `429_DELAY`: 15 seconds when hitting 429 errors
  - `MAX_CONSECUTIVE_429`: 3 consecutive 429 errors before model switch

### 3. Improved Model Switching
- **Problem**: Models were switched too frequently without proper tracking
- **Solution**: 
  - Track 429 errors per model
  - Switch models only after consecutive failures
  - Reset counters when switching to new model
  - Better logging of model switches

### 4. State Persistence
- **Problem**: Process interruption would lose progress
- **Solution**: 
  - Save tracking state to `groq_tracking_state.json` every 5 discounts
  - Load existing state when restarting
  - Resume from where it left off

### 5. Better Error Handling
- **Problem**: Process would stop on file errors
- **Solution**: 
  - Continue processing other files if one fails
  - Better error logging and recovery
  - Graceful handling of interruptions

## Configuration

### Rate Limiting Configuration
```python
RATE_LIMIT_CONFIG = {
    'REQUEST_DELAY': 3,      # Delay between successful requests (seconds)
    'RETRY_DELAY': 5,        # Delay between retry attempts (seconds)
    'MODEL_SWITCH_DELAY': 10, # Delay when switching models (seconds)
    '429_DELAY': 15,         # Delay when hitting 429 error (seconds)
    'MAX_CONSECUTIVE_429': 3, # Max consecutive 429 errors before longer delay
}
```

### Command Line Options
```bash
# Basic usage
python groq_chat.py

# With custom data directory
python groq_chat.py --data-dir /path/to/data

# Reset tracking state
python groq_chat.py --reset-tracking

# Set log level
python groq_chat.py --log-level DEBUG
```

### Environment Variables
```bash
# Required
GROQ_API_KEY=your-groq-api-key

# Optional
DISCOUNT_DATA_DIR=/path/to/data
RESET_GROQ_TRACKING=true
LOG_LEVEL=INFO
```

## Usage

### From build.sh
```bash
# Run with Groq enhancement
./build.sh 2

# Run with database update only
./build.sh 1
```

### Direct Script Execution
```bash
# From mysite directory
python groq_enhancement.py

# Or use the original script
python groq_chat.py
```

## Monitoring

### Progress Tracking
- Progress logged every 5 discounts
- Shows successful and failed counts
- Tracking state saved periodically

### Log Levels
- `INFO`: Standard progress and status messages
- `DEBUG`: Detailed processing information
- `WARNING`: Validation failures and retries
- `ERROR`: Critical failures and errors

### State Files
- `groq_tracking_state.json`: Contains processed/failed discount IDs
- `enhanced_*.json`: Output files with successfully processed discounts

## Troubleshooting

### Common Issues

1. **429 Errors Still Occurring**
   - Increase delay values in `RATE_LIMIT_CONFIG`
   - Check if multiple processes are running simultaneously

2. **Process Stuck on Same Discount**
   - Use `--reset-tracking` to clear state
   - Check logs for validation errors

3. **Memory Issues**
   - Reduce `MAX_RESULTS` in filter configuration
   - Process smaller files separately

### Recovery
- Delete `groq_tracking_state.json` to start fresh
- Use `--reset-tracking` flag
- Check logs for specific error messages

## Performance Tips

1. **Optimal Rate Limiting**: Adjust delays based on your API tier
2. **Batch Processing**: Process multiple files in sequence
3. **Monitoring**: Watch logs for 429 errors and adjust accordingly
4. **Recovery**: Use state persistence to resume interrupted processes

## Future Improvements

1. **Parallel Processing**: Process multiple discounts concurrently (with proper rate limiting)
2. **API Tier Detection**: Automatically adjust rate limits based on API tier
3. **Enhanced Validation**: More sophisticated validation rules
4. **Metrics Collection**: Track success rates and performance metrics 