# Elevator Simulator - Test Suite

## Running Tests

### Run all tests

```bash
uv run pytest
```

### Run with coverage report

```bash
uv run pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Run only unit tests

```bash
uv run pytest -m unit
```

### Run only integration tests

```bash
uv run pytest -m integration
```

### Run tests excluding slow ones

```bash
uv run pytest -m "not slow"
```

### Run specific test file

```bash
uv run pytest tests/test_movement.py -v
```

### Run specific test function

```bash
uv run pytest tests/test_movement.py::test_elevator_capacity -v
```

## Test Organization

### Test Files

- **test_config_integration.py** - Configuration loading and integration tests
- **test_movement.py** - Elevator movement and request handling tests
- **test_realistic_visitors.py** - Visitor pattern and behavior tests
- **test_heavy_load.py** - Stress testing with heavy traffic load (marked as slow)
- **debug_stuck_elevator.py** - Debug utility for troubleshooting stuck elevators
- **verify_structure.py** - Project structure verification script
- **conftest.py** - Shared pytest fixtures and configuration

### Test Markers

Tests are marked with the following markers:

- `@pytest.mark.unit` - Fast unit tests (< 1 second)
- `@pytest.mark.integration` - Integration tests that involve multiple components
- `@pytest.mark.slow` - Tests that take longer to run (> 10 seconds)

## Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

- `simple_building` - Building with 10 floors and 2 elevators
- `single_elevator_building` - Building with 5 floors and 1 elevator
- `simulation` - Full simulation engine (10 floors, 3 elevators)
- `small_simulation` - Small simulation for quick tests (5 floors, 1 elevator)
- `sample_person` - A sample person object for testing
- `config` - Current configuration object

## Coverage

Current test coverage: **41%**

To improve coverage, focus on:

- Visualization modules (currently 0%)
- Demo loader utilities (currently 0%)
- Edge cases in simulation engine
- Error handling paths

View detailed coverage report:

```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Writing New Tests

### Example Unit Test

```python
import pytest

@pytest.mark.unit
def test_elevator_capacity(simple_building):
    """Test that elevator respects capacity limits"""
    elevator = simple_building.elevators[0]
    assert elevator.capacity > 0
    assert not elevator.is_full
```

### Example Integration Test

```python
import pytest
import time

@pytest.mark.integration
def test_elevator_delivers_passenger(small_simulation):
    """Test complete passenger delivery workflow"""
    sim = small_simulation
    sim.start_simulation()
    
    sim.add_manual_request(1, 5)
    time.sleep(5)
    
    stats = sim.get_current_statistics()
    assert stats["total_people_completed"] > 0
```

## Continuous Integration

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: uv run pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Tips

- Use `pytest -v` for verbose output
- Use `pytest -s` to see print statements
- Use `pytest --lf` to run only last failed tests
- Use `pytest --pdb` to drop into debugger on failures
- Use `pytest -k "keyword"` to run tests matching keyword
