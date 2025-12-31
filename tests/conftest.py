"""
Pytest configuration and shared fixtures
"""

import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.simulation_engine import SimulationEngine
from src.core.elevator_simulator import Building, Person
from src.utils.config_loader import get_config


@pytest.fixture
def simple_building():
    """Create a simple building for testing"""
    return Building(num_floors=10, num_elevators=2)


@pytest.fixture
def single_elevator_building():
    """Create a building with a single elevator"""
    return Building(num_floors=5, num_elevators=1)


@pytest.fixture
def simulation():
    """Create a basic simulation engine"""
    sim = SimulationEngine(num_floors=10, num_elevators=3)
    yield sim
    # Cleanup
    if sim.is_running:
        sim.stop_simulation()


@pytest.fixture
def small_simulation():
    """Create a small simulation for quick tests"""
    sim = SimulationEngine(num_floors=5, num_elevators=1)
    yield sim
    # Cleanup
    if sim.is_running:
        sim.stop_simulation()


@pytest.fixture
def sample_person():
    """Create a sample person for testing"""
    import time

    return Person(id=1, current_floor=1, destination_floor=5, arrival_time=time.time())


@pytest.fixture
def config():
    """Get the current configuration"""
    return get_config()
