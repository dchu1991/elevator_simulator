"""
Advanced Elevator Assignment Strategies
=======================================

More sophisticated strategies for elevator assignment:
- LOOK Algorithm
- Destination Dispatch
- ML-based (simple heuristic learning)
"""

from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from src.core.interfaces import ElevatorAssignmentStrategy, ElevatorConfig
from src.core.elevator_simulator import ElevatorState
from src.core.strategies import NearestCarStrategy


class LOOKStrategy(ElevatorAssignmentStrategy):
    """
    LOOK algorithm - Like SCAN but reverses at last request, not at building end.

    More efficient than SCAN as it doesn't travel to floors with no requests.
    """

    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """Assign elevator using LOOK algorithm"""
        best_elevator = None
        best_score = float("inf")

        for i, elevator in enumerate(elevators):
            if elevator.is_full:
                continue

            score = self._calculate_look_score(
                elevator, request_floor, direction, config
            )

            if score < best_score:
                best_score = score
                best_elevator = i

        return best_elevator

    def _calculate_look_score(
        self, elevator, request_floor: int, direction, config: ElevatorConfig
    ) -> float:
        """Calculate LOOK score - prefer elevators serving requests in same direction"""
        distance = abs(elevator.current_floor - request_floor)

        # Idle elevator - very good
        if elevator.state == ElevatorState.IDLE:
            return distance * 0.5  # Low score = high priority

        # Moving in same direction and will pass this floor
        if elevator.direction == direction:
            if direction.value == "UP" and elevator.current_floor <= request_floor:
                # Will pick up on the way
                return distance * 0.7
            elif direction.value == "DOWN" and elevator.current_floor >= request_floor:
                # Will pick up on the way
                return distance * 0.7

        # Moving opposite direction or won't pass this floor
        # Will need to reverse first
        return distance * 2.0 + 100  # Higher score = lower priority


class DestinationDispatchStrategy(ElevatorAssignmentStrategy):
    """
    Destination Dispatch - Group passengers by destination floor.

    Modern elevators ask for destination floor before boarding,
    allowing optimal grouping of passengers.
    """

    def __init__(self):
        # Track destination floor requests
        self.destination_groups: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        # Track which elevator is assigned to which destination group
        self.elevator_destinations: Dict[int, List[int]] = defaultdict(list)

    def assign_elevator(
        self,
        elevators: List,
        request_floor: int,
        direction,
        config: ElevatorConfig,
        destination_floor: Optional[int] = None,
    ) -> Optional[int]:
        """
        Assign elevator based on destination grouping.

        If destination_floor is provided, try to group with others going same direction.
        """
        if destination_floor is None:
            # Fallback to simple nearest if destination unknown
            return self._assign_nearest(elevators, request_floor, config)

        # Try to find elevator already going to nearby destination
        best_elevator = self._find_grouped_elevator(
            elevators, request_floor, destination_floor, direction, config
        )

        if best_elevator is not None:
            return best_elevator

        # Otherwise assign nearest available
        return self._assign_nearest(elevators, request_floor, config)

    def _find_grouped_elevator(
        self, elevators, request_floor, destination_floor, direction, config
    ) -> Optional[int]:
        """Find elevator serving similar destinations"""
        for i, elevator in enumerate(elevators):
            if elevator.is_full:
                continue

            # Check if elevator has passengers going to nearby floors
            if i in self.elevator_destinations:
                destinations = self.elevator_destinations[i]
                # If any destination within 3 floors, group together
                if any(abs(dest - destination_floor) <= 3 for dest in destinations):
                    # Also check elevator is going right direction
                    if (
                        elevator.direction == direction
                        or elevator.state == ElevatorState.IDLE
                    ):
                        return i

        return None

    def _assign_nearest(self, elevators, request_floor, config) -> Optional[int]:
        """Fallback to nearest available elevator"""
        available = [(i, e) for i, e in enumerate(elevators) if not e.is_full]

        if not available:
            return None

        # Prefer idle elevators
        idle = [(i, e) for i, e in available if e.state == ElevatorState.IDLE]

        if idle:
            return min(idle, key=lambda x: abs(x[1].current_floor - request_floor))[0]

        return min(available, key=lambda x: abs(x[1].current_floor - request_floor))[0]

    def register_destination(
        self, elevator_idx: int, request_floor: int, destination_floor: int
    ):
        """Register a destination for tracking"""
        self.destination_groups[destination_floor].append((elevator_idx, request_floor))
        if destination_floor not in self.elevator_destinations[elevator_idx]:
            self.elevator_destinations[elevator_idx].append(destination_floor)

    def clear_destination(self, elevator_idx: int, destination_floor: int):
        """Clear a destination when reached"""
        if (
            elevator_idx in self.elevator_destinations
            and destination_floor in self.elevator_destinations[elevator_idx]
        ):
            self.elevator_destinations[elevator_idx].remove(destination_floor)


