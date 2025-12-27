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

```python
from simulation_engine import SimulationEngine
from visualization import InteractiveController

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

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run fast tests (exclude slow ones)
uv run pytest -m "not slow"
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

**Current Test Coverage: 41%**

### File Structure

```text
elevator/
├── src/
│   ├── core/
│   │   ├── elevator_simulator.py   # Core classes (Elevator, Building, Person)
│   │   └── simulation_engine.py    # Simulation orchestration
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

### Dependencies

- Python 3.8+
- `pygame>=2.6.1` - For graphical visualization
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
- **Advanced AI**: Machine learning for predictive scheduling
- **Web Interface**: Browser-based visualization
- **Multi-building**: Campus or mall complex simulation
- **Accessibility**: Wheelchair and mobility considerations
- **Load Balancing**: Dynamic elevator bank management

## Contributing

This simulator provides a solid foundation for elevator system research, optimization algorithm testing, and educational purposes. The modular architecture makes it easy to extend with new features and algorithms.

## License

Open source project for educational and research purposes.
