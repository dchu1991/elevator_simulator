"""
Elevator Assignment Strategies
==============================

Different strategies for assigning elevators to requests.
Demonstrates Strategy Pattern + Dependency Injection.
"""

from typing import List, Optional
from src.core.interfaces import ElevatorAssignmentStrategy, ElevatorConfig
from src.core.elevator_simulator import Direction, ElevatorState


class NearestCarStrategy(ElevatorAssignmentStrategy):
    """Assign nearest available elevator (current default behavior)"""

    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """Assign based on proximity and current load"""
        best_elevator = None
        best_score = float("inf")

        for i, elevator in enumerate(elevators):
            score = self._calculate_score(elevator, request_floor, direction, config)

            if score < best_score:
                best_score = score
                best_elevator = i

        return best_elevator

    def _calculate_score(
        self, elevator, request_floor: int, direction, config: ElevatorConfig
    ) -> float:
        """Calculate assignment score (lower is better)"""
        # Can't assign if full
        if elevator.is_full:
            return config.full_penalty

        distance = abs(elevator.current_floor - request_floor)
        score = distance * config.distance_weight

        # Bonus if elevator is idle
        if elevator.state == ElevatorState.IDLE:
            score += config.idle_bonus

        # Bonus if going same direction and not too busy
        elif (
            elevator.direction == direction
            and elevator.passenger_count < elevator.capacity * 0.7
        ):
            score += config.same_direction_bonus

        # Penalty if going opposite direction
        elif elevator.direction != Direction.IDLE and elevator.direction != direction:
            score += config.opposite_direction_penalty

        # Add load factor
        if config.enable_load_balancing:
            load_factor = elevator.passenger_count / elevator.capacity
            score += load_factor * config.load_factor_weight

        return score


class SCANStrategy(ElevatorAssignmentStrategy):
    """SCAN algorithm - elevator continues in direction until no more requests"""

    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """Assign elevator using SCAN algorithm"""
        # Find elevators moving in same direction
        same_direction = [
            (i, e)
            for i, e in enumerate(elevators)
            if e.direction == direction and not e.is_full
        ]

        if same_direction:
            # Prefer elevator approaching from correct direction
            if direction.value == "UP":
                candidates = [
                    (i, e)
                    for i, e in same_direction
                    if e.current_floor <= request_floor
                ]
            else:
                candidates = [
                    (i, e)
                    for i, e in same_direction
                    if e.current_floor >= request_floor
                ]

            if candidates:
                # Choose closest one
                return min(
                    candidates, key=lambda x: abs(x[1].current_floor - request_floor)
                )[0]

        # Fall back to nearest idle elevator
        idle_elevators = [
            (i, e)
            for i, e in enumerate(elevators)
            if e.state == ElevatorState.IDLE and not e.is_full
        ]

        if idle_elevators:
            return min(
                idle_elevators, key=lambda x: abs(x[1].current_floor - request_floor)
            )[0]

        # Last resort: nearest available
        available = [(i, e) for i, e in enumerate(elevators) if not e.is_full]
        if available:
            return min(
                available, key=lambda x: abs(x[1].current_floor - request_floor)
            )[0]

        return None


class RoundRobinStrategy(ElevatorAssignmentStrategy):
    """Simple round-robin assignment for load balancing"""

    def __init__(self):
        self.last_assigned = -1

    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """Assign next elevator in round-robin fashion"""
        num_elevators = len(elevators)

        for _ in range(num_elevators):
            self.last_assigned = (self.last_assigned + 1) % num_elevators
            elevator = elevators[self.last_assigned]

            if not elevator.is_full:
                return self.last_assigned

        return None  # All elevators full
