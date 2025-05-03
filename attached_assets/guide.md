
# Hackatime API Guide

This comprehensive guide will help you understand and utilize the Hackatime API to track and analyze coding time across your projects.

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Sending Heartbeats](#sending-heartbeats)
5. [Retrieving Statistics](#retrieving-statistics)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Code Examples](#code-examples)
9. [Implementation Tips](#implementation-tips)
10. [Troubleshooting](#troubleshooting)

## Introduction

Hackatime is a service that allows developers to track their coding time across different projects and languages. Similar to WakaTime, it provides insights into your coding habits and productivity.

## Authentication

All requests to the Hackatime API require authentication using an API key.

### Getting an API Key

1. Create an account on Hackatime
2. Navigate to your account settings
3. Generate or copy your API key

### Using the API Key

Include your API key in the Authorization header of your requests:

```
Authorization: Bearer YOUR_API_KEY
```

## API Endpoints

### Base URL

All API requests should be made to:

```
https://hackatime.hackclub.com/api/
```

### Main Endpoints

| Endpoint | Description |
|----------|-------------|
| `/v1/users/my/stats` | Get user statistics |
| `/hackatime/v1/users/current/heartbeats.bulk` | Send heartbeats (coding activity) |

## Sending Heartbeats

Heartbeats are the core mechanism of tracking coding time. A heartbeat represents a moment of coding activity.

### Heartbeat Format

Heartbeats should be sent as an array of objects with the following structure:

```json
[{
  "entity": "file_name.ext",
  "type": "file",
  "time": 1679324567,
  "category": "coding",
  "project": "project_name",
  "branch": "main",
  "language": "language_name",
  "is_write": true,
  "lines": 150,
  "lineno": 42,
  "cursorpos": 10,
  "line_additions": 2,
  "line_deletions": 1,
  "project_root_count": 1,
  "dependencies": "{dependency1,dependency2}",
  "machine": "machine_id",
  "editor": "editor_name",
  "operating_system": "os_name",
  "user_agent": "user_agent_string"
}]
```

### Required Fields

- `entity`: The file being edited
- `type`: Type of entity (usually "file")
- `time`: Unix timestamp in seconds
- `category`: Activity category (usually "coding")
- `project`: Name of the project

### Sending Frequency

It's recommended to send heartbeats:
- When a file is opened
- When changes are made to a file
- Every 2-5 minutes during active coding sessions

## Retrieving Statistics

Statistics provide insights into your coding activity.

### User Statistics

To retrieve your coding statistics:

```
GET /api/v1/users/my/stats
```

Optional query parameters:
- `start`: Start date (YYYY-MM-DD)
- `end`: End date (YYYY-MM-DD)
- `features`: Additional data to include (e.g., "projects", "languages")

### Response Format

```json
{
  "data": {
    "username": "your_username",
    "total_seconds": 12345,
    "human_readable_total": "3 hrs 25 mins",
    "daily_average": 1234,
    "human_readable_daily_average": "20 mins",
    "start": "2023-01-01T00:00:00Z",
    "end": "2023-01-31T23:59:59Z",
    "projects": [
      {
        "name": "project1",
        "total_seconds": 5000,
        "percent": 40.5
      }
    ],
    "languages": [
      {
        "name": "Python",
        "total_seconds": 3000,
        "percent": 24.3
      }
    ]
  }
}
```

## Error Handling

The Hackatime API returns standard HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized (invalid API key) |
| 404 | Not Found |
| 500 | Server Error |

### Error Response Format

```json
{
  "error": "Error message details",
  "type": "ErrorType"
}
```

## Best Practices

1. **Regular Heartbeats**: Send heartbeats at regular intervals (every 2-5 minutes)
2. **Batch Heartbeats**: Use the bulk endpoint to send multiple heartbeats at once
3. **Handle Network Issues**: Implement retry logic for failed API calls
4. **Secure API Keys**: Never expose your API key in client-side code
5. **Respect Rate Limits**: Avoid sending too many requests in a short period

## Code Examples

### Python Example (with Flask)

```python
import requests
import json
from datetime import datetime

def send_heartbeat(api_key, project_name, file_name, line_number):
    url = "https://hackatime.hackclub.com/api/hackatime/v1/users/current/heartbeats.bulk"
    
    heartbeat_data = [{
        "entity": file_name,
        "type": "file",
        "time": int(datetime.now().timestamp()),
        "category": "coding",
        "project": project_name,
        "branch": "main",
        "language": "Python",
        "is_write": True,
        "lines": 150,
        "lineno": line_number,
        "cursorpos": 0,
        "line_additions": 1,
        "line_deletions": 0,
        "project_root_count": 1,
        "dependencies": "{flask,requests}",
        "machine": "machine_id",
        "editor": "vscode",
        "operating_system": "Linux",
        "user_agent": "Mozilla/5.0"
    }]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(url, headers=headers, json=heartbeat_data)
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def get_stats(api_key):
    url = "https://hackatime.hackclub.com/api/v1/users/my/stats?features=projects,languages"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}
```

### JavaScript Example

```javascript
async function sendHeartbeat(apiKey, projectName, fileName, lineNumber) {
    const url = 'https://hackatime.hackclub.com/api/hackatime/v1/users/current/heartbeats.bulk';
    
    const heartbeatData = [{
        "entity": fileName,
        "type": "file",
        "time": Math.floor(Date.now() / 1000),
        "category": "coding",
        "project": projectName,
        "branch": "main",
        "language": "JavaScript",
        "is_write": true,
        "lines": 150,
        "lineno": lineNumber,
        "cursorpos": 0,
        "line_additions": 1,
        "line_deletions": 0,
        "project_root_count": 1,
        "dependencies": "{react,express}",
        "machine": `machine_${Math.random().toString(36).substring(2, 10)}`,
        "editor": "vscode",
        "operating_system": "MacOS",
        "user_agent": navigator.userAgent
    }];
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify(heartbeatData)
        });
        
        return response.ok ? await response.json() : { error: await response.text() };
    } catch (error) {
        return { error: error.message };
    }
}

async function getStats(apiKey) {
    const url = 'https://hackatime.hackclub.com/api/v1/users/my/stats?features=projects,languages';
    
    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        return response.ok ? await response.json() : { error: await response.text() };
    } catch (error) {
        return { error: error.message };
    }
}
```

## Implementation Tips

### 1. Editor Integration

For a full-featured implementation, consider integrating with your editor:
- Track when files are opened, edited, and closed
- Monitor cursor position and line changes
- Detect idle time to avoid overcounting

### 2. Handling Offline Mode

Store heartbeats locally when offline:
1. Save heartbeats to local storage when network is unavailable
2. Periodically attempt to sync local heartbeats when network is restored
3. Include appropriate timestamps for each heartbeat

### 3. Privacy Considerations

- Consider what data you're collecting and sharing
- Allow users to configure what data is sent (e.g., exclude certain projects or files)
- Inform users about what data is being collected

## Troubleshooting

### Common Issues

1. **Authentication Errors (401)**
   - Verify your API key is valid and correctly formatted
   - Check that you're using the "Bearer" prefix

2. **Malformed Request (400)**
   - Ensure all required fields are present in your heartbeat
   - Check that time is formatted as a Unix timestamp in seconds
   - Verify JSON format is correct

3. **Rate Limiting (429)**
   - Reduce frequency of heartbeats
   - Implement exponential backoff for retries

4. **Dependencies Format Error**
   - Ensure dependencies are formatted properly as a PostgreSQL array string: `"{dependency1,dependency2}"`

### Debugging Tips

1. Log full request and response details for debugging
2. Use network monitoring tools to analyze API requests
3. Contact Hackatime support with detailed error information

---

This guide provides a comprehensive overview of working with the Hackatime API. For more detailed information or specific use cases, refer to the official Hackatime documentation or reach out to their support team.
