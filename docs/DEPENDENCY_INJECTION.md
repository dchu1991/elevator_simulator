# Dependency Injection Guide

## Overview

This project uses **Dependency Injection (DI)** to improve testability, flexibility, and maintainability. DI allows components to receive their dependencies from external sources rather than creating them internally.

## Benefits

### 1. **Testability**

```python
# Without DI - hard to test
class Building:
    def __init__(self):
        self.config = get_config()  # Singleton - can't substitute
        self.strategy = NearestCarStrategy()  # Hardcoded - can't change

# With DI - easy to test
class Building:
    def __init__(self, config: ElevatorConfig, strategy: ElevatorAssignmentStrategy):
        self.config = config  # Can inject test config
        self.strategy = strategy  # Can inject mock strategy
```

### 2. **Flexibility**

Switch algorithms without code changes:

```python
# Production: use Nearest strategy
container = create_default_container()

# Testing: try SCAN strategy
container = create_test_container(strategy_name='scan')

# Benchmarking: compare all strategies
for strategy in ['nearest', 'scan', 'round_robin']:
    container = create_test_container(strategy_name=strategy)
    # Run tests...
```

### 3. **Decoupling**

Components don't know how their dependencies are created:

```python
# Component only knows it needs "a strategy" - doesn't care which one
class ElevatorController:
    def __init__(self, strategy: ElevatorAssignmentStrategy):
        self.strategy = strategy  # Works with any strategy implementation
```

## Core Components

### 1. Interfaces ([interfaces.py](../src/core/interfaces.py))

**ElevatorConfig**: Dataclass replacing singleton pattern

```python
@dataclass
class ElevatorConfig:
    num_floors: int = 20
    elevator_speed: float = 2.0
    # ... 50+ configuration parameters
```

**ElevatorAssignmentStrategy**: ABC for elevator algorithms

```python
class ElevatorAssignmentStrategy(ABC):
    @abstractmethod
    def assign_elevator(
        self, 
        elevators: List[Elevator], 
        floor: int, 
        direction: Direction, 
        config: ElevatorConfig
    ) -> int:
        """Return index of best elevator"""
        pass
```

**Protocol Interfaces**: For future extension

- `IPersonGenerator`: Custom person generation patterns
- `ITrafficManager`: Traffic pattern management
- `IStatisticsCollector`: Custom metrics collection
- `IEventBus`: Event-driven architecture

### 2. Strategies ([strategies.py](../src/core/strategies.py))

**NearestCarStrategy** (Default)

- Scores elevators based on distance, load, direction
- Configurable weights via `ElevatorConfig`
- Best for general-purpose use

**SCANStrategy**

- Elevator continues in same direction until no requests
- More efficient for heavy unidirectional traffic
- Similar to disk scheduling SCAN algorithm

**RoundRobinStrategy**

- Simple load balancing across elevators
- Good for uniform traffic distribution
- Minimal computational overhead

### 3. Container ([container.py](../src/core/container.py))

**Container Class**: Manages dependency lifecycle

```python
class Container:
    def register_singleton(self, name: str, instance: Any)
    def register_factory(self, name: str, factory: Callable[[], Any])
    def register_type(self, name: str, type_class: type, *dependencies: str)
    def resolve(self, name: str) -> Any
```

**Factory Functions**:

- `create_default_container()`: Production configuration
- `create_test_container(**kwargs)`: Testing with overrides

## Usage Examples

### Basic DI Usage

```python
from src.core.container import create_default_container

# Create container with default configuration
container = create_default_container()

# Resolve dependencies
config = container.resolve('config')
strategy = container.resolve('strategy')

# Use in your code
building = Building(config=config, strategy=strategy)
```

### Testing with Config Overrides

```python
from src.core.container import create_test_container

# Create test container with overrides
container = create_test_container(
    config_overrides={
        'num_floors': 5,  # Smaller building for faster tests
        'elevator_speed': 100.0,  # Super fast for testing
        'max_capacity': 4,  # Smaller capacity
    }
)

config = container.resolve('config')
assert config.num_floors == 5  # Override applied
assert config.elevator_speed == 100.0  # Override applied
assert config.num_elevators == 4  # Default value (not overridden)
```

### Comparing Strategies

```python
from src.core.container import create_test_container

# Test all strategies
strategies = ['nearest', 'scan', 'round_robin']
results = {}

for strategy_name in strategies:
    container = create_test_container(strategy_name=strategy_name)
    strategy = container.resolve('strategy')
    
    # Run simulation with this strategy
    # ... collect metrics ...
    results[strategy_name] = metrics

# Compare results
print(f"Nearest: {results['nearest'].avg_wait_time}s")
print(f"SCAN: {results['scan'].avg_wait_time}s")
print(f"RoundRobin: {results['round_robin'].avg_wait_time}s")
```

### Manual Dependency Injection

```python
from src.core.interfaces import ElevatorConfig
from src.core.strategies import SCANStrategy

# Create dependencies manually
config = ElevatorConfig(
    num_floors=10,
    num_elevators=3,
    elevator_speed=2.5
)
strategy = SCANStrategy()

# Inject into components
building = Building(config=config, strategy=strategy)
controller = ElevatorController(strategy=strategy)
```

## Integration Roadmap

