# OrcaSlicer API - Project Summary

## Overview

This project provides a production-ready HTTP API wrapper around OrcaSlicer, enabling programmatic 3D model slicing without GUI interaction. It's designed for large-scale additive manufacturing applications, pricing systems, and automated slicing workflows.

## What's Been Delivered

### 1. Complete FastAPI Application

**Location:** `src/`

- **API Routes** (`src/api/`)
  - Model management (upload, list, get)
  - Profile CRUD operations
  - Slice job management
  - Health check endpoint

- **Business Logic** (`src/services/`)
  - Storage service for file operations
  - Models service for upload/management
  - Profiles service for configuration
  - Slice service with OrcaSlicer CLI integration

- **Data Models** (`src/models/`)
  - SQLAlchemy ORM models
  - Pydantic schemas for validation
  - Type-safe request/response models

- **Core Utilities** (`src/core/`)
  - Configuration management
  - Structured JSON logging
  - Error handling with standard responses

### 2. Python Client Library

**Location:** `src/clients/python_client.py`

High-level client with methods for:
- Uploading models
- Managing profiles (create, list, get, update, delete)
- Creating and monitoring slice jobs
- Downloading outputs (G-code, 3MF)
- Comprehensive error handling

### 3. Docker Deployment

**Files:**
- `Dockerfile` - Multi-stage build with OrcaSlicer AppImage
- `docker-compose.yml` - Ready-to-use composition
- `.dockerignore` - Optimized build context

**Features:**
- Ubuntu 22.04 base
- OrcaSlicer CLI integration
- Persistent volume support
- Health checks
- Environment configuration

### 4. Documentation

- **README.md** - Complete user guide with examples
- **API_REFERENCE.md** - Comprehensive API documentation
- **DEPLOYMENT.md** - Production deployment guide
- **CONTRIBUTING.md** - Development guidelines
- **LICENSE** - MIT license

### 5. Testing Suite

**Location:** `tests/`

- Unit tests for API endpoints
- Client library tests
- pytest configuration
- Example test patterns

### 6. Example Code

- **example_usage.py** - Complete workflow demonstration
- Inline code examples in documentation
- Python client usage patterns

### 7. Development Tools

- `.gitignore` - Python/Docker ignore rules
- `.env.example` - Environment variable template
- `Makefile` - Common commands for development
- `pytest.ini` - Test configuration
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies

## Architecture Highlights

### Technology Stack

```
┌─────────────────────────────────────┐
│         Python 3.11+                │
│  ┌─────────────────────────────┐   │
│  │       FastAPI               │   │
│  │    (async/await)            │   │
│  └─────────────┬───────────────┘   │
│                │                    │
│  ┌─────────────▼───────────────┐   │
│  │    SQLAlchemy + SQLite      │   │
│  │   (async via aiosqlite)     │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  OrcaSlicer CLI             │   │
│  │  (subprocess execution)     │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Key Design Decisions

1. **Async Architecture**
   - FastAPI with async/await
   - Non-blocking database operations
   - Background job processing

2. **Layered Structure**
   - Routes → Services → Storage
   - Clear separation of concerns
   - Easy to test and maintain

3. **Type Safety**
   - Pydantic for validation
   - Type hints throughout
   - OpenAPI schema generation

4. **Error Handling**
   - Unified error response format
   - Custom exception classes
   - Proper HTTP status codes

5. **Logging**
   - Structured JSON logs
   - Contextual information
   - Docker-friendly output

## API Capabilities

### Supported Input Formats
- `.stl` (STereoLithography)
- `.step` (STEP format)
- `.3mf` (3D Manufacturing Format)

### Supported Outputs
- G-code files
- 3MF projects with settings
- JSON metadata (print time, material, layers, dimensions)

### Profile Management
- Built-in OrcaSlicer profiles
- Custom user profiles
- Settings inheritance and overrides
- Per-request parameter overrides

### Job Processing
- Asynchronous slicing
- Status polling
- Progress tracking
- Error reporting

## Example Workflow

```python
from src.clients.python_client import OrcaSlicerClient

# Initialize
client = OrcaSlicerClient(base_url="http://localhost:8000")

# Upload model
model = client.upload_model("bracket.stl")

# Create profile
profile = client.create_profile({
    "name": "My Profile",
    "vendor": "Ginger Additive",
    "machine_id": "large_manipulator",
    "settings_overrides": {"layer_height": 0.2}
})

# Slice with overrides
job = client.create_slice_job(
    model_id=model["id"],
    profile_id=profile["id"],
    overrides={"infill_density": 30},
    output_options={
        "gcode": True,
        "project_3mf": True,
        "metadata_json": True
    }
)

# Poll for completion
import time
while True:
    job = client.get_slice_job(job["id"])
    if job["status"] == "completed":
        break
    time.sleep(2)

