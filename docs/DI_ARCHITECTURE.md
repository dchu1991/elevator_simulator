# Dependency Injection Architecture

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ main.py      │  │ demos/       │  │ tests/       │          │
│  │ Interactive  │  │ Scenarios    │  │ Test Suite   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┼──────────────────┘                   │
│                            │                                      │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DI Container Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Container (src/core/container.py)            │   │
│  │  ┌─────────────────┐         ┌─────────────────┐         │   │
│  │  │ Factory:        │         │ Factory:        │         │   │
│  │  │ Default         │         │ Test            │         │   │
│  │  │ Container       │         │ Container       │         │   │
│  │  │                 │         │                 │         │   │
│  │  │ - Loads from    │         │ - Overrides     │         │   │
│  │  │   config file   │         │ - Mock deps     │         │   │
│  │  │ - Production    │         │ - Test configs  │         │   │
│  │  └────────┬────────┘         └────────┬────────┘         │   │
│  │           │                           │                  │   │
│  │           └───────────┬───────────────┘                  │   │
│  │                       │                                  │   │
│  │                       ▼                                  │   │
│  │           ┌──────────────────────┐                       │   │
│  │           │ resolve('config')    │──────────┐            │   │
│  │           │ resolve('strategy')  │          │            │   │
│  │           └──────────────────────┘          │            │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────┬────────────────────┘
                           │                  │
                           ▼                  ▼
┌──────────────────────────────────┐  ┌──────────────────────────────┐
│  Configuration (Injected)        │  │  Strategy (Injected)         │
│                                  │  │                              │
│  ElevatorConfig (dataclass)      │  │  ElevatorAssignmentStrategy  │
│  src/core/interfaces.py          │  │  src/core/strategies.py      │
│                                  │  │                              │
│  ┌────────────────────────────┐  │  │  ┌────────────────────────┐  │
│  │ Building Parameters:       │  │  │  │ NearestCarStrategy     │  │
│  │ - num_floors              │  │  │  │ - Distance scoring     │  │
│  │ - num_elevators           │  │  │  │ - Load balancing       │  │
│  │ - elevator_capacity       │  │  │  └────────────────────────┘  │
│  │ - elevator_speed          │  │  │                              │
│  ├────────────────────────────┤  │  │  ┌────────────────────────┐  │
│  │ Strategy Parameters:       │  │  │  │ SCANStrategy           │  │
│  │ - distance_weight         │  │  │  │ - Direction-based      │  │
│  │ - load_factor_weight      │  │  │  │ - Efficient for rush   │  │
│  │ - idle_bonus              │  │  │  └────────────────────────┘  │
│  ├────────────────────────────┤  │  │                              │
│  │ Traffic Parameters:        │  │  │  ┌────────────────────────┐  │
│  │ - base_arrival_rate       │  │  │  │ RoundRobinStrategy     │  │
│  │ - rush_multiplier         │  │  │  │ - Simple rotation      │  │
│  │ - enable_realistic_visitors│ │  │  │ - Fair distribution    │  │
│  ├────────────────────────────┤  │  │  └────────────────────────┘  │
│  │ Simulation Timing:         │  │  │                              │
│  │ - control_loop_interval   │  │  │  ┌────────────────────────┐  │
│  │ - movement_delay_factor   │  │  │  │ Custom Strategy        │  │
│  │ - stats_recording_interval│  │  │  │ - Implement ABC        │  │
│  └────────────────────────────┘  │  │  │ - Your algorithm       │  │
└──────────────────┬───────────────┘  └──┴────────────────────────┘  │
                   │                     │                            │
                   │                     │                            │
                   ▼                     ▼                            │
┌─────────────────────────────────────────────────────────────────┐
│                      Domain Layer                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            SimulationEngine (Future)                      │   │
│  │  def __init__(self, config: ElevatorConfig,              │   │
│  │               strategy: ElevatorAssignmentStrategy):      │   │
│  │      self.config = config                                │   │
│  │      self.strategy = strategy                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Building (Future)                              │   │
│  │  def __init__(self, config: ElevatorConfig,              │   │
│  │               strategy: ElevatorAssignmentStrategy):      │   │
│  │      self.config = config                                │   │
│  │      self.strategy = strategy                            │   │
│  │                                                           │   │
│  │  def assign_elevator(self, floor, direction):            │   │
│  │      return self.strategy.assign_elevator(...)           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Elevator, Person (Domain Models)               │   │
│  │  - Core business logic                                    │   │
│  │  - No external dependencies                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Dependency Flow

### Before DI (Current - Tight Coupling)

```
SimulationEngine
    │
    ├─> get_config() ──────────────┐ (Singleton - Global State)
    │                               │
    └─> Building                    │
            │                       │
            ├─> get_config() ───────┤ (Multiple calls to singleton)
            │                       │
            └─> Elevator.score() ───┘ (Hardcoded algorithm)
```

**Problems:**

