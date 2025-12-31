# Elevator Mall Simulator

A comprehensive, realistic elevator simulation system for a multi-story mall with intelligent scheduling, realistic traffic patterns, and real-time visualization.

## Features

### 🏢 Realistic Building Simulation

- Configurable number of floors (5-50) and elevators (1-8)
- Individual elevator properties (capacity, speed, efficiency)
- Smart elevator scheduling and dispatch algorithms
- Realistic passenger boarding and movement

### 👥 Intelligent Traffic Generation

- Mall-specific traffic patterns (ground floor popularity, top floor restaurants)
- Rush hour simulation (morning, lunch, evening)
- Poisson arrival distribution for realistic passenger generation
- Varied destination preferences based on floor types

### 🎮 Multiple Visualization Modes

- **ASCII Art Display**: Real-time building view with elevator positions
- **Pygame Graphics**: Modern graphical interface with smooth animations
- **Statistics Dashboard**: Comprehensive performance metrics
- **Interactive Mode**: Live controls with manual request addition
- **Command-line Interface**: Various simulation modes

### 📊 Advanced Analytics

- Real-time performance tracking
- Trend analysis and efficiency metrics
- Comparative benchmarking across configurations
- Wait time optimization and throughput analysis

### 🆕 Advanced Features (NEW!)

#### **Event Bus System** (Observer Pattern)

- Subscribe to simulation events in real-time
- EventLogger for file-based event logging
- EventMetrics for statistics collection
- Thread-safe publish/subscribe
- **Coverage: 96%** | **Tests: 11**

#### **Advanced Assignment Strategies**

- **LOOK Strategy**: More efficient than SCAN (reverses at last request)
- **Destination Dispatch**: Groups passengers by destination floor
- **ML-based Strategy**: Online learning with feedback (learning_rate=0.1)
- **Adaptive Strategy**: Auto-switches based on traffic patterns
- **Coverage: 91%** | **Tests: 14**

#### **Performance Benchmarking Framework**

- Compare multiple strategies systematically
- BenchmarkResult with comprehensive metrics
- ComparisonReport with winner detection
- JSON export for analysis
- **Coverage: 90%** | **Tests: 23**

#### **Data Persistence**

- Record simulations with snapshots and events
- Save/load recordings (with gzip compression)
- Replay simulations with callbacks
- Export to CSV for analysis
- Compare multiple sessions
- **Coverage: 98%** | **Tests: 34**

#### **Pydantic Configuration Validation**

- Type-safe configuration with validation
- Field constraints (min/max, cross-field validation)
- ConfigFactory with 5 presets (small/medium/large/testing/benchmark)
- Config file validation and migration
- **Coverage: 99%** | **Tests: 28**

## Quick Start

### Installation

```bash
# Install dependencies with uv
uv sync
```

### Basic Demo (2 minutes)

```bash
uv run main.py demo
```

### Interactive Mode

```bash
uv run main.py interactive
```

### Visual Simulation

```bash
uv run main.py visual
```

### Pygame Graphics

```bash
uv run main.py pygame
```

### Custom Configuration

```bash
uv run main.py custom
```

### Command-Line Arguments

You can specify the number of floors and elevators for any mode:

```bash
# Demo with 20 floors and 6 elevators
uv run main.py demo --floors 20 --elevators 6

# Visual mode with 8 floors and 1 elevator (short flags)
uv run main.py visual -f 8 -e 1

# Pygame graphics with custom building size  
uv run main.py pygame --floors 15 --elevators 3

# Interactive mode with custom building size
uv run main.py interactive --floors 25 --elevators 5

# Statistics mode with large building
uv run main.py stats --floors 30 --elevators 8
```

**Parameter Ranges:**

- Floors: 5-50 (default varies by mode)
- Elevators: 1-8 (default varies by mode)

**Default Values by Mode:**

- Demo: 15 floors, 3 elevators
- Visual: 15 floors, 3 elevators  
- Interactive: 15 floors, 4 elevators
- Stats: 20 floors, 4 elevators

## Architecture

### Core Components

1. **Elevator Class** (`elevator_simulator.py`)
   - Individual elevator logic and state management
   - Passenger boarding/unboarding
   - Request handling and destination management
   - Performance tracking

2. **Building Class** (`elevator_simulator.py`)
   - Overall building coordination
   - Floor-based waiting queues
   - Elevator assignment optimization
   - Traffic statistics

3. **Person Class** (`elevator_simulator.py`)
   - Individual passenger representation
   - Wait time tracking
   - Direction and destination logic

