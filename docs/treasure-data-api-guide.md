# Treasure Data API Guide and Response Examples

This document provides an overview of Treasure Data API endpoints, authentication methods, and example responses from various API calls using curl.

## Additional Reference Documentation

For comprehensive API documentation and tools, refer to these official resources:

### Official Documentation and Tools

- **Official API Documentation**: https://api-docs.treasuredata.com/en/overview/gettingstarted/
  - REST API overview with multiple API types (Audience API, TD API, Postback API, Real-time Personalization API)
  - Resource-based interactions over HTTP
  - Complete API reference with all endpoints

- **CLI Tool (td command)**: https://github.com/treasure-data/td
  - Command-line utility wrapping the Ruby Client Library
  - Installation: `gem install td`
  - Key commands: `td account`, `td database:create`, `td table:create`
  - Supports bulk data import and job management

- **Console Interface**: https://console.treasuredata.com/
  - Interactive web console for data management
  - Visual interface for database and query operations

### Key Resources

These resources provide detailed information about:
- Complete API reference with all endpoints
- Authentication methods and best practices
- SDKs and client libraries (Ruby, Java, Python, etc.)
- Command-line interface for TD operations
- Interactive web console for data management
- Bulk data import capabilities

## API Endpoints

### Core API Endpoints
1. **US Region (Default)**: `api.treasuredata.com`
2. **Japan Region**: `api.treasuredata.co.jp`

### Workflow API Endpoints
1. **US Region**: `api-workflow.treasuredata.com`
2. **Japan Region**: `api-workflow.treasuredata.co.jp`

## API Authentication

All API requests require authentication with a valid API key. Include it in the HTTP headers as follows:

```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/system/server_status"
```

## Core API Examples

### Server Status Check

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/system/server_status"
```

**Response:**
```json
{
  "status": "ok"
}
```

### Account Information

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/account/show"
```

**Response:**
```json
{
  "account": {
    "id": 12345,
    "plan": 3,
    "presto_plan": 6,
    "guaranteed_cores": 4,
    "maximum_cores": 16,
    "storage_size": 120000000000,
    "encrypt_start_at": "2020-01-01T00:00:00Z",
    "created_at": "2020-01-01T00:00:00Z"
  }
}
```

### Database List

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/database/list"
```

**Response:**
```json
{
  "databases": [
    {
      "name": "sample_db1",
      "created_at": "2023-01-01 00:00:00 UTC",
      "updated_at": "2023-01-01 00:00:00 UTC",
      "count": 1000,
      "organization": null,
      "permission": "administrator",
      "delete_protected": false
    },
    {
      "name": "sample_db2",
      "created_at": "2023-01-02 00:00:00 UTC",
      "updated_at": "2023-01-02 00:00:00 UTC",
      "count": 500,
      "organization": null,
      "permission": "administrator",
      "delete_protected": false
    }
  ]
}
```

### Table List for a Specific Database

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/table/list/sample_db1"
```

**Response:**
```json
{
  "database": "sample_db1",
  "tables": [
    {
      "id": 123456789,
      "name": "customer_data",
      "estimated_storage_size": 150000,
      "counter_updated_at": "2023-01-01T00:00:00Z",
      "last_log_timestamp": "2023-01-01T00:00:00Z",
      "delete_protected": false,
      "created_at": "2022-01-01 00:00:00 UTC",
      "updated_at": "2023-01-01 00:00:00 UTC",
      "type": "log",
      "include_v": true,
      "count": 750,
      "schema": "[[\"created\",\"string\"],[\"description\",\"string\"],[\"user_id\",\"string\"],[\"user_name\",\"string\"],[\"email\",\"string\"],[\"summary\",\"string\"],[\"updated\",\"string\"],[\"key\",\"string\"]]",
      "expire_days": null
    },
    {
      "id": 987654321,
      "name": "purchase_history",
      "estimated_storage_size": 250000,
      "counter_updated_at": "2023-01-01T00:00:00Z",
      "last_log_timestamp": "2023-01-01T00:00:00Z",
      "delete_protected": false,
      "created_at": "2022-01-01 00:00:00 UTC",
      "updated_at": "2023-01-01 00:00:00 UTC",
      "type": "log",
      "include_v": true,
      "count": 3500,
      "schema": "[[\"user_id\",\"long\",\"user_id\"],[\"purchase_id\",\"long\",\"purchase_id\"],[\"purchase_date\",\"string\",\"purchase_date\"],[\"purchase_amount\",\"double\",\"purchase_amount\"]]",
      "expire_days": null
    }
  ]
}
```

