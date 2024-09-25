#!/bin/bash

# URL for the GET request
URL="http://localhost:8000/rankings"

# Access token for the header
ACCESS_TOKEN="ACCESS_TOKEN"

# Log file path
LOG_FILE="path/to/file/post_request.log"

# Make the GET request and log the output
curl -L -X GET "$URL" \
     -H "access-token: $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     >> "$LOG_FILE" 2>&1
