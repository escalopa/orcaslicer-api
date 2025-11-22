# Contributing to OrcaSlicer API

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, professional, and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
   - Relevant logs

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with:
   - Clear use case description
   - Why this feature would be useful
   - Potential implementation approach
   - Examples of similar features elsewhere

### Pull Requests

1. **Fork and Clone**

```bash
git clone https://github.com/yourusername/orcaslicer-api.git
cd orcaslicer-api
```

2. **Create a Branch**

```bash
git checkout -b feature/your-feature-name
```

3. **Make Changes**

Follow the coding standards below.

4. **Test Your Changes**

```bash
# Run tests
pytest tests/

# Test with Docker
docker build -t orcaslicer-api:test .
docker run -p 8000:8000 orcaslicer-api:test
```

5. **Commit**

```bash
git add .
git commit -m "Add: descriptive commit message"
```

Use conventional commit messages:
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for updates to existing features
- `Remove:` for removing features
- `Docs:` for documentation changes
- `Refactor:` for code refactoring
- `Test:` for test changes

6. **Push and Create PR**

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Development Setup

### Local Development

1. **Install Python 3.11+**

2. **Create virtual environment**

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements-dev.txt
```

4. **Set environment variables**

```bash
export ORCA_CLI_PATH=/path/to/orcaslicer
export DATA_DIR=./data
export LOG_JSON=false
```

5. **Run the server**

```bash
python -m uvicorn src.main:app --reload
```

### Docker Development

```bash
docker build -t orcaslicer-api:dev .
docker run -p 8000:8000 -v $(pwd)/data:/data orcaslicer-api:dev
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes

### Code Structure

```python
"""Module docstring."""

import standard_library
import third_party
from local import module

# Constants
CONSTANT_NAME = "value"

# Type aliases
TypeAlias = Dict[str, Any]


class ClassName:
    """Class docstring."""

    def method_name(self, param: str) -> str:
        """
        Method docstring.

        Args:
            param: Parameter description

        Returns:
            Return value description
        """
        pass
```

### FastAPI Routes

```python
@router.post("/endpoint", response_model=ResponseModel, status_code=201)
async def endpoint_function(
    param: ParamModel,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint description.

    Detailed explanation if needed.
    """
    pass
```

### Error Handling

```python
from src.core.errors import ApiError

if not resource:
    raise ApiError(
        code="RESOURCE_NOT_FOUND",
        message=f"Resource '{resource_id}' not found.",
        http_status=404,
        details={"resource_id": resource_id},
    )
```

### Logging

```python
from src.core.logging import logger

logger.info("Operation completed", extra={
    "operation": "slice",
    "job_id": job_id,
    "duration_ms": duration,
})
```

## Testing

### Writing Tests

Place tests in `tests/` directory:

```python
def test_feature():
    """Test feature description."""
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/endpoint")

    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "expected"
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_api.py

# With coverage
pytest --cov=src tests/
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include parameter types and return types
- Provide usage examples for complex functions

### API Documentation

- FastAPI auto-generates OpenAPI docs
- Add descriptions to endpoints and models
- Include example requests/responses in docstrings

### README Updates

Update README.md when:
- Adding new features
- Changing configuration options
- Modifying deployment process
- Adding dependencies

## Commit Guidelines

### Good Commit Messages

✅ Good:
```
Add: profile update endpoint with PATCH method

- Implement PATCH /profiles/{id}
- Support partial updates via ProfileUpdate schema
- Add test coverage for update scenarios
```

❌ Bad:
```
fixed stuff
```

### Commit Frequency

- Commit often, push when feature is complete
- Each commit should be logical and atomic
- Don't commit broken code to main branch

## Pull Request Process

1. **Update Documentation**
   - Update README if needed
   - Add/update docstrings
   - Update API_REFERENCE.md if adding endpoints

2. **Add Tests**
   - All new features need tests
   - Bug fixes should include regression tests
   - Aim for >80% code coverage

3. **Check CI**
   - Ensure all tests pass
   - Fix any linting errors
   - Verify Docker build succeeds

4. **Request Review**
   - Assign reviewers
   - Respond to feedback promptly
   - Make requested changes

5. **Merge**
   - Squash commits if many small commits
   - Use descriptive merge commit message
   - Delete branch after merge

## Areas for Contribution

Looking for ways to contribute? Consider:

### High Priority
- [ ] PostgreSQL support for horizontal scaling
- [ ] S3-compatible storage backend
- [ ] API authentication (JWT, API keys)
- [ ] Rate limiting
- [ ] Webhook support for job notifications

### Medium Priority
- [ ] More comprehensive OrcaSlicer parameter parsing
- [ ] 3MF metadata extraction improvements
- [ ] Job queue with priority support
- [ ] WebSocket for real-time progress updates
- [ ] Metrics endpoint (Prometheus)

### Documentation
- [ ] More example scripts
- [ ] Video tutorial
- [ ] Architecture deep-dive
- [ ] OrcaSlicer parameter reference

### Testing
- [ ] Integration tests with real OrcaSlicer
- [ ] Load testing
- [ ] Security testing
- [ ] Error scenario coverage

## Questions?

- Open an issue for questions
- Tag with `question` label
- We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
