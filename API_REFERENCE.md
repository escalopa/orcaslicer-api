# API Reference

Complete reference for the OrcaSlicer API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production deployments, consider adding API key or JWT authentication.

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

## Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "http_status": 404,
    "details": {
      "additional": "context"
    }
  }
}
```

## Endpoints

### Health Check

#### GET /health

Check service health and status.

**Response**
```json
{
  "status": "ok",
  "orca_cli_available": true,
  "orca_version": "OrcaSlicer-01.10.01.50",
  "profiles_loaded": 348,
  "uptime_seconds": 12345
}
```

---

## Models

### Upload Model

#### POST /models

Upload a 3D model file for slicing.

**Request**
- Content-Type: `multipart/form-data`
- Form field: `file` (binary)

**Supported Formats**
- `.stl` - STereoLithography
- `.step` - Standard for the Exchange of Product model data
- `.3mf` - 3D Manufacturing Format

**Example**
```bash
curl -X POST http://localhost:8000/models \
  -F "file=@model.stl"
```

**Response (201)**
```json
{
  "id": "mdl_3q9x7r",
  "filename": "model.stl",
  "format": "stl",
  "size_bytes": 1048576,
  "uploaded_at": "2025-11-23T10:00:00Z",
  "checksum_sha256": "c9c60579a2c5...",
  "storage_path": "/data/models/mdl_3q9x7r/model.stl"
}
```

### List Models

#### GET /models

List all uploaded models.

**Query Parameters**
- `limit` (integer, optional): Max results (1-100, default: 20)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response**
```json
{
  "items": [
    {
      "id": "mdl_3q9x7r",
      "filename": "model.stl",
      "format": "stl",
      "size_bytes": 1048576,
      "uploaded_at": "2025-11-23T10:00:00Z",
      "checksum_sha256": "c9c60579...",
      "storage_path": "/data/models/mdl_3q9x7r/model.stl"
    }
  ],
  "total": 1
}
```

### Get Model

#### GET /models/{model_id}

Get details of a specific model.

**Response**
```json
{
  "id": "mdl_3q9x7r",
  "filename": "model.stl",
  "format": "stl",
  "size_bytes": 1048576,
  "uploaded_at": "2025-11-23T10:00:00Z",
  "checksum_sha256": "c9c60579...",
  "storage_path": "/data/models/mdl_3q9x7r/model.stl"
}
```

---

## Profiles

Profiles define the slicing configuration: machine, process, and filament settings.

### Create Profile

#### POST /profiles

Create a new slicing profile.

**Request Body**
```json
{
  "name": "LargeRobot_PLA_0.2mm",
  "description": "Profile for large manipulator",
  "source": "user",
  "vendor": "Ginger Additive",
  "machine_id": "ginger_large_manipulator",
  "process_id": "0.20mm Quality @Ginger",
  "filament_id": "Ginger PLA White",
  "settings_overrides": {
    "layer_height": 0.2,
    "infill_density": 25,
    "support_enable": true,
    "nozzle_temperature": 205,
    "bed_temperature": 60
  }
}
```

**Fields**
- `name` (string, required): Profile name
- `description` (string, optional): Description
- `source` (string): "user" or "builtin"
- `vendor` (string, optional): Manufacturer name
- `machine_id` (string, optional): Machine preset identifier
- `process_id` (string, optional): Process preset identifier
- `filament_id` (string, optional): Filament preset identifier
- `settings_overrides` (object, optional): Setting key-value pairs

**Response (201)**
```json
{
  "id": "prof_large_robot_pla_0_2",
  "name": "LargeRobot_PLA_0.2mm",
  "description": "Profile for large manipulator",
  "source": "user",
  "vendor": "Ginger Additive",
  "machine_id": "ginger_large_manipulator",
  "process_id": "0.20mm Quality @Ginger",
  "filament_id": "Ginger PLA White",
  "settings_overrides": {
    "layer_height": 0.2,
    "infill_density": 25,
    "support_enable": true,
    "nozzle_temperature": 205,
    "bed_temperature": 60
  },
  "created_at": "2025-11-23T10:15:00Z",
  "updated_at": "2025-11-23T10:15:00Z"
}
```

### List Profiles

#### GET /profiles

List all slicing profiles.

**Query Parameters**
- `source` (string, optional): Filter by "builtin" or "user"
- `limit` (integer, optional): Max results (1-100, default: 20)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response**
```json
{
  "items": [
    {
      "id": "prof_large_robot_pla_0_2",
      "name": "LargeRobot_PLA_0.2mm",
      "source": "user",
      "vendor": "Ginger Additive",
      "machine_id": "ginger_large_manipulator",
      "created_at": "2025-11-23T10:15:00Z",
      "updated_at": "2025-11-23T10:15:00Z"
    }
  ],
  "total": 1
}
```

### Get Profile

#### GET /profiles/{profile_id}

Get details of a specific profile.

**Response**
```json
{
  "id": "prof_large_robot_pla_0_2",
  "name": "LargeRobot_PLA_0.2mm",
  "description": "Profile for large manipulator",
  "source": "user",
  "vendor": "Ginger Additive",
  "machine_id": "ginger_large_manipulator",
  "process_id": "0.20mm Quality @Ginger",
  "filament_id": "Ginger PLA White",
  "settings_overrides": {
    "layer_height": 0.2,
    "infill_density": 25,
    "support_enable": true
  },
  "created_at": "2025-11-23T10:15:00Z",
  "updated_at": "2025-11-23T10:15:00Z"
}
```

### Update Profile

#### PATCH /profiles/{profile_id}

Partially update a profile.

**Request Body**
```json
{
  "description": "Updated description",
  "settings_overrides": {
    "infill_density": 30
  }
}
```

**Response**
```json
{
  "id": "prof_large_robot_pla_0_2",
  "name": "LargeRobot_PLA_0.2mm",
  "description": "Updated description",
  "settings_overrides": {
    "layer_height": 0.2,
    "infill_density": 30,
    "support_enable": true
  },
  "updated_at": "2025-11-23T11:00:00Z"
}
```

### Delete Profile

#### DELETE /profiles/{profile_id}

Delete a profile.

**Response**
```json
{
  "id": "prof_large_robot_pla_0_2",
  "deleted": true
}
```

---

## Slice Jobs

### Create Slice Job

#### POST /slice-jobs

Create a new slicing job.

**Request Body**
```json
{
  "model_id": "mdl_3q9x7r",
  "profile_id": "prof_large_robot_pla_0_2",
  "overrides": {
    "layer_height": 0.16,
    "infill_density": 40,
    "support_enable": false
  },
  "output_options": {
    "gcode": true,
    "project_3mf": true,
    "metadata_json": true
  },
  "metadata": {
    "job_reference": "order-1234",
    "requested_by": "pricing-service"
  }
}
```

**Fields**
- `model_id` (string, required): Model to slice
- `profile_id` (string, required): Profile to use
- `overrides` (object, optional): Per-request setting overrides
- `output_options` (object, optional): Output format options
  - `gcode` (boolean): Generate G-code (default: true)
  - `project_3mf` (boolean): Generate 3MF project (default: false)
  - `metadata_json` (boolean): Generate metadata (default: true)
- `metadata` (object, optional): Custom metadata for tracking

**Response (201)**
```json
{
  "id": "job_9k2z1v",
  "model_id": "mdl_3q9x7r",
  "profile_id": "prof_large_robot_pla_0_2",
  "status": "queued",
  "queued_at": "2025-11-23T11:10:00Z",
  "overrides": {
    "layer_height": 0.16,
    "infill_density": 40,
    "support_enable": false
  },
  "output_options": {
    "gcode": true,
    "project_3mf": true,
    "metadata_json": true
  }
}
```

### Get Slice Job

#### GET /slice-jobs/{job_id}

Get the status and results of a slicing job.

**Job Statuses**
- `queued` - Waiting to be processed
- `running` - Currently slicing
- `completed` - Successfully completed
- `failed` - Failed with error

**Response (queued)**
```json
{
  "id": "job_9k2z1v",
  "model_id": "mdl_3q9x7r",
  "profile_id": "prof_large_robot_pla_0_2",
  "status": "queued",
  "queued_at": "2025-11-23T11:10:00Z"
}
```

**Response (running)**
```json
{
  "id": "job_9k2z1v",
  "status": "running",
  "queued_at": "2025-11-23T11:10:00Z",
  "started_at": "2025-11-23T11:11:05Z",
  "progress_percent": 42
}
```

**Response (completed)**
```json
{
  "id": "job_9k2z1v",
  "model_id": "mdl_3q9x7r",
  "profile_id": "prof_large_robot_pla_0_2",
  "status": "completed",
  "queued_at": "2025-11-23T11:10:00Z",
  "started_at": "2025-11-23T11:11:05Z",
  "finished_at": "2025-11-23T11:12:40Z",
  "output": {
    "gcode_url": "http://localhost:8000/slice-jobs/job_9k2z1v/gcode",
    "project_3mf_url": "http://localhost:8000/slice-jobs/job_9k2z1v/project.3mf",
    "metadata": {
      "estimated_print_time_seconds": 5400,
      "filament_used_mm": 13456.7,
      "filament_used_g": 39.2,
      "layer_count": 260,
      "bounding_box_mm": {
        "x": 120.0,
        "y": 80.0,
        "z": 35.0
      }
    }
  }
}
```

### Download G-code

#### GET /slice-jobs/{job_id}/gcode

Download the generated G-code file.

**Response**
- Content-Type: `application/octet-stream`
- Binary G-code file

**Example**
```bash
curl http://localhost:8000/slice-jobs/job_9k2z1v/gcode \
  -o output.gcode