### Job List

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/job/list?limit=2"
```

**Response:**
```json
{
  "count": 20,
  "from": null,
  "to": null,
  "jobs": [
    {
      "job_id": "987654",
      "cpu_time": null,
      "created_at": "2023-01-01 00:00:00 UTC",
      "duration": 13,
      "end_at": "2023-01-01 00:00:13 UTC",
      "num_records": null,
      "result_size": 0,
      "start_at": "2023-01-01 00:00:00 UTC",
      "status": "success",
      "updated_at": "2023-01-01 00:00:13 UTC",
      "database": "customer_db",
      "hive_result_schema": "[[\"user_id\", \"bigint\"]]",
      "linked_result_export_job_id": null,
      "organization": null,
      "priority": 0,
      "query": "RESULT EXPORT FROM JOB 123456",
      "result": "s3://EXAMPLE-BUCKET/exported_data/user_data.tsv",
      "result_export_target_job_id": 123456,
      "retry_limit": 0,
      "type": "result_export",
      "url": "https://console.treasuredata.com/app/jobs/987654",
      "user_name": "Example User"
    },
    {
      "job_id": "123456",
      "cpu_time": 442,
      "created_at": "2023-01-01 00:00:00 UTC",
      "duration": 9,
      "end_at": "2023-01-01 00:00:09 UTC",
      "num_records": 317,
      "result_size": 838,
      "start_at": "2023-01-01 00:00:00 UTC",
      "status": "success",
      "updated_at": "2023-01-01 00:00:09 UTC",
      "database": "customer_db",
      "hive_result_schema": "[[\"user_id\", \"bigint\"]]",
      "linked_result_export_job_id": 987654,
      "organization": null,
      "priority": 0,
      "query": "SELECT a.user_id FROM customer_db.customers a WHERE (...)",
      "result": "s3://EXAMPLE-BUCKET/exported_data/user_data.tsv",
      "result_export_target_job_id": null,
      "retry_limit": 0,
      "type": "presto",
      "url": "https://console.treasuredata.com/app/jobs/123456",
      "user_name": "Example User"
    }
  ]
}
```

### Job Status

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api.treasuredata.com/v3/job/status/123456"
```

**Response:**
```json
{
  "job_id": "123456",
  "status": "success",
  "created_at": "2023-01-01 00:00:00 UTC",
  "updated_at": "2023-01-01 00:00:09 UTC",
  "start_at": "2023-01-01 00:00:00 UTC",
  "end_at": "2023-01-01 00:00:09 UTC"
}
```

### Submit Query

**Request:**
```bash
curl -s -X POST -H "Authorization: TD1 YOUR_API_KEY" \
  -d 'query=SELECT COUNT(1) FROM www_access' \
  "https://api.treasuredata.com/v3/job/issue/presto/sample_db"
```

**Response:**
```json
{
  "job_id": "123456",
  "database": "sample_db",
  "job_type": "presto",
  "status": "queued",
  "url": "https://console.treasuredata.com/app/jobs/123456"
}
```

## Workflow API Examples

