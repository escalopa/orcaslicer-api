# Quick Start Guide

Get OrcaSlicer API up and running in 5 minutes.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Method 1: Automated Script

```bash
./quickstart.sh
```

This will:
1. Check dependencies
2. Build the Docker image
3. Start the service
4. Verify it's running
5. Show access points

## Method 2: Manual Steps

### Step 1: Build

```bash
docker build -t orcaslicer-api:latest .
```

### Step 2: Run

```bash
docker-compose up -d
```

### Step 3: Verify

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "orca_cli_available": true,
  "profiles_loaded": 0,
  "uptime_seconds": 5
}
```

## Access the API

### Interactive Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Command Line

```bash
# Health check
curl http://localhost:8000/health

# List profiles
curl http://localhost:8000/profiles

# Upload a model (requires a model file)
curl -X POST http://localhost:8000/models \
  -F "file=@example.stl"
```

## First API Call

### 1. Create a Profile

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Profile",
    "description": "My first profile",
    "source": "user",
    "vendor": "Test",
    "machine_id": "test_machine",
    "process_id": "test_process",
    "filament_id": "test_filament",
    "settings_overrides": {
      "layer_height": 0.2,
      "infill_density": 20
    }
  }'
```

### 2. Upload a Model

```bash
curl -X POST http://localhost:8000/models \
  -F "file=@your_model.stl"
```

### 3. Create a Slice Job

```bash
curl -X POST http://localhost:8000/slice-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "mdl_xxxxx",
    "profile_id": "prof_xxxxx",
    "overrides": {
      "infill_density": 30
    },
    "output_options": {
      "gcode": true,
      "project_3mf": true,
      "metadata_json": true
    }
  }'
```

### 4. Check Job Status

```bash
curl http://localhost:8000/slice-jobs/job_xxxxx
```

### 5. Download G-code

```bash
curl http://localhost:8000/slice-jobs/job_xxxxx/gcode \
  -o output.gcode
```

## Using the Python Client

### Install Dependencies

```bash
pip install httpx
```

### Run Example Script

```bash
python example_usage.py
```

Note: You'll need to provide a model file (example.stl) or update the script with your file path.

### Custom Script

```python
from src.clients.python_client import OrcaSlicerClient

# Initialize client
client = OrcaSlicerClient(base_url="http://localhost:8000")

# Upload model
model = client.upload_model("path/to/model.stl")
print(f"Model ID: {model['id']}")

# Create profile
profile = client.create_profile({
    "name": "My Profile",
    "vendor": "Test",
    "machine_id": "test_machine",
    "process_id": "test_process",
    "filament_id": "test_filament",
    "settings_overrides": {"layer_height": 0.2}
})
print(f"Profile ID: {profile['id']}")

# Create slice job
job = client.create_slice_job(
    model_id=model["id"],
    profile_id=profile["id"],
    overrides={"infill_density": 30},
    output_options={
        "gcode": True,
        "metadata_json": True
    }
)
print(f"Job ID: {job['id']}")

# Wait for completion
import time
while True:
    job = client.get_slice_job(job["id"])
    if job["status"] in ["completed", "failed"]:
        break
    print(f"Status: {job['status']}")
    time.sleep(2)

# Download if successful
if job["status"] == "completed":
    client.download_gcode(job["id"], "output.gcode")
    print("✓ G-code downloaded")
```

## Common Commands

### View Logs

```bash
docker-compose logs -f
```

### Stop Service

```bash
docker-compose down
```

### Restart Service

```bash
docker-compose restart
```

### Rebuild After Changes

```bash
docker-compose down
docker build -t orcaslicer-api:latest .
docker-compose up -d
```

### Clean Everything

```bash
docker-compose down -v  # Removes volumes too
```

## Troubleshooting

### Service Won't Start

Check logs:
```bash
docker-compose logs
```

### Connection Refused

Ensure the service is running:
```bash
docker-compose ps
```

### Port Already in Use

Change port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Use 8080 instead of 8000
```

### OrcaSlicer CLI Not Found

The Dockerfile may need updating with the correct OrcaSlicer download URL. Check:
```bash
docker exec -it orcaslicer-api ls -la /app/squashfs-root/AppRun
```

## Next Steps

1. **Read the full docs**: [README.md](README.md)
2. **Explore API reference**: [API_REFERENCE.md](API_REFERENCE.md)
3. **Deploy to production**: [DEPLOYMENT.md](DEPLOYMENT.md)
4. **Contribute**: [CONTRIBUTING.md](CONTRIBUTING.md)

## Getting Help

- Check documentation in the `*.md` files
- Review example code in `example_usage.py`
- Open an issue on GitHub
- Check Docker logs for errors

## Summary of URLs

| Resource | URL |
|----------|-----|
| API Base | http://localhost:8000 |
| Health Check | http://localhost:8000/health |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI Schema | http://localhost:8000/openapi.json |

---

**You're all set!** 🎉

The OrcaSlicer API is now running and ready to slice your 3D models.