class MLBasedStrategy(ElevatorAssignmentStrategy):
    """
    ML-based strategy using simple online learning.

    Learns from past assignments which strategies work best for different scenarios.
    Uses a simple weighted voting system based on historical performance.
    """

    def __init__(self):
        # Track performance of different assignment decisions
        self.assignment_history: List[Dict] = []
        self.strategy_weights = {
            "nearest": 1.0,
            "same_direction": 1.0,
            "idle_preference": 1.0,
            "load_balanced": 1.0,
        }
        self.learning_rate = 0.1

    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """Assign elevator using learned weights"""
        best_elevator = None
        best_score = float("inf")

        for i, elevator in enumerate(elevators):
            if elevator.is_full:
                continue

            score = self._calculate_ml_score(elevator, request_floor, direction, config)

            if score < best_score:
                best_score = score
                best_elevator = i

        # Record this assignment for learning
        if best_elevator is not None:
            self._record_assignment(best_elevator, request_floor, elevators)

        return best_elevator

    def _calculate_ml_score(
        self, elevator, request_floor: int, direction, config: ElevatorConfig
    ) -> float:
        """Calculate score using learned weights"""
        score = 0.0

        # Distance component (weighted)
        distance = abs(elevator.current_floor - request_floor)
        score += distance * self.strategy_weights["nearest"]

        # Idle bonus (weighted)
        if elevator.state == ElevatorState.IDLE:
            score -= 10 * self.strategy_weights["idle_preference"]

        # Same direction bonus (weighted)
        if elevator.direction == direction:
            score -= 5 * self.strategy_weights["same_direction"]

        # Load balancing (weighted)
        if config.enable_load_balancing:
            load_factor = elevator.passenger_count / elevator.capacity
            score += load_factor * 15 * self.strategy_weights["load_balanced"]

        return score

    def _record_assignment(self, elevator_idx: int, request_floor: int, elevators):
        """Record assignment for future learning"""
        elevator = elevators[elevator_idx]

        self.assignment_history.append(
            {
                "elevator_idx": elevator_idx,
                "request_floor": request_floor,
                "elevator_floor": elevator.current_floor,
                "elevator_state": elevator.state,
                "elevator_load": elevator.passenger_count / elevator.capacity,
            }
        )

        # Keep history limited
        if len(self.assignment_history) > 1000:
            self.assignment_history.pop(0)

    def update_from_feedback(self, wait_time: float, assignment_idx: int):
        """
        Update strategy weights based on performance feedback.

        Args:
            wait_time: How long person waited
            assignment_idx: Index in assignment_history
        """
        if assignment_idx >= len(self.assignment_history):
            return

        assignment = self.assignment_history[assignment_idx]

        # Good performance (low wait time) - reinforce
        if wait_time < 10:
            reward = 1.0
        # Acceptable
        elif wait_time < 30:
            reward = 0.5
        # Poor
        else:
            reward = -0.5

        # Update weights based on what contributed to this assignment
        if assignment["elevator_state"] == ElevatorState.IDLE:
            self.strategy_weights["idle_preference"] += self.learning_rate * reward

        if abs(assignment["elevator_floor"] - assignment["request_floor"]) < 5:
            self.strategy_weights["nearest"] += self.learning_rate * reward

        if assignment["elevator_load"] < 0.5:
            self.strategy_weights["load_balanced"] += self.learning_rate * reward

        # Ensure weights stay positive
        for key in self.strategy_weights:
            self.strategy_weights[key] = max(0.1, self.strategy_weights[key])

    def get_learned_weights(self) -> Dict[str, float]:
        """Get current learned weights"""
        return self.strategy_weights.copy()

    def reset_learning(self):
        """Reset learned weights to defaults"""
        self.strategy_weights = {
            "nearest": 1.0,
            "same_direction": 1.0,
            "idle_preference": 1.0,
            "load_balanced": 1.0,
        }
        self.assignment_history.clear()


class AdaptiveStrategy(ElevatorAssignmentStrategy):
    """
    Adaptive strategy that switches between different strategies based on traffic patterns.

    - Light traffic: Use simple nearest
    - Heavy traffic: Use LOOK algorithm
    - Rush hour: Use destination dispatch
    """

    def __init__(self):
        self.nearest = NearestCarStrategy()
        self.look = LOOKStrategy()
        # Track recent request rate
        self.recent_requests = []
        self.max_history = 100

    def assign_elevator(
        self, elevators: List, request_floor: int, direction, config: ElevatorConfig
    ) -> Optional[int]:
        """Assign elevator using adaptive strategy selection"""
        # Record request
        import time

        self.recent_requests.append(time.time())
        if len(self.recent_requests) > self.max_history:
            self.recent_requests.pop(0)

        # Calculate request rate (requests per minute)
        if len(self.recent_requests) >= 2:
            time_span = self.recent_requests[-1] - self.recent_requests[0]
            if time_span > 0:
                request_rate = len(self.recent_requests) / time_span * 60
            else:
                request_rate = 0
        else:
            request_rate = 0

        # Choose strategy based on traffic
        if request_rate < 10:
            # Light traffic - use simple nearest
            return self.nearest.assign_elevator(
                elevators, request_floor, direction, config
            )
        else:
            # Heavy traffic - use LOOK
            return self.look.assign_elevator(
                elevators, request_floor, direction, config
            )
