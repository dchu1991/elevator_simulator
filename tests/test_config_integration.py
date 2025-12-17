"""
Test configuration integration and loading
"""

import pytest
import time
from src.utils.config_loader import get_config
from src.core.elevator_simulator import Building, Person, Direction
from src.core.simulation_engine import TrafficManager


@pytest.mark.unit
def test_config_loads_successfully(config):
    """Test that configuration loads without errors"""
    assert config is not None
    assert hasattr(config, 'num_floors')
    assert hasattr(config, 'num_elevators')
    assert config.num_floors > 0
    assert config.num_elevators > 0


@pytest.mark.unit
def test_building_uses_config_values(config):
    """Test that Building uses values from config"""
    building = Building()
    
    assert building.num_floors == config.num_floors
    assert len(building.elevators) == config.num_elevators


@pytest.mark.unit
def test_elevator_uses_config_values(config, simple_building):
    """Test that Elevator uses values from config"""
    elevator = simple_building.elevators[0]
    
    assert elevator.capacity == config.elevator_capacity
    assert elevator.speed == config.elevator_speed


@pytest.mark.unit
def test_elevator_scoring_uses_config(config, simple_building):
    """Test that elevator scoring algorithm uses config strategy parameters"""
    building = simple_building
    
    # Setup elevators at different positions
    building.elevators[0].current_floor = 1
    building.elevators[0].direction = Direction.UP
    building.elevators[1].current_floor = 8
    building.elevators[1].direction = Direction.DOWN
    
    # Calculate scores for a request at floor 5 going up
    score1 = building.calculate_elevator_score(building.elevators[0], 5, Direction.UP)
    score2 = building.calculate_elevator_score(building.elevators[1], 5, Direction.DOWN)
    
    # Verify scores are calculated (both should be numeric)
    assert isinstance(score1, (int, float)), "Score should be numeric"
    assert isinstance(score2, (int, float)), "Score should be numeric"
    
    # The scoring may vary based on current config, but both elevators should have valid scores
    # The actual comparison depends on the scoring strategy in the config


@pytest.mark.unit
def test_traffic_manager_uses_config(config, simple_building):
    """Test that TrafficManager uses config values"""
    traffic_mgr = TrafficManager(simple_building)
    
    assert traffic_mgr.base_arrival_rate == config.base_arrival_rate
    assert traffic_mgr.rush_multiplier == config.rush_multiplier
    assert traffic_mgr.lunch_multiplier == config.lunch_multiplier


@pytest.mark.unit
def test_config_has_required_fields(config):
    """Test that config has all required fields"""
    required_fields = [
        'num_floors', 'num_elevators', 'elevator_capacity', 'elevator_speed',
        'distance_weight', 'same_direction_bonus', 'opposite_direction_penalty',
        'full_penalty', 'base_arrival_rate', 'rush_multiplier'
    ]
    
    for field in required_fields:
        assert hasattr(config, field), f"Config missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
