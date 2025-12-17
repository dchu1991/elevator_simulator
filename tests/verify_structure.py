"""Quick verification that reorganized structure works"""

import sys
from pathlib import Path

# Ensure we can import from src (go up one level from tests to project root)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Testing reorganized project structure...")
print("=" * 50)

try:
    from src.core import SimulationEngine

    print("✓ Core module (SimulationEngine) imports")
except ImportError as e:
    print(f"✗ Core module failed: {e}")
    sys.exit(1)

try:
    from src.visualization import run_visual_simulation

    print("✓ Visualization module imports")
except ImportError as e:
    print(f"✗ Visualization module failed: {e}")
    sys.exit(1)

try:
    from src.utils import get_config

    config = get_config()
    print(
        f"✓ Config loads: {config.num_floors} floors, {config.num_elevators} elevators"
    )
except Exception as e:
    print(f"✗ Config failed: {e}")
    sys.exit(1)

try:
    sim = SimulationEngine()
    print("✓ Simulation engine creates successfully")
except Exception as e:
    print(f"✗ Simulation creation failed: {e}")
    sys.exit(1)

print("=" * 50)
print("All modules working! Project structure verified.")
print("\nRun 'uv run main.py help' to get started!")