- ❌ Hard to test (can't override config)
- ❌ Tight coupling (components know about global state)
- ❌ Can't swap algorithms without code changes

### After DI (Future - Loose Coupling)

```
Container
    │
    ├─> Creates ElevatorConfig ───────┐
    │                                  │
    └─> Creates Strategy ──────────────┤
                                       │
                                       ▼
                            SimulationEngine(config, strategy)
                                       │
                                       ├─> Passes config ───┐
                                       │                    │
                                       └─> Building(config, strategy)
                                                            │
                                                            ├─> Uses config
                                                            │
                                                            └─> Uses strategy
```

**Benefits:**

- ✅ Easy to test (inject mock config/strategy)
- ✅ Loose coupling (components receive dependencies)
- ✅ Flexible (swap implementations at runtime)
- ✅ Clear dependencies (explicit in constructors)

## Current State vs Future State

| Component | Current State | Future State (After Phase 2) |
|-----------|---------------|------------------------------|
| **ElevatorConfig** | Singleton `get_config()` | Injected dataclass |
| **Strategy** | Hardcoded in `Elevator.score()` | Injected `ElevatorAssignmentStrategy` |
| **SimulationEngine** | Creates dependencies | Receives dependencies |
| **Building** | Uses singleton config | Receives config + strategy |
| **Tests** | Hard to mock | Easy to inject test doubles |

## How to Use

### 1. Production Use (Current)

```python
# Old way (still works)
from utils.config_loader import get_config
config = get_config()  # Singleton

# New way (preferred)
from src.core.container import create_default_container
container = create_default_container()
config = container.resolve('config')
strategy = container.resolve('strategy')
```

### 2. Testing Use (New)

```python
from src.core.container import create_test_container

# Fast test configuration
container = create_test_container(
    strategy_name='round_robin',  # Simple strategy
    config_overrides={
        'num_floors': 5,
        'elevator_speed': 100.0,  # 50x faster
    }
)

config = container.resolve('config')
strategy = container.resolve('strategy')

# Use in tests
building = Building(config=config, strategy=strategy)
```

### 3. Comparing Strategies

```python
from src.core.container import create_test_container

strategies = ['nearest', 'scan', 'round_robin']

for strategy_name in strategies:
    container = create_test_container(strategy_name=strategy_name)
    config = container.resolve('config')
    strategy = container.resolve('strategy')
    
    # Run identical simulation with different strategy
    sim = SimulationEngine(config=config, strategy=strategy)
    results = sim.run()
    
    print(f"{strategy_name}: {results.avg_wait_time}s")
```

## Integration Steps (Phase 2)

### Step 1: Refactor SimulationEngine

```python
# Before
class SimulationEngine:
    def __init__(self, num_floors, num_elevators):
        self.config = get_config()  # Singleton
        self.building = Building(...)

# After
class SimulationEngine:
    def __init__(self, config: ElevatorConfig, 
                 strategy: ElevatorAssignmentStrategy):
        self.config = config
        self.building = Building(config=config, strategy=strategy)
```

### Step 2: Refactor Building

```python
# Before
class Building:
    def __init__(self, num_floors, num_elevators):
        self.config = get_config()  # Singleton
        
    def assign_elevator(self, floor, direction):
        # Hardcoded scoring logic
        best_elevator = min(elevators, key=lambda e: e.score(...))

# After
class Building:
    def __init__(self, config: ElevatorConfig,
                 strategy: ElevatorAssignmentStrategy):
        self.config = config
        self.strategy = strategy
        
    def assign_elevator(self, floor, direction):
        # Delegated to injected strategy
        idx = self.strategy.assign_elevator(
            self.elevators, floor, direction, self.config
        )
        return self.elevators[idx]
```

### Step 3: Update Calling Code

```python
# Before
sim = SimulationEngine(num_floors=20, num_elevators=4)

# After
from src.core.container import create_default_container

container = create_default_container()
config = container.resolve('config')
strategy = container.resolve('strategy')

sim = SimulationEngine(config=config, strategy=strategy)
```

## Extension Points

The architecture is designed for easy extension:

### Add New Strategy

```python
from src.core.interfaces import ElevatorAssignmentStrategy

class DestinationDispatchStrategy(ElevatorAssignmentStrategy):
    """Group passengers by destination floor"""
    def assign_elevator(self, elevators, floor, direction, config):
        # Your algorithm here
        return best_elevator_index
```

### Add New Protocol

```python
from typing import Protocol

class IEventBus(Protocol):
    """Event bus for observer pattern"""
    def publish(self, event: str, data: Any) -> None: ...
    def subscribe(self, event: str, handler: Callable) -> None: ...
```

### Register in Container

```python
def create_custom_container():
    container = Container()
    
    # Register your custom implementations
    container.register_singleton('config', custom_config)
    container.register_singleton('strategy', DestinationDispatchStrategy())
    container.register_singleton('event_bus', CustomEventBus())
    
    return container
```

## Summary

The DI architecture provides:

1. **Clear Separation**: Container → Dependencies → Domain
2. **Testability**: Easy to inject test doubles
3. **Flexibility**: Swap implementations without code changes
4. **Extensibility**: Add new strategies/protocols easily
5. **Maintainability**: Explicit dependency graph

**Status**: Foundation complete ✅, integration pending (Phase 2)
