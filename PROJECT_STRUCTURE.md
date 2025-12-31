# Elevator Simulator - Project Structure

## 📁 Directory Organization

```
elevator/
├── src/                          # Source code
│   ├── core/                     # Core simulation logic
│   │   ├── __init__.py
│   │   ├── elevator_simulator.py # Elevator, Building, Person classes
│   │   ├── simulation_engine.py  # Simulation orchestration
│   │   ├── interfaces.py         # 🆕 DI interfaces and protocols
│   │   ├── strategies.py         # 🆕 Elevator assignment strategies
│   │   └── container.py          # 🆕 DI container
│   │
│   ├── visualization/            # Visualization modules
│   │   ├── __init__.py
│   │   ├── visualization.py      # ASCII visualization
│   │   └── pygame_visualization.py # Pygame GUI
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── config_loader.py      # Configuration management
│       └── demo_loader.py        # Demo scenario loader
│
├── config/                       # Configuration files
│   ├── elevator_config.json      # Main configuration
│   └── demo_scenarios.json       # Demo scenarios
│
├── tests/                        # Test & debug scripts
│   ├── test_config_integration.py
│   ├── test_movement.py
│   ├── test_realistic_visitors.py
│   ├── test_heavy_load.py        # Heavy traffic stress test
│   ├── test_dependency_injection.py  # 🆕 DI tests
│   ├── debug_stuck_elevator.py   # Debug utility
│   └── verify_structure.py       # Structure verification
│
├── demos/                        # Demo scripts
│   ├── demo.py                   # Config-based demo runner
│   └── pygame_demo.py            # Pygame demo
│
├── examples/                     # 🆕 Usage examples
│   └── dependency_injection_demo.py  # DI usage examples
│
├── docs/                         # Documentation
│   ├── CONFIG_GUIDE.md
│   ├── INTERACTIVE_GUIDE.md
│   ├── DEPENDENCY_INJECTION.md   # 🆕 DI full guide
│   ├── DI_QUICKSTART.md          # 🆕 DI quick reference
│   ├── DI_ARCHITECTURE.md        # 🆕 DI architecture diagrams
│   ├── DI_IMPLEMENTATION_SUMMARY.md  # 🆕 Implementation summary
│   └── DI_MIGRATION_GUIDE.md     # 🆕 Migration guide
│
├── main.py                       # Main entry point
├── README.md                     # Project documentation
├── PROJECT_STRUCTURE.md          # This file
├── pyproject.toml                # Project configuration (uv)
└── uv.lock                       # Dependency lock file
```

## 🚀 Quick Start

### Installation

```bash
uv sync                          # Install dependencies
```

### Running the Simulation

```bash
# From the project root
uv run main.py demo              # Quick demo
uv run main.py visual            # ASCII visualization
uv run main.py pygame            # Graphical interface
uv run main.py help              # Show help and config
```

### Running Tests

```bash
uv run tests/test_config_integration.py
uv run tests/test_movement.py
uv run tests/test_realistic_visitors.py
```

### Running Demos

```bash
uv run demos/demo.py
uv run demos/pygame_demo.py
```

## 📦 Module Imports

### From other Python files

```python
# Core simulation
from src.core.simulation_engine import SimulationEngine
from src.core.elevator_simulator import Building, Elevator, Person, Direction

# Visualization
from src.visualization.visualization import run_visual_simulation
from src.visualization.pygame_visualization import run_pygame_simulation

# Configuration
from src.utils.config_loader import get_config

# 🆕 Dependency Injection (NEW!)
from src.core.interfaces import ElevatorConfig, ElevatorAssignmentStrategy
from src.core.strategies import NearestCarStrategy, SCANStrategy, RoundRobinStrategy
from src.core.container import Container, create_default_container, create_test_container
```

### Using Dependency Injection

```python
# Quick start with DI
from src.core.container import create_test_container

# Test with different strategy
container = create_test_container(strategy_name='scan')
config = container.resolve('config')
strategy = container.resolve('strategy')

# Test with config overrides
container = create_test_container(
    config_overrides={'num_floors': 10, 'elevator_speed': 10.0}
)
```

## ⚙️ Configuration

Edit `config/elevator_config.json` to customize:

- Building parameters (floors, elevators, capacity, speed)
- Strategy weights (distance, direction bonuses/penalties)
- Traffic patterns (arrival rates, rush hour multipliers)
- Simulation timing (control loop intervals, delays)

See `docs/CONFIG_GUIDE.md` for detailed configuration documentation.

## 📖 Documentation

- **CONFIG_GUIDE.md** - Complete configuration guide with examples
- **INTERACTIVE_GUIDE.md** - Interactive mode usage guide
- **README.md** - Main project documentation

## 🧪 Testing

Tests are organized by functionality:

- **test_config_integration.py** - Verify config system works
- **test_movement.py** - Test elevator movement logic
- **test_realistic_visitors.py** - Test visitor patterns

## 🎨 Visualization Options

1. **ASCII Mode** (`visualization.py`)
   - Real-time text-based visualization
   - Works in any terminal
   - Statistics dashboard

2. **Pygame Mode** (`pygame_visualization.py`)
   - Modern graphical interface
   - Mouse and keyboard controls
   - Smooth animations
   - Requires pygame package

## 📝 Notes

- All imports use absolute paths from project root
- Configuration file automatically loaded from `config/` directory
- Tests and demos can be run independently
- Main entry point is `main.py` in project root