4. **SimulationEngine** (`simulation_engine.py`)
   - Main simulation orchestration
   - Multi-threaded elevator controllers
   - Traffic management
   - Statistics collection

5. **Visualization System** (`visualization.py`)
   - ASCII art building display
   - Real-time statistics dashboard
   - Interactive controls
   - Performance reporting

### Intelligent Algorithms

#### Elevator Scheduling

The system uses a sophisticated scoring algorithm to assign elevators to requests:

- **Distance Factor**: Closer elevators score better
- **Direction Alignment**: Bonus for elevators already moving in the right direction
- **Load Optimization**: Penalties for full elevators
- **Efficiency Tracking**: Historical performance consideration

#### Traffic Patterns

Realistic mall traffic simulation includes:

- **Floor Popularity**: Ground floor (30%), lower floors (15%), top floors (12%)
- **Rush Hours**: 8-10 AM, 12-2 PM, 5-7 PM with 2-3x normal traffic
- **Destination Logic**: Smart floor selection based on current location

## Usage Examples

### Command Line Options

```bash
# Quick demonstration
uv run main.py demo

# Visual simulation with ASCII art
uv run main.py visual

# Interactive mode with controls
uv run main.py interactive

# Statistics-focused run
uv run main.py stats

# Custom configuration
uv run main.py custom

# Performance benchmarking
uv run main.py benchmark

# Help information
uv run main.py help
```

### Programmatic Usage

#### Basic Simulation

```python
from src.core.simulation_engine import SimulationEngine
from src.visualization.visualization import InteractiveController

# Create simulation
sim = SimulationEngine(num_floors=20, num_elevators=4)

# Start simulation
sim.start_simulation()

# Add manual requests
sim.add_manual_request(from_floor=1, to_floor=15)

# Get statistics
stats = sim.get_current_statistics()
print(f"Throughput: {stats['throughput']:.1f} people/hour")

# Stop simulation
sim.stop_simulation()
```

#### Using Advanced Features

**Event Bus - Monitor Events**

```python
from src.core.event_bus import EventBus, EventType

bus = EventBus()

# Subscribe to elevator events
def on_elevator_moved(event):
    print(f"Elevator {event.data['elevator_id']} moved to floor {event.data['floor']}")

bus.subscribe(EventType.ELEVATOR_MOVED, on_elevator_moved)
bus.subscribe(EventType.PASSENGER_PICKED_UP, lambda e: print(f"Picked up passenger {e.data['passenger_id']}"))

# Publish events
bus.publish(EventType.ELEVATOR_MOVED, {"elevator_id": 1, "floor": 5})
```

**Benchmarking - Compare Strategies**

```python
from src.core.benchmarking import QuickBenchmark

# Quick comparison of strategies
report = QuickBenchmark.quick_compare(
    strategies=['nearest', 'scan', 'round_robin', 'look', 'adaptive'],
    duration=60.0
)

# Print results
report.print_comparison()

# Get best performer
winner = report.get_winner('avg_wait_time')
print(f"Best strategy: {winner.strategy_name}")
```

**Persistence - Record & Replay**

```python
from src.core.persistence import SimulationRecorder, SimulationReplayer

# Record a simulation
recorder = SimulationRecorder(storage_dir='simulation_data')
recorder.start(
    config={'num_floors': 20, 'num_elevators': 4},
    strategy_name='nearest'
)

# Record snapshots during simulation
recorder.record_snapshot(snapshot)
recorder.record_event({'type': 'request', 'floor': 5})

# Finalize and save
recorder.stop({'total_completed': 100})
filepath = recorder.save(compress=True)

# Replay later
replayer = SimulationReplayer(storage_dir='simulation_data')
replayer.replay(session_id='20250101_120000')
```

**Validated Config - Type-Safe Configuration**

```python
from src.core.validated_config import ConfigFactory, ElevatorSystemConfig

# Use presets
config = ConfigFactory.medium_building()  # 20 floors, 4 elevators
fast_config = ConfigFactory.fast_testing()  # Optimized for testing

# Save/load configs
config.save_to_file('my_config.json')
loaded = ElevatorSystemConfig.load_from_file('my_config.json')

# Validation happens automatically
try:
    bad_config = ElevatorSystemConfig(
        building={'num_floors': 200}  # Too many!
    )
except ValidationError as e:
    print(f"Invalid config: {e}")
```

**Advanced Strategies**

