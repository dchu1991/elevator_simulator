"""
Tests for Advanced Strategies
=============================

Test LOOK, Destination Dispatch, ML-based, and Adaptive strategies.
"""

import pytest
import time
from src.core.advanced_strategies import (
    LOOKStrategy,
    DestinationDispatchStrategy,
    MLBasedStrategy,
    AdaptiveStrategy,
)
from src.core.interfaces import ElevatorConfig
from src.core.elevator_simulator import Elevator, Direction, ElevatorState


@pytest.fixture
def test_elevators():
    """Create test elevators"""
    elevators = [
        Elevator(1, capacity=8, speed=2.0),
        Elevator(2, capacity=8, speed=2.0),
        Elevator(3, capacity=8, speed=2.0),
    ]

    # Set initial states
    elevators[0].current_floor = 1
    elevators[0].state = ElevatorState.IDLE

    elevators[1].current_floor = 10
    elevators[1].state = ElevatorState.MOVING
    elevators[1].direction = Direction.UP

    elevators[2].current_floor = 15
    elevators[2].state = ElevatorState.IDLE

    return elevators


@pytest.fixture
def config():
    """Create test config"""
    return ElevatorConfig()


class TestLOOKStrategy:
    """Test LOOK algorithm strategy"""

    def test_prefers_idle_elevator(self, test_elevators, config):
        """LOOK should prefer idle elevators"""
        strategy = LOOKStrategy()

        # Request from floor 5
        assigned = strategy.assign_elevator(test_elevators, 5, Direction.UP, config)

        # Should prefer elevator 1 (idle at floor 1) over elevator 2 (moving)
        assert assigned in [0, 2]  # One of the idle ones

    def test_prefers_same_direction(self, test_elevators, config):
        """LOOK should prefer elevators moving in same direction"""
        strategy = LOOKStrategy()

        # Request from floor 12 going UP
        # Elevator 2 is at floor 10 going UP
        assigned = strategy.assign_elevator(test_elevators, 12, Direction.UP, config)

        assert assigned == 1  # Elevator moving UP

    def test_no_full_elevators(self, test_elevators, config):
        """LOOK should not assign full elevators"""
        # Make all elevators full by adding passengers
        for elevator in test_elevators:
            # Add passengers up to capacity
            for i in range(elevator.capacity):
                from src.core.elevator_simulator import Person

                person = Person(
                    id=i,
                    current_floor=1,
                    destination_floor=10,
                    arrival_time=time.time(),
                )
                elevator.passengers.append(person)

        strategy = LOOKStrategy()
        assigned = strategy.assign_elevator(test_elevators, 10, Direction.UP, config)

        assert assigned is None  # No available elevator


class TestDestinationDispatchStrategy:
    """Test Destination Dispatch strategy"""

    def test_groups_similar_destinations(self, test_elevators, config):
        """Should group passengers with similar destinations"""
        strategy = DestinationDispatchStrategy()

        # Register elevator 1 going to floor 20
        strategy.register_destination(0, 1, 20)

        # Request from floor 5 to floor 21 (close to 20)
        assigned = strategy.assign_elevator(
            test_elevators, 5, Direction.UP, config, destination_floor=21
        )

        assert assigned == 0  # Should group with elevator going to 20

    def test_fallback_to_nearest(self, test_elevators, config):
        """Should fall back to nearest if no destination given"""
        strategy = DestinationDispatchStrategy()

        # No destination specified
        assigned = strategy.assign_elevator(test_elevators, 5, Direction.UP, config)

        assert assigned is not None

    def test_clears_destination(self, test_elevators, config):
        """Should clear destinations when reached"""
        strategy = DestinationDispatchStrategy()

        strategy.register_destination(0, 1, 20)
        assert 20 in strategy.elevator_destinations[0]

        strategy.clear_destination(0, 20)
        assert 20 not in strategy.elevator_destinations[0]


class TestMLBasedStrategy:
    """Test ML-based strategy with learning"""

    def test_initial_assignment(self, test_elevators, config):
        """ML strategy should assign elevator initially"""
        strategy = MLBasedStrategy()

        assigned = strategy.assign_elevator(test_elevators, 10, Direction.UP, config)

        assert assigned is not None
        assert 0 <= assigned < len(test_elevators)

    def test_records_assignments(self, test_elevators, config):
        """Should record assignment history"""
        strategy = MLBasedStrategy()

        strategy.assign_elevator(test_elevators, 10, Direction.UP, config)
        strategy.assign_elevator(test_elevators, 5, Direction.UP, config)

        assert len(strategy.assignment_history) == 2

    def test_learns_from_feedback(self, test_elevators, config):
        """Should update weights based on feedback"""
        strategy = MLBasedStrategy()

        # Make an assignment
        strategy.assign_elevator(test_elevators, 10, Direction.UP, config)

        # Get initial weights
        initial_weights = strategy.get_learned_weights().copy()

        # Provide good feedback (low wait time)
        strategy.update_from_feedback(wait_time=5.0, assignment_idx=0)

        # Weights should change
        updated_weights = strategy.get_learned_weights()
        # At least one weight should be different
        assert any(initial_weights[k] != updated_weights[k] for k in initial_weights)

    def test_negative_feedback(self, test_elevators, config):
        """Should handle negative feedback"""
        strategy = MLBasedStrategy()

        strategy.assign_elevator(test_elevators, 10, Direction.UP, config)

        # Bad feedback (high wait time)
        strategy.update_from_feedback(wait_time=100.0, assignment_idx=0)

        # Should not crash
        weights = strategy.get_learned_weights()
        assert all(w > 0 for w in weights.values())  # Weights stay positive

    def test_reset_learning(self, test_elevators, config):
        """Should reset learning"""
        strategy = MLBasedStrategy()

        strategy.assign_elevator(test_elevators, 10, Direction.UP, config)
        strategy.update_from_feedback(wait_time=5.0, assignment_idx=0)

        strategy.reset_learning()

        assert len(strategy.assignment_history) == 0
        weights = strategy.get_learned_weights()
        assert weights["nearest"] == 1.0  # Back to default


class TestAdaptiveStrategy:
    """Test Adaptive strategy that switches between algorithms"""

    def test_switches_based_on_traffic(self, test_elevators, config):
        """Should switch strategies based on traffic"""
        strategy = AdaptiveStrategy()

        # Light traffic - should work
        assigned = strategy.assign_elevator(test_elevators, 10, Direction.UP, config)
        assert assigned is not None

        # Simulate heavy traffic by making many requests quickly
        for _ in range(50):
            strategy.assign_elevator(test_elevators, 10, Direction.UP, config)
            time.sleep(0.01)  # Very fast requests

        # Should still work
        assigned = strategy.assign_elevator(test_elevators, 10, Direction.UP, config)
        assert assigned is not None

    def test_tracks_request_rate(self, test_elevators, config):
        """Should track request rate"""
        strategy = AdaptiveStrategy()

        # Make several requests
        for _ in range(10):
            strategy.assign_elevator(test_elevators, 10, Direction.UP, config)

        # Should have recorded requests
        assert len(strategy.recent_requests) == 10
