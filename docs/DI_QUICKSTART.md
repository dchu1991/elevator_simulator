# Quick Start: Dependency Injection

## TL;DR

```python
from src.core.container import create_test_container

# Quick test with different strategy
container = create_test_container(strategy_name='scan')
strategy = container.resolve('strategy')

# Quick test with config override
container = create_test_container(
    config_overrides={'num_floors': 5, 'elevator_speed': 10.0}
)
config = container.resolve('config')
```

## Common Use Cases

### 1. Compare All Strategies

```python
from src.core.container import create_test_container

for strategy_name in ['nearest', 'scan', 'round_robin']:
    container = create_test_container(strategy_name=strategy_name)
    strategy = container.resolve('strategy')
    config = container.resolve('config')
    
    # Run your simulation...
    print(f"{strategy_name}: {avg_wait_time}s")
```

### 2. Test with Fast Configuration

```python
# Normal simulation takes minutes - speed it up for testing
container = create_test_container(
    config_overrides={
        'elevator_speed': 100.0,  # 50x faster
        'door_open_time': 0.01,    # 100x faster
        'loading_time': 0.01,      # 100x faster
        'num_floors': 5,           # Smaller building
    }
)
```

### 3. Stress Test

```python
container = create_test_container(
    config_overrides={
        'num_floors': 100,          # Tall building
        'num_elevators': 2,         # Few elevators
        'max_capacity': 4,          # Small elevators
        'spawn_interval': 0.1,      # Spawn very fast
    }
)
```

### 4. Custom Strategy

```python
from src.core.interfaces import ElevatorAssignmentStrategy, ElevatorConfig
from src.core.elevator_simulator import Elevator, Direction

class AlwaysFirstStrategy(ElevatorAssignmentStrategy):
    """Always use first elevator - for testing"""
    def assign_elevator(self, elevators, floor, direction, config):
        return 0

# Use it
config = ElevatorConfig()
strategy = AlwaysFirstStrategy()
# Inject into your building/controller...
```

## Strategy Reference

| Strategy | Best For | Pros | Cons |
|----------|----------|------|------|
| **nearest** | General use | Efficient, configurable | Complex scoring |
| **scan** | Rush hours | Predictable, efficient | May ignore far calls |
| **round_robin** | Uniform traffic | Simple, fair | Ignores distance |

## Configuration Override Cheatsheet

### Speed Controls

```python
config_overrides={
    'elevator_speed': 10.0,     # Default: 2.0 (floors/sec)
    'door_open_time': 0.5,      # Default: 2.0 (seconds)
    'loading_time': 0.1,        # Default: 1.0 (seconds)
}
```

### Capacity & Scale

```python
config_overrides={
    'num_floors': 10,           # Default: 20
    'num_elevators': 3,         # Default: 4
    'max_capacity': 6,          # Default: 8
}
```

### Traffic Patterns

```python
config_overrides={
    'spawn_interval': 1.0,      # Default: 3.0 (seconds between people)
    'peak_hours': [8, 9],       # Default: [8, 9, 12, 13, 17, 18]
    'peak_multiplier': 5.0,     # Default: 3.0 (spawn rate multiplier)
}
```

### Strategy Weights (for NearestCarStrategy)

```python
config_overrides={
    'distance_weight': 2.0,     # Default: 1.0 (prefer closer)
    'load_weight': 1.5,         # Default: 1.0 (prefer less loaded)
    'idle_bonus': -10,          # Default: -5 (prefer idle elevators)
    'opposite_direction_penalty': 20,  # Default: 10 (avoid wrong direction)
}
```

## Examples in Code

See [dependency_injection_demo.py](../examples/dependency_injection_demo.py) for complete examples:

1. Basic DI usage
2. Swapping strategies
3. Config overrides
4. Manual injection
5. Benefits demonstration

## Tests

See [test_dependency_injection.py](../tests/test_dependency_injection.py) for:

- Strategy injection tests
- Config override tests
- Strategy behavior tests
- Strategy comparison tests

Run tests:

```bash
pytest tests/test_dependency_injection.py -v
```

## Full Documentation

See [DEPENDENCY_INJECTION.md](DEPENDENCY_INJECTION.md) for complete guide.