### List Workflow Projects

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/projects"
```

**Response:**
```json
{
  "projects": [
    {
      "id": "123456",
      "name": "demo_content_affinity",
      "revision": "abcdef1234567890abcdef1234567890",
      "createdAt": "2022-01-01T00:00:00Z",
      "updatedAt": "2022-01-02T00:00:00Z",
      "deletedAt": null,
      "archiveType": "s3",
      "archiveMd5": "abcdefghijklmnopqrstuvwx==",
      "metadata": []
    },
    {
      "id": "789012",
      "name": "cdp_audience_123456",
      "revision": "abcdef1234567890abcdef1234567890",
      "createdAt": "2022-01-01T00:00:00Z",
      "updatedAt": "2023-01-01T00:00:00Z",
      "deletedAt": null,
      "archiveType": "s3",
      "archiveMd5": "zyxwvutsrqponmlkjihgfed==",
      "metadata": [
        {"key": "pbp", "value": "cdp_audience"},
        {"key": "pbp", "value": "cdp_audience_123456"},
        {"key": "sys", "value": "cdp_audience"}
      ]
    }
  ]
}
```

### Get Workflows in a Project

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/projects/123456/workflows"
```

**Response:**
```json
{
  "workflows": [
    {
      "id": "123456",
      "name": "create_segment_list",
      "project": {
        "id": "123456",
        "name": "workflow_examples"
      },
      "revision": "abcdef1234567890abcdef1234567890",
      "timezone": "UTC",
      "config": {
        "+get_segment_rules": {
          "docker": {
            "image": "digdag/digdag-python:3.9"
          },
          "py>": "script.audience_studio.set_rules_into_var",
          "audience_id": "${audience_id}",
          "target_segments": "${segment_id}",
          "_env": {
            "TD_APIKEY": "${secret:td.apikey}",
            "TD_ENDPOINT": "${td.cdp_endpoint}"
          }
        },
        "+loop": {
          "for_each>": {
            "rule": "${rules}"
          },
          "_do": {
            "+insert": {
              "td>": "sql/insert_segment.sql",
              "insert_into": "${td.table}"
            }
          }
        }
      }
    },
    {
      "id": "789012",
      "name": "session_time",
      "project": {
        "id": "123456",
        "name": "workflow_examples"
      },
      "revision": "abcdef1234567890abcdef1234567890",
      "timezone": "Asia/Tokyo",
      "config": {
        "+task1": {
          "echo>": "${session_local_time}"
        },
        "+task2": {
          "echo>": "${moment(session_time).format(\"YYYY-MM-DD HH:mm:ss\")}"
        }
      }
    }
  ]
}
```

### Download Project Archive

You can download a project's complete archive (including all SQL, Digdag files, and other resources) as a tar.gz file. This is useful for backing up projects, examining workflow definitions, or migrating projects between environments.

**Request:**
```bash
curl -X GET "https://api-workflow.treasuredata.com/api/projects/123456/archive" \
  -H "Authorization: TD1 YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -o project_123456.tar.gz
```

This command downloads the complete project archive as a tar.gz file. The archive contains:
- Workflow definition files (*.dig)
- SQL query files
- Python scripts
- Configuration files
- Any other resources needed for the workflows

**Note:** The downloaded archive can be extracted using standard tools:
```bash
mkdir project_dir && tar -xzf project_123456.tar.gz -C project_dir
```

## Job History and Data Retention

Treasure Data preserves job history and results for 90 days through standard console, CLI, and API methods. For data older than 90 days, Treasure Data offers a premium audit log service.

### Standard Job History
- Job history and results are accessible for 90 days
- Jobs can be retrieved using their job_id during this retention period
- Query results are available for up to 90 days after execution

### Job Access Methods
- **Console**: Navigate to the Jobs section in the TD console
- **CLI**: Use the `td job:list` command
- **API**: Use the `/v3/job/list` endpoint with optional parameters:
  - `GET /v3/job/list?from_id=:from_id&to_id=:to_id&status=:job_status`

## System-generated vs. Manual Workflows

The API responses reveal certain patterns that can help identify system-generated workflows:

### System-generated Workflows
- Contain metadata with `{"key": "sys", "value": "cdp_audience"}`
- Follow strict naming conventions (e.g., `cdp_audience_[number]`)
- Often updated in groups at the same time

### Manual Workflows
- Usually have empty metadata (`"metadata": []`)
- Have diverse naming patterns, often including personal names
- Updated independently

## Workflow Session and Attempt API Examples

### Understanding Sessions and Attempts

In Treasure Data's workflow system:
- **Session**: A planned execution of a workflow at a specific time
- **Attempt**: An actual execution instance of a session (can retry multiple times)
- **Task**: Individual steps within an attempt that perform specific operations

### List Sessions for a Workflow

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/sessions?workflow=12345678&last=5"
```

**Response:**
```json
{
  "sessions": [
    {
      "id": "123456789",
      "project": {
        "id": "123456",
        "name": "example_project"
      },
      "workflow": {
        "name": "daily_aggregation",
        "id": "12345678"
      },
      "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "sessionTime": "2025-08-03T03:00:00+00:00",
      "lastAttempt": {
        "id": "987654321",
        "retryAttemptName": null,
        "done": true,
        "success": true,
        "cancelRequested": false,
        "params": {
          "last_session_time": "2025-08-03T02:00:00+00:00",
          "next_session_time": "2025-08-03T04:00:00+00:00"
        },
        "createdAt": "2025-08-03T03:00:00Z",
        "finishedAt": "2025-08-03T03:05:30Z",
        "status": "success"
      }
    }
  ]
}
```

### Get Session Details

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/sessions/123456789"
```

**Response:**
```json
{
  "id": "123456789",
  "project": {
    "id": "123456",
    "name": "example_project"
  },
  "workflow": {
    "name": "daily_aggregation",
    "id": "12345678"
  },
  "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sessionTime": "2025-08-03T03:00:00+00:00",
  "lastAttempt": {
    "id": "987654321",
    "retryAttemptName": null,
    "done": true,
    "success": true,
    "cancelRequested": false,
    "params": {
      "last_session_time": "2025-08-03T02:00:00+00:00",
      "next_session_time": "2025-08-03T04:00:00+00:00"
    },
    "createdAt": "2025-08-03T03:00:00Z",
    "finishedAt": "2025-08-03T03:05:30Z",
    "status": "success"
  }
}
```

### List Attempts for a Session

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/sessions/123456789/attempts"
```

**Response:**
```json
{
  "attempts": [
    {
      "id": "987654321",
      "index": 1,
      "project": {
        "id": "123456",
        "name": "example_project"
      },
      "workflow": {
        "name": "daily_aggregation",
        "id": "12345678"
      },
      "sessionId": "123456789",
      "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "sessionTime": "2025-08-03T03:00:00+00:00",
      "retryAttemptName": null,
      "done": true,
      "success": true,
      "cancelRequested": false,
      "params": {
        "last_session_time": "2025-08-03T02:00:00+00:00",
        "next_session_time": "2025-08-03T04:00:00+00:00"
      },
      "createdAt": "2025-08-03T03:00:00Z",
      "finishedAt": "2025-08-03T03:05:30Z",
      "status": "success"
    }
  ]
}
```

### Get Attempt Details

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/attempts/987654321"
```

**Response:**
```json
{
  "id": "987654321",
  "index": 1,
  "project": {
    "id": "123456",
    "name": "example_project"
  },
  "workflow": {
    "name": "daily_aggregation",
    "id": "12345678"
  },
  "sessionId": "123456789",
  "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sessionTime": "2025-08-03T03:00:00+00:00",
  "retryAttemptName": null,
  "done": true,
  "success": true,
  "cancelRequested": false,
  "params": {
    "last_session_time": "2025-08-03T02:00:00+00:00",
    "next_session_time": "2025-08-03T04:00:00+00:00"
  },
  "createdAt": "2025-08-03T03:00:00Z",
  "finishedAt": "2025-08-03T03:05:30Z",
  "status": "success"
}
```