```python
from src.core.advanced_strategies import (
    LOOKStrategy,
    DestinationDispatchStrategy,
    MLBasedStrategy,
    AdaptiveStrategy,
)
from src.core.container import create_test_container

# Use LOOK strategy (more efficient than SCAN)
container = create_test_container(strategy_name='look')

# Or create custom strategy
look_strategy = LOOKStrategy()
dispatch_strategy = DestinationDispatchStrategy()
ml_strategy = MLBasedStrategy(learning_rate=0.1)
adaptive_strategy = AdaptiveStrategy()  # Auto-switches based on traffic

# Provide feedback for ML strategy
ml_strategy.provide_feedback(
    elevator_id=0,
    request={'floor': 5, 'direction': 'UP'},
    wait_time=12.5,
    success=True
)
```

## Performance Metrics

The simulator tracks comprehensive performance metrics:

### Traffic Metrics

- Total people generated and completed
- Current waiting queue size
- People in transit
- Average wait times

### Efficiency Metrics

- Elevator utilization rates
- Distance traveled per elevator
- Passengers served per elevator
- System throughput (people/hour)

### Trend Analysis

- Wait time trends (improving/worsening)
- Throughput changes over time
- Peak usage periods
- System efficiency evolution

## Display Legend

### ASCII Visualization

```text
[↑2/8]  - Elevator going UP with 2/8 passengers
[↓5/8]  - Elevator going DOWN with 5/8 passengers  
[○3/8]  - Elevator IDLE with 3/8 passengers
[◆4/8]  - Elevator LOADING with 4/8 passengers
↑3 ↓2   - 3 people waiting UP, 2 waiting DOWN
◇       - Floor has pending request
│       - Empty elevator shaft
```

### Elevator States

- **IDLE**: No requests, stationary
- **MOVING**: Traveling between floors
- **LOADING**: Stopped for passenger exchange
- **MAINTENANCE**: Out of service (future feature)

## Configuration Options

### Building Parameters

- **Floors**: 5-50 floors (default: 15-20)
- **Elevators**: 1-8 elevators (default: 3-4)
- **Elevator Capacity**: 6-12 people (randomized)
- **Elevator Speed**: 1.5-3.0 floors/second (randomized)

### Traffic Parameters

- **Base Arrival Rate**: 2 people/minute (configurable)
- **Rush Hour Multiplier**: 3x normal rate
- **Floor Popularity**: Weighted distribution
- **Destination Logic**: Mall-specific patterns

## Example Output

```text
=== ELEVATOR MALL SIMULATOR ===
Time: 45.2s | Generated: 23 | Completed: 18 | Waiting: 5
Average Wait: 12.3s | Throughput: 85.2/hour

Floor   Elev1    Elev2    Elev3
15:     │        │        │    
14:     │        [↓2/8]   │    
13:     │        │        │    
12:     [↑4/6]   │        │    
...
2:      │        │        │     ↑2
1:      │        │        [○1/8] ↓1

ELEVATOR STATUS:
Elevator 1: Floor 12 | UP | MOVING | Load: 4/6
  Passengers: P5→15, P7→14, P12→15, P15→13
  Requests: Up: [15] | Dest: [13, 14, 15]
  Served: 8 | Distance: 45.2 floors | Efficiency: 78.3%
```

## Development

### Testing