# Download outputs
client.download_gcode(job["id"], "output.gcode")
client.download_project_3mf(job["id"], "project.3mf")

print(f"Print time: {job['output']['metadata']['estimated_print_time_seconds']}s")
```

## Deployment

### Docker (Recommended)

```bash
# Build
docker build -t orcaslicer-api .

# Run
docker-compose up -d

# Access
curl http://localhost:8000/health
```

### Local Development

```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
export ORCA_CLI_PATH=/path/to/orcaslicer
export DATA_DIR=./data

# Run
python -m uvicorn src.main:app --reload
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/models` | Upload model |
| GET | `/models` | List models |
| GET | `/models/{id}` | Get model |
| POST | `/profiles` | Create profile |
| GET | `/profiles` | List profiles |
| GET | `/profiles/{id}` | Get profile |
| PATCH | `/profiles/{id}` | Update profile |
| DELETE | `/profiles/{id}` | Delete profile |
| POST | `/slice-jobs` | Create job |
| GET | `/slice-jobs/{id}` | Get job status |
| GET | `/slice-jobs/{id}/gcode` | Download G-code |
| GET | `/slice-jobs/{id}/project.3mf` | Download 3MF |

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Project Structure

```
orcaslicer-api/
├── src/
│   ├── api/                    # HTTP endpoints
│   ├── core/                   # Configuration & utilities
│   ├── models/                 # Data models
│   ├── services/               # Business logic
│   ├── clients/                # Client libraries
│   ├── database.py            # DB setup
│   └── main.py                # FastAPI app
├── tests/                      # Test suite
├── Dockerfile                  # Container definition
├── docker-compose.yml         # Composition
├── requirements.txt           # Python dependencies
├── example_usage.py           # Usage examples
├── Makefile                   # Common commands
├── README.md                  # User guide
├── API_REFERENCE.md           # API docs
├── DEPLOYMENT.md              # Deployment guide
├── CONTRIBUTING.md            # Development guide
└── LICENSE                    # MIT license
```

## Use Cases

### 1. Automated Pricing
Generate cost estimates by:
- Uploading model
- Slicing with relevant settings
- Extracting print time and material usage
- Calculating price

### 2. Web-Based Slicing Service
Offer slicing as a service:
- Users upload models via web interface
- Backend uses this API for processing
- Return downloadable G-code

### 3. Manufacturing Pipeline
Batch process models:
- Automated workflow for production
- Custom machine profiles
- Quality assurance checks

### 4. Large-Format Additive Manufacturing
Support non-standard machines:
- Define custom machine profiles
- Large build volumes
- Specialized toolpaths

## Future Enhancements

### High Priority
- [ ] PostgreSQL support for scalability
- [ ] S3-compatible storage backend
- [ ] Authentication (JWT/API keys)
- [ ] Rate limiting
- [ ] Webhooks for notifications

### Medium Priority
- [ ] Advanced metadata extraction from 3MF
- [ ] WebSocket for real-time updates
- [ ] Job priority queue
- [ ] Prometheus metrics
- [ ] Multi-material support

### Nice to Have
- [ ] G-code preview generation
- [ ] Cost calculator plugin system
- [ ] Custom slicing engine plugins
- [ ] Model repair service
- [ ] Print time optimization hints

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_api.py

# Run client tests (requires running server)
pytest tests/test_client.py
```

## Performance Considerations

### Resource Requirements
- **CPU**: 2-4 cores minimum, 8+ recommended
- **Memory**: 4GB minimum, 8-16GB recommended
- **Storage**: SSD preferred for working directories
- **Network**: Standard bandwidth, low latency preferred

### Scalability
- **Single instance**: Can handle multiple concurrent jobs
- **Horizontal scaling**: Requires PostgreSQL + shared storage
- **Job queue**: Background processing prevents blocking

### Bottlenecks
- OrcaSlicer CLI execution time (model-dependent)
- File I/O for large models
- Database writes (SQLite limitations)

## Security Considerations

### Current State
- No authentication (suitable for internal networks)
- No rate limiting
- No input validation beyond format

### Production Recommendations
1. Add API authentication
2. Implement rate limiting
3. Enable HTTPS/TLS
4. Validate uploaded files
5. Set upload size limits
6. Run behind firewall
7. Regular security updates

## License

MIT License - See LICENSE file for full text.

## Acknowledgments

- Built on [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Designed for additive manufacturing workflows

## Support & Contact

- **Issues**: GitHub Issues
- **Documentation**: See docs/ folder
- **Examples**: See example_usage.py

---

**Status**: Production-ready for internal deployments. Suitable for:
- Internship deliverable ✓
- Internal tool deployment ✓
- Proof of concept ✓
- Production with authentication additions ✓

**Not included** (as specified):
- PrusaSlicer/SuperSlicer support (OrcaSlicer only)
- GUI/web interface (API only)
- User management system
- Payment/billing integration
