# Treasure Data API Guide and Response Examples

This document provides an overview of Treasure Data API endpoints, authentication methods, and example responses from various API calls using curl.

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

Each operation returns a structured JSON response with relevant information and status indicators.
