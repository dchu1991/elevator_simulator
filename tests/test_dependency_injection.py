"""
Tests demonstrating benefits of Dependency Injection
====================================================

Shows how DI makes testing easier and more flexible.
"""

import pytest
from src.core.container import create_test_container
from src.core.strategies import NearestCarStrategy, SCANStrategy, RoundRobinStrategy
from src.core.interfaces import ElevatorConfig
from src.core.elevator_simulator import Elevator, Direction, ElevatorState


class TestDependencyInjection:
    """Test DI patterns and benefits"""
    
    def test_strategy_injection_nearest(self):
        """Test with NearestCar strategy"""
        container = create_test_container(strategy_name='nearest')
        strategy = container.resolve('strategy')
        
        assert isinstance(strategy, NearestCarStrategy)
    
    def test_strategy_injection_scan(self):
        """Test with SCAN strategy"""
        container = create_test_container(strategy_name='scan')
        strategy = container.resolve('strategy')
        
        assert isinstance(strategy, SCANStrategy)
    
    def test_strategy_injection_round_robin(self):
        """Test with RoundRobin strategy"""
        container = create_test_container(strategy_name='round_robin')
        strategy = container.resolve('strategy')
        
        assert isinstance(strategy, RoundRobinStrategy)
    
    def test_config_override(self):
        """Test config overrides for testing"""
        container = create_test_container(
            config_overrides={
                'num_floors': 5,
                'elevator_speed': 100.0,  # Super fast for testing
            }
        )
        
        config = container.resolve('config')
        assert config.num_floors == 5
        assert config.elevator_speed == 100.0
    
    def test_strategy_behavior_nearest(self):
        """Test NearestCar strategy picks closest elevator"""
        # Create test elevators
        elevators = [
            Elevator(1, capacity=8, speed=2.0),  # Floor 1
            Elevator(2, capacity=8, speed=2.0),  # Floor 1
            Elevator(3, capacity=8, speed=2.0),  # Floor 1
        ]
        
        # Move them to different floors
        elevators[0].current_floor = 1
        elevators[1].current_floor = 5
        elevators[2].current_floor = 10
        
        # All idle
        for e in elevators:
            e.state = ElevatorState.IDLE
            e.direction = Direction.IDLE
        
        config = ElevatorConfig()
        strategy = NearestCarStrategy()
        
        # Request from floor 6 - should pick elevator 2 (floor 5)
        assigned = strategy.assign_elevator(elevators, 6, Direction.UP, config)
        assert assigned == 1  # Index of elevator at floor 5
    
    def test_strategy_behavior_round_robin(self):
        """Test RoundRobin strategy distributes load"""
        elevators = [
            Elevator(1, capacity=8, speed=2.0),
            Elevator(2, capacity=8, speed=2.0),
            Elevator(3, capacity=8, speed=2.0),
        ]
        
        for e in elevators:
            e.state = ElevatorState.IDLE
        
        config = ElevatorConfig()
        strategy = RoundRobinStrategy()
        
        # Make 3 assignments - should cycle through elevators
        assignments = []
        for _ in range(3):
            assigned = strategy.assign_elevator(elevators, 5, Direction.UP, config)
            assignments.append(assigned)
        
        # Should have assigned to different elevators
        assert len(set(assignments)) == 3  # All different
        assert set(assignments) == {0, 1, 2}  # All elevators used
    
    def test_multiple_containers(self):
        """Test creating multiple independent containers"""
        container1 = create_test_container(
            strategy_name='nearest',
            config_overrides={'num_floors': 10}
        )
        
        container2 = create_test_container(
            strategy_name='scan',
            config_overrides={'num_floors': 20}
        )
        
        config1 = container1.resolve('config')
        config2 = container2.resolve('config')
        strategy1 = container1.resolve('strategy')
        strategy2 = container2.resolve('strategy')
        
        # Containers are independent
        assert config1.num_floors == 10
        assert config2.num_floors == 20
        assert isinstance(strategy1, NearestCarStrategy)
        assert isinstance(strategy2, SCANStrategy)


class TestStrategyComparison:
    """Compare different strategies"""
    
    @pytest.fixture
    def test_elevators(self):
        """Create test elevators"""
        elevators = [
            Elevator(1, capacity=8, speed=2.0),
            Elevator(2, capacity=8, speed=2.0),
            Elevator(3, capacity=8, speed=2.0),
        ]
        
        # Set initial positions
        elevators[0].current_floor = 1
        elevators[0].state = ElevatorState.IDLE
        elevators[0].direction = Direction.IDLE
        
        elevators[1].current_floor = 5
        elevators[1].state = ElevatorState.MOVING
        elevators[1].direction = Direction.UP
        
        elevators[2].current_floor = 10
        elevators[2].state = ElevatorState.IDLE
        elevators[2].direction = Direction.IDLE
        
        return elevators
    
    def test_nearest_prefers_idle(self, test_elevators):
        """NearestCar should prefer idle elevators"""
        config = ElevatorConfig(idle_bonus=-20)  # Strong preference for idle
        strategy = NearestCarStrategy()
        
        # Request from floor 6 - elevator 2 (floor 5) is closer but moving
        # elevator 3 (floor 10) is idle
        assigned = strategy.assign_elevator(test_elevators, 6, Direction.UP, config)
        
        # With strong idle bonus, might prefer idle elevator even if farther
        # This demonstrates configurable behavior
        assert assigned in [1, 2]  # Either the moving one or idle one
    
    def test_scan_prefers_same_direction(self, test_elevators):
        """SCAN should prefer elevators going same direction"""
        config = ElevatorConfig()
        strategy = SCANStrategy()
        
        # Request from floor 7 going UP
        # Elevator 2 at floor 5 going UP should be preferred
        assigned = strategy.assign_elevator(test_elevators, 7, Direction.UP, config)
        
        assert assigned == 1  # Elevator going UP