### Get Tasks for an Attempt

**Request:**
```bash
curl -s -H "Authorization: TD1 YOUR_API_KEY" "https://api-workflow.treasuredata.com/api/attempts/987654321/tasks"
```

**Response:**
```json
{
  "tasks": [
    {
      "id": "1234567890",
      "fullName": "+main_workflow",
      "parentId": null,
      "config": {},
      "upstreams": [],
      "state": "success",
      "cancelRequested": false,
      "exportParams": {},
      "storeParams": {},
      "stateParams": {},
      "updatedAt": "2025-08-03T03:05:30Z",
      "retryAt": null,
      "startedAt": "2025-08-03T03:00:00Z",
      "error": {},
      "isGroup": true
    },
    {
      "id": "1234567891",
      "fullName": "+main_workflow+extract_data",
      "parentId": "1234567890",
      "config": {
        "td>": {
          "query": "SELECT * FROM source_table WHERE dt >= '${last_session_time}'",
          "database": "analytics_db",
          "engine": "presto"
        }
      },
      "upstreams": [],
      "state": "success",
      "cancelRequested": false,
      "exportParams": {},
      "storeParams": {
        "td": {
          "last_job_id": "123456789"
        }
      },
      "stateParams": {},
      "updatedAt": "2025-08-03T03:02:15Z",
      "retryAt": null,
      "startedAt": "2025-08-03T03:00:01Z",
      "error": {},
      "isGroup": false
    },
    {
      "id": "1234567892",
      "fullName": "+main_workflow+transform_data",
      "parentId": "1234567890",
      "config": {
        "td>": {
          "query": "INSERT INTO target_table SELECT ... FROM temp_table",
          "database": "analytics_db",
          "engine": "hive"
        }
      },
      "upstreams": ["1234567891"],
      "state": "success",
      "cancelRequested": false,
      "exportParams": {},
      "storeParams": {},
      "stateParams": {},
      "updatedAt": "2025-08-03T03:05:30Z",
      "retryAt": null,
      "startedAt": "2025-08-03T03:02:16Z",
      "error": {},
      "isGroup": false
    }
  ]
}
```

### Task States

Tasks can have the following states:
- `blocked`: Waiting for upstream dependencies
- `ready`: Ready to run
- `retry_waiting`: Waiting before retry
- `running`: Currently executing
- `planned`: Planned for execution
- `success`: Completed successfully
- `failed`: Failed with error
- `canceled`: Execution was canceled
- `group_retry_waiting`: Group task waiting for retry

### Common Use Cases

1. **Monitor Workflow Execution**
   - Get session details to see overall execution status
   - List tasks to identify which steps are running or failed

2. **Debug Failed Workflows**
   - Get attempt details to see error status
   - List tasks to find exactly which task failed
   - Check task error details and logs

3. **Analyze Performance**
   - Compare startedAt and updatedAt timestamps for execution duration
   - Identify slow-running tasks as bottlenecks
   - Track retry patterns and frequencies

4. **Audit and Compliance**
   - Track all execution attempts for audit trails
   - Monitor parameter changes between executions
   - Verify scheduled executions are running as expected

## Additional API Operations

The Treasure Data API supports many more operations including:

1. **Database Operations**: Create, list, and delete databases
2. **Table Operations**: Create, list, delete, swap tables and manage schemas
3. **Import Operations**: Import data in various formats (msgpack, json, csv, etc.)
4. **Schedule Operations**: Create and manage scheduled jobs
5. **User Management**: List, create, and delete users
6. **Access Control**: Manage permissions for resources
7. **Export Operations**: Manage result URLs for exporting data
8. **Workflow Operations**: Create and manage workflows using the Workflow API
9. **Session/Attempt Operations**: Monitor and manage workflow executions

Each operation returns a structured JSON response with relevant information and status indicators.