### Phase 1: Foundation ✅ (Complete)

- [x] Create interfaces and protocols
- [x] Implement strategy pattern for elevator assignment
- [x] Build DI container
- [x] Add comprehensive tests
- [x] Create documentation and examples

### Phase 2: Core Refactoring (Next Steps)

- [ ] Refactor `SimulationEngine` to accept injected dependencies
- [ ] Refactor `Building` to use injected `ElevatorAssignmentStrategy`
- [ ] Replace `get_config()` singleton with injected `ElevatorConfig`
- [ ] Update all calling code to use `container.resolve()`

### Phase 3: Advanced Features

- [ ] Implement `IEventBus` for observer pattern
- [ ] Add event logging and monitoring
- [ ] Create more strategies (LOOK, Destination Dispatch, Machine Learning)
- [ ] Add strategy performance comparison tools

### Phase 4: Testing & Optimization

- [ ] Add integration tests using DI
- [ ] Create benchmark suite comparing strategies
- [ ] Add configuration validation
- [ ] Performance profiling with different strategies

## Testing

Run DI-specific tests:

```bash
pytest tests/test_dependency_injection.py -v
```

Run all tests:

```bash
pytest -v
```

## Design Patterns Used

### 1. Strategy Pattern

- **Intent**: Define family of algorithms, encapsulate each, make them interchangeable
- **Used in**: `ElevatorAssignmentStrategy` with multiple implementations
- **Benefits**: Switch algorithms without changing client code

### 2. Dependency Injection

- **Intent**: Invert control of dependency creation
- **Used in**: `Container` class manages all dependencies
- **Benefits**: Testability, flexibility, decoupling

### 3. Abstract Base Class (ABC)

- **Intent**: Define interface contracts
- **Used in**: `ElevatorAssignmentStrategy` base class
- **Benefits**: Type safety, clear contracts

### 4. Protocol (Structural Typing)

- **Intent**: Define interfaces through structure, not inheritance
- **Used in**: `IPersonGenerator`, `ITrafficManager`, etc.
- **Benefits**: Duck typing with type checking

### 5. Factory Pattern

- **Intent**: Encapsulate object creation
- **Used in**: `create_default_container()`, `create_test_container()`
- **Benefits**: Consistent object creation, easy configuration

## Common Patterns

### Pattern: Test Configuration Override

```python
def test_high_traffic():
    container = create_test_container(
        config_overrides={
            'spawn_interval': 0.1,  # Spawn people every 0.1s
            'max_capacity': 10,
        }
    )
    # Test with high traffic...
```

### Pattern: Strategy Comparison

```python
def compare_strategies():
    base_config = {'num_floors': 20, 'num_elevators': 4}
    
    for strategy in ['nearest', 'scan', 'round_robin']:
        container = create_test_container(
            strategy_name=strategy,
            config_overrides=base_config
        )
        # Run identical simulation...
        # Compare results...
```

### Pattern: Mock Dependencies

```python
def test_with_mock_strategy():
    class MockStrategy(ElevatorAssignmentStrategy):
        def assign_elevator(self, elevators, floor, direction, config):
            return 0  # Always assign first elevator
    
    config = ElevatorConfig()
    strategy = MockStrategy()
    
    building = Building(config=config, strategy=strategy)
    # Test with predictable behavior...
```

## FAQ

**Q: Why not just use global `get_config()`?**  
A: Singletons make testing hard. With DI, you can easily inject test configurations without affecting other tests.

**Q: Isn't DI more complex?**  
A: Initially yes, but it pays off quickly:

- Tests run faster (inject fast test configs)
- Tests are isolated (no shared state)
- Easy to experiment (swap strategies)
- Clearer dependencies (explicit in constructors)

**Q: How do I choose a strategy?**  
A:

- `NearestCarStrategy`: General-purpose, good default
- `SCANStrategy`: Heavy unidirectional traffic (morning rush to top floors)
- `RoundRobinStrategy`: Uniform distribution, simple load balancing
- Custom: Implement `ElevatorAssignmentStrategy` for specific needs

**Q: Can I create custom strategies?**  
A: Yes! Implement `ElevatorAssignmentStrategy`:

```python
class MyCustomStrategy(ElevatorAssignmentStrategy):
    def assign_elevator(self, elevators, floor, direction, config):
        # Your logic here
        return best_elevator_index
```

## Related Documentation

- [Examples](../examples/dependency_injection_demo.py) - Practical usage examples
- [Tests](../tests/test_dependency_injection.py) - Test cases demonstrating benefits
- [Interfaces](../src/core/interfaces.py) - Interface definitions
- [Strategies](../src/core/strategies.py) - Strategy implementations
- [Container](../src/core/container.py) - DI container implementation

## Summary

Dependency Injection transforms this codebase from tightly-coupled components to a flexible, testable architecture:

| Aspect | Before DI | After DI |
|--------|-----------|----------|
| **Testing** | Hard to override config/strategy | Easy to inject mocks |
| **Flexibility** | Hardcoded algorithms | Pluggable strategies |
| **Coupling** | Components create dependencies | Dependencies injected |
| **Configuration** | Singleton pattern | Dataclass pattern |
| **Extensibility** | Modify existing code | Add new implementations |

The DI infrastructure is now complete and ready for integration into the main codebase.
