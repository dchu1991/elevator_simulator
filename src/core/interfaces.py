"""
Interfaces and Protocols for Dependency Injection
=================================================

Defines clear contracts between components to enable dependency injection,
improve testability, and reduce coupling.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from dataclasses import dataclass


@dataclass
class ElevatorConfig:
    """Configuration for elevator behavior - injected instead of using singleton"""

    # Building parameters
    num_floors: int = 20
    num_elevators: int = 4
    elevator_capacity: int = 8
    elevator_speed: float = 2.0
    floor_height_meters: float = 3.5

    # Strategy parameters
    distance_weight: float = 1.0
    full_penalty: int = 50
    same_direction_bonus: int = -5
    opposite_direction_penalty: int = 20
    load_factor_weight: int = 20
    idle_bonus: int = -8

    # Traffic parameters
    base_arrival_rate: float = 20.0
    rush_multiplier: float = 3.0
    lunch_multiplier: float = 2.0
    night_multiplier: float = 0.2
    enable_realistic_visitors: bool = True

    # Simulation timing
    control_loop_interval: float = 0.1  # seconds
    traffic_check_interval: float = 1.0  # seconds
    movement_delay_factor: float = 0.5
    stats_recording_interval: float = 10.0

    # Behavior
    allow_direction_change_when_empty: bool = True
    prefer_nearest_call: bool = True
    max_wait_time_before_reassign: float = 300.0
    enable_load_balancing: bool = True


class ElevatorAssignmentStrategy(ABC):
    """Abstract strategy for assigning elevators to requests"""

    @abstractmethod
    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """
        Assign an elevator to handle a request.

        Args:
            elevators: List of available elevators
            request_floor: Floor where request originated
            direction: Direction of travel (UP/DOWN)
            config: Configuration for scoring

        Returns:
            Index of assigned elevator, or None if no suitable elevator
        """
        pass


class IPersonGenerator(Protocol):
    """Protocol for generating people in the simulation"""

    def generate_person(self):
        """Generate a new person entering the building"""
        ...

    def create_return_journey(self, person) -> Optional:
        """Create a return journey for a visitor"""
        ...


class ITrafficManager(Protocol):
    """Protocol for managing traffic patterns"""

    def start(self) -> None:
        """Start generating traffic"""
        ...

    def stop(self) -> None:
        """Stop generating traffic"""
        ...

    def get_current_rate(self) -> float:
        """Get current traffic generation rate"""
        ...


class IStatisticsCollector(Protocol):
    """Protocol for collecting simulation statistics"""

    def record_pickup(self, person, wait_time: float) -> None:
        """Record when a person is picked up"""
        ...

    def record_dropoff(self, person, journey_time: float) -> None:
        """Record when a person reaches destination"""
        ...

    def get_statistics(self) -> dict:
        """Get current statistics"""
        ...


class IEventBus(Protocol):
    """Protocol for event-based communication between components"""

    def subscribe(self, event_type: str, handler) -> None:
        """Subscribe to an event type"""
        ...

    def publish(self, event_type: str, data: dict) -> None:
        """Publish an event"""
        ...

    def unsubscribe(self, event_type: str, handler) -> None:
        """Unsubscribe from an event type"""
        ...