```

### Download 3MF Project

#### GET /slice-jobs/{job_id}/project.3mf

Download the 3MF project file with applied settings.

**Response**
- Content-Type: `application/octet-stream`
- Binary 3MF file

**Example**
```bash
curl http://localhost:8000/slice-jobs/job_9k2z1v/project.3mf \
  -o project.3mf
```

---

## Common Slicing Parameters

These parameters can be used in profile `settings_overrides` or job `overrides`:

### Layer Settings
- `layer_height` (float): Layer height in mm (e.g., 0.2)
- `initial_layer_height` (float): First layer height in mm
- `layer_height_adaptive` (boolean): Enable adaptive layers

### Infill Settings
- `infill_density` (integer): Infill percentage (0-100)
- `infill_pattern` (string): Pattern type (grid, honeycomb, etc.)
- `top_layers` (integer): Number of top solid layers
- `bottom_layers` (integer): Number of bottom solid layers

### Support Settings
- `support_enable` (boolean): Enable support structures
- `support_angle` (integer): Overhang angle threshold
- `support_pattern` (string): Support pattern type

### Temperature Settings
- `nozzle_temperature` (integer): Nozzle temp in °C
- `bed_temperature` (integer): Bed temp in °C
- `chamber_temperature` (integer): Chamber temp in °C (if applicable)

### Speed Settings
- `print_speed` (integer): Default print speed in mm/s
- `first_layer_speed` (integer): First layer speed in mm/s
- `travel_speed` (integer): Travel move speed in mm/s

### Quality Settings
- `wall_count` (integer): Number of perimeter walls
- `top_bottom_thickness` (float): Combined top/bottom thickness
- `infill_overlap` (float): Infill/wall overlap percentage

**Note:** Available parameters depend on the OrcaSlicer version and profile. Consult OrcaSlicer documentation for a complete list.

---

## Rate Limiting

Currently, no rate limiting is implemented. For production:
- Consider implementing per-IP or per-API-key limits
- Limit concurrent slicing jobs
- Set maximum file upload sizes

## Webhooks (Future)

Future versions may support webhooks for job completion notifications:

```json
{
  "webhook_url": "https://your-service.com/webhook",
  "events": ["job.completed", "job.failed"]
}
```

## WebSocket Support (Future)

Real-time job progress updates via WebSocket may be added:

```
ws://localhost:8000/ws/jobs/{job_id}
```