The project uses pytest for comprehensive testing:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test files
uv run pytest tests/test_event_bus.py -v
uv run pytest tests/test_benchmarking.py -v
uv run pytest tests/test_persistence.py -v

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run fast tests (exclude slow ones)
uv run pytest -m "not slow"
```

**Test Suite Summary:**

| Test File | Tests | Coverage | Status |
|-----------|-------|----------|--------|
| test_event_bus.py | 11 | 96% | ✅ |
| test_advanced_strategies.py | 14 | 91% | ✅ |
| test_validated_config.py | 28 | 99% | ✅ |
| test_benchmarking.py | 23 | 90% | ✅ |
| test_persistence.py | 34 | 98% | ✅ |
| **Total** | **110** | **40%** | **✅** |

See [tests/README.md](tests/README.md) for detailed testing documentation.

**Current Overall Coverage: 40%**

### File Structure

```text
elevator/
├── src/
│   ├── core/
│   │   ├── elevator_simulator.py   # Core classes (Elevator, Building, Person)
│   │   ├── simulation_engine.py    # Simulation orchestration
│   │   ├── interfaces.py           # DI interfaces and protocols
│   │   ├── strategies.py           # Basic assignment strategies
│   │   ├── container.py            # DI container
│   │   ├── event_bus.py            # 🆕 Event system (Observer)
│   │   ├── advanced_strategies.py  # 🆕 Advanced algorithms
│   │   ├── benchmarking.py         # 🆕 Performance framework
│   │   ├── persistence.py          # 🆕 Save/replay
│   │   └── validated_config.py     # 🆕 Pydantic validation
│   ├── visualization/
│   │   ├── visualization.py        # ASCII display
│   │   └── pygame_visualization.py # Pygame graphics
│   └── utils/
│       ├── config_loader.py        # Configuration management
│       └── demo_loader.py          # Demo scenarios
├── config/
│   ├── elevator_config.json        # System configuration
│   └── demo_scenarios.json         # Demo scenarios
├── tests/                          # Test suite
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_config_integration.py  # Config tests
│   ├── test_movement.py            # Movement tests
│   ├── test_heavy_load.py          # Stress tests
│   ├── test_dependency_injection.py # DI tests
│   ├── test_event_bus.py           # 🆕 Event system tests
│   ├── test_advanced_strategies.py # 🆕 Strategy tests
│   ├── test_validated_config.py    # 🆕 Config tests
│   ├── test_benchmarking.py        # 🆕 Benchmark tests
│   ├── test_persistence.py         # 🆕 Persistence tests
│   └── README.md                   # Testing docs
├── demos/                          # Demo scripts
├── docs/                           # Documentation
├── main.py                         # Main entry point
└── pyproject.toml                  # Project configuration
```

### Key Classes

- `Elevator`: Individual elevator logic
- `Building`: Overall building coordination  
- `Person`: Passenger representation
- `SimulationEngine`: Main simulation controller
- `ElevatorController`: Per-elevator thread management
- `TrafficManager`: Realistic passenger generation
- `ASCIIDisplay`: Real-time visualization
- `StatisticsTracker`: Performance analytics

### Design Patterns & Architecture

The system uses modern software design patterns for flexibility and testability:

#### Dependency Injection (NEW! 🎉)

The system now uses **Dependency Injection** for improved testability and flexibility:

```python
from src.core.container import create_test_container

# Test with different elevator assignment strategies
container = create_test_container(strategy_name='scan')
strategy = container.resolve('strategy')

# Override configuration for testing
container = create_test_container(
    config_overrides={'num_floors': 5, 'elevator_speed': 10.0}
)
```

**Available Strategies:**

**Basic Strategies:**

- `NearestCarStrategy`: Default - scores based on distance, load, direction
- `SCANStrategy`: Elevator continues in same direction (like disk scheduling)
- `RoundRobinStrategy`: Simple load balancing across elevators

**Advanced Strategies (🆕 NEW):**

- `LOOKStrategy`: Like SCAN but reverses at last request (more efficient)
- `DestinationDispatchStrategy`: Groups passengers by destination floor
- `MLBasedStrategy`: Online learning with weighted voting (learning_rate=0.1)
- `AdaptiveStrategy`: Auto-switches strategies based on traffic patterns

**Benefits:**

- ✅ Easy to swap elevator algorithms without code changes
- ✅ Simple to inject test configurations
- ✅ Better testability with mock dependencies
- ✅ Clear separation of concerns

**Documentation:**

- 📖 [Full DI Guide](docs/DEPENDENCY_INJECTION.md) - Complete documentation
- ⚡ [Quick Start](docs/DI_QUICKSTART.md) - TL;DR version
- 💡 [Examples](examples/dependency_injection_demo.py) - Usage examples
- ✅ [Tests](tests/test_dependency_injection.py) - Test cases

**Strategy Pattern**: Pluggable elevator assignment algorithms  
**Context Manager**: Clean simulation session management  
**Protocols**: Interface-based design for extensibility

### Dependencies

- Python 3.8+
- `pygame>=2.6.1` - For graphical visualization
- `pydantic>=2.0` - For configuration validation
- **Development:**
  - `pytest>=8.0.0` - Testing framework
  - `pytest-cov>=4.1.0` - Coverage reporting
  - `black>=24.8.0` - Code formatting
  - `ruff>=0.14.9` - Linting

Install all dependencies:

```bash
uv sync
```

## Future Enhancements

- **Elevator Maintenance**: Scheduled downtime simulation
- **Emergency Scenarios**: Fire evacuation protocols
- **Energy Optimization**: Power consumption modeling
- **Web Interface**: Browser-based visualization and control
- **Multi-building**: Campus or mall complex simulation
- **Accessibility**: Wheelchair and mobility considerations
- **Load Balancing**: Dynamic elevator bank management
- **Real-time API**: WebSocket support for live monitoring

## Contributing

This simulator provides a solid foundation for elevator system research, optimization algorithm testing, and educational purposes. The modular architecture makes it easy to extend with new features and algorithms.

## License

Open source project for educational and research purposes.
