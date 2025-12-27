"""
Test elevator movement and request handling
"""

import pytest
import time
from src.core.simulation_engine import SimulationEngine


@pytest.mark.integration
def test_elevator_responds_to_simple_request(small_simulation):
    """Test that elevator responds to a simple request and delivers passenger"""
    sim = small_simulation
    sim.start_simulation()

    elevator = sim.building.elevators[0]
    initial_floor = elevator.current_floor

    # Add request
    sim.add_manual_request(1, 5)

    # Wait for delivery
    max_wait = 10  # seconds
    delivered = False
    for _ in range(max_wait * 2):
        time.sleep(0.5)
        stats = sim.get_current_statistics()
        if stats["total_people_completed"] > 0:
            delivered = True
            break

    assert delivered, "Elevator should deliver the passenger"
    assert elevator.current_floor != initial_floor, "Elevator should have moved"


@pytest.mark.integration
def test_elevator_handles_multiple_requests(small_simulation):
    """Test that elevator handles multiple requests correctly"""
    sim = small_simulation
    sim.start_simulation()

    # Add multiple requests
    sim.add_manual_request(1, 5)
    sim.add_manual_request(2, 4)
    sim.add_manual_request(3, 1)

    # Wait for completion
    max_wait = 20  # seconds
    for _ in range(max_wait * 2):
        time.sleep(0.5)
        stats = sim.get_current_statistics()
        if stats["total_people_completed"] >= 3:
            break

    stats = sim.get_current_statistics()
    assert stats["total_people_completed"] >= 3, "All passengers should be delivered"


@pytest.mark.integration
def test_elevator_moves_between_floors(single_elevator_building):
    """Test basic elevator movement between floors"""
    building = single_elevator_building
    elevator = building.elevators[0]

    initial_floor = elevator.current_floor

    # Directly test move_to_floor
    target_floor = 4 if initial_floor != 4 else 1
    travel_time = elevator.move_to_floor(target_floor)

    assert elevator.current_floor == target_floor, "Elevator should reach target floor"
    assert travel_time > 0, "Travel time should be positive"


@pytest.mark.unit
def test_elevator_capacity(simple_building):
    """Test elevator capacity limits"""
    elevator = simple_building.elevators[0]

    assert not elevator.is_full, "New elevator should not be full"
    assert elevator.passenger_count == 0, "New elevator should have no passengers"

    # Test capacity
    assert hasattr(elevator, "capacity"), "Elevator should have capacity attribute"
    assert elevator.capacity > 0, "Capacity should be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
