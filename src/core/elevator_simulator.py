"""
Elevator Simulator for a Tall Mall
==================================

This module implements a comprehensive elevator simulation system
for a multi-story mall. Features include multiple elevators,
intelligent scheduling, person generation, and real-time visualization.
"""

import random
import time
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from src.utils.config_loader import get_config
from src.core.interfaces import ElevatorAssignmentStrategy, ElevatorConfig


class Direction(Enum):
    """Elevator movement directions"""

    UP = "UP"
    DOWN = "DOWN"
    IDLE = "IDLE"


class ElevatorState(Enum):
    """Elevator operational states"""

    IDLE = "IDLE"
    MOVING = "MOVING"
    LOADING = "LOADING"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class Person:
    """Represents a person in the mall wanting to use elevators"""

    id: int
    current_floor: int
    destination_floor: int
    arrival_time: float
    boarding_time: Optional[float] = None
    visit_duration: Optional[float] = None  # Time to spend at destination
    is_leaving: bool = False  # True when returning to exit the building
    visit_start_time: Optional[float] = None  # When they reached their destination

    @property
    def direction(self) -> Direction:
        """Get the direction this person wants to travel"""
        if self.destination_floor > self.current_floor:
            return Direction.UP
        elif self.destination_floor < self.current_floor:
            return Direction.DOWN
        return Direction.IDLE

    @property
    def wait_time(self) -> float:
        """Calculate how long this person has been waiting"""
        current_time = time.time()
        if self.boarding_time:
            return self.boarding_time - self.arrival_time
        return current_time - self.arrival_time


class Elevator:
    """Represents an individual elevator in the mall"""

    def __init__(self, elevator_id: int, capacity: int = None, speed: float = None):
        config = get_config()
        self.id = elevator_id
        self.capacity = capacity if capacity is not None else config.elevator_capacity
        self.speed = speed if speed is not None else config.elevator_speed
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.state = ElevatorState.IDLE

        # Passengers and requests
        self.passengers: List[Person] = []
        self.up_requests: Set[int] = set()  # Floors with up requests
        self.down_requests: Set[int] = set()  # Floors with down requests
        self.destination_floors: Set[int] = set()  # Internal destination requests

        # Statistics
        self.total_passengers_served = 0
        self.total_distance_traveled = 0
        self.last_position_time = time.time()

    @property
    def is_full(self) -> bool:
        """Check if elevator is at capacity"""
        return len(self.passengers) >= self.capacity

    @property
    def passenger_count(self) -> int:
        """Get current number of passengers"""
        return len(self.passengers)

    def add_request(self, floor: int, direction: Direction):
        """Add a request for the elevator to visit a floor"""
        if direction == Direction.UP:
            self.up_requests.add(floor)
        elif direction == Direction.DOWN:
            self.down_requests.add(floor)

    def add_destination(self, floor: int):
        """Add an internal destination (passenger's target floor)"""
        self.destination_floors.add(floor)

    def board_passenger(self, person: Person) -> bool:
        """Try to board a passenger. Returns True if successful."""
        if self.is_full:
            return False

        person.boarding_time = time.time()
        self.passengers.append(person)
        self.add_destination(person.destination_floor)
        return True

    def unboard_passengers(self, floor: int) -> List[Person]:
        """Remove passengers who have reached their destination"""
        passengers_leaving = [
            p for p in self.passengers if p.destination_floor == floor
        ]
        self.passengers = [p for p in self.passengers if p.destination_floor != floor]

        # Mark visit start time for passengers reaching their destination
        current_time = time.time()
        for passenger in passengers_leaving:
            if not passenger.is_leaving and passenger.visit_duration:
                passenger.visit_start_time = current_time

        if floor in self.destination_floors:
            self.destination_floors.remove(floor)

        self.total_passengers_served += len(passengers_leaving)
        return passengers_leaving

    def has_requests_in_direction(
        self, direction: Direction, current_floor: int
    ) -> bool:
        """Check if there are any requests in the given direction"""
        if direction == Direction.UP:
            up_floors = [f for f in self.up_requests if f > current_floor]
            dest_floors = [f for f in self.destination_floors if f > current_floor]
            return bool(up_floors or dest_floors)
        elif direction == Direction.DOWN:
            down_floors = [f for f in self.down_requests if f < current_floor]
            dest_floors = [f for f in self.destination_floors if f < current_floor]
            return bool(down_floors or dest_floors)
        return False

    def get_next_stop(self) -> Optional[int]:
        """Determine the next floor this elevator should stop at"""
        current = self.current_floor

        # Find next stop in current direction (NOT including current floor)
        if self.direction == Direction.UP:
            candidates = [f for f in self.destination_floors if f > current]
            candidates.extend([f for f in self.up_requests if f > current])
            if candidates:
                return min(candidates)
        elif self.direction == Direction.DOWN:
            candidates = [f for f in self.destination_floors if f < current]
            candidates.extend([f for f in self.down_requests if f < current])
            if candidates:
                return max(candidates)
        elif self.direction == Direction.IDLE:
            # When idle, find ANY destination or request (excluding current floor)
            if self.destination_floors:
                if candidates := [f for f in self.destination_floors if f != current]:
                    return min(candidates, key=lambda f: abs(f - current))
            if all_requests := [
                f
                for f in list(self.up_requests) + list(self.down_requests)
                if f != current
            ]:
                return min(all_requests, key=lambda f: abs(f - current))
        return None

    def update_direction(self):
        """Update elevator direction based on pending requests"""
        current = self.current_floor

        # If we have requests in current direction, continue
        if self.has_requests_in_direction(self.direction, current):
            return

        # Change direction if we have requests in the opposite direction
        if self.direction == Direction.UP:
            self.direction = (
                Direction.DOWN
                if self.has_requests_in_direction(Direction.DOWN, current)
                else Direction.IDLE
            )
        elif self.direction == Direction.DOWN:
            if self.has_requests_in_direction(Direction.UP, current):
                self.direction = Direction.UP
            else:
                self.direction = Direction.IDLE
        elif self.has_requests_in_direction(Direction.UP, current):
            self.direction = Direction.UP
        elif self.has_requests_in_direction(Direction.DOWN, current):
            self.direction = Direction.DOWN

    def move_to_floor(self, target_floor: int) -> float:
        """Simulate movement to target floor. Returns travel time."""
        if target_floor == self.current_floor:
            return 0

        distance = abs(target_floor - self.current_floor)
        travel_time = distance / self.speed

        # Update statistics
        self.total_distance_traveled += distance

        # Update position
        self.current_floor = target_floor
        self.last_position_time = time.time()

        return travel_time

    def handle_floor_stop(
        self, floor: int, waiting_people: List[Person]
    ) -> Tuple[List[Person], List[Person]]:
        """Handle stopping at a floor - unboard and board passengers"""
        # Unboard passengers
        passengers_leaving = self.unboard_passengers(floor)

        # Board new passengers
        passengers_boarding = []
        remaining_people = []

        for person in waiting_people:
            # Board passenger if we have space and moving in their direction
            # Or if we're idle (we'll adopt their direction)
            can_board = not self.is_full and (
                person.direction == self.direction or self.direction == Direction.IDLE
            )

            if can_board and self.board_passenger(person):
                passengers_boarding.append(person)
                # If we were idle, adopt the passenger's direction
                if self.direction == Direction.IDLE:
                    self.direction = person.direction
            else:
                remaining_people.append(person)

        return passengers_leaving, passengers_boarding

    def __repr__(self):
        return (
            f"Elevator {self.id}: Floor {self.current_floor}, "
            f"{self.passenger_count}/{self.capacity} passengers, "
            f"{self.direction.value}"
        )


class Building:
    """Represents the mall building with multiple floors and elevators"""

    def __init__(
        self,
        num_floors: int = None,
        num_elevators: int = None,
        strategy: ElevatorAssignmentStrategy = None,
    ):
        config = get_config()
        self.num_floors = num_floors if num_floors is not None else config.num_floors
        self.num_elevators = (
            num_elevators if num_elevators is not None else config.num_elevators
        )
        self.elevators: List[Elevator] = []
        self.strategy = strategy  # ElevatorAssignmentStrategy instance

        # Create elevators
        for i in range(self.num_elevators):
            elevator = Elevator(elevator_id=i + 1)
            self.elevators.append(elevator)

        # Waiting areas for each floor (people waiting for elevators)
        self.waiting_up: Dict[int, List[Person]] = {
            floor: [] for floor in range(1, self.num_floors + 1)
        }
        self.waiting_down: Dict[int, List[Person]] = {
            floor: [] for floor in range(1, self.num_floors + 1)
        }

        # Statistics
        self.total_people_generated = 0
        self.total_people_completed = 0
        self.completed_journeys: List[Person] = []

        # Visitor management for realistic mall behavior
        self.active_visitors: Dict[int, Person] = {}  # visitor_id -> Person
        self.pending_returns: List[Tuple[float, Person]] = []  # (return_time, person)

    def add_person_request(self, person: Person):
        """Add a person's elevator request to the building"""
        floor = person.current_floor
        direction = person.direction

        if direction == Direction.UP:
            self.waiting_up[floor].append(person)
        elif direction == Direction.DOWN:
            self.waiting_down[floor].append(person)

        # Notify elevators of the request
        self.assign_elevator_to_request(floor, direction, person.destination_floor)

        # If person reached their destination and has visit duration,
        # schedule return
        if (
            not person.is_leaving
            and person.visit_duration
            and person.destination_floor != 1
        ):
            return_time = time.time() + person.visit_duration
            self.pending_returns.append((return_time, person))
            self.active_visitors[person.id] = person

    def process_pending_returns(self):
        """Check for visitors who should start their return journey"""
        current_time = time.time()
        returns_to_process = []

        # Find returns that are due
        returns_to_process.extend(
            i
            for i, (return_time, original_person) in enumerate(self.pending_returns)
            if current_time >= return_time
        )
        # Process returns in reverse order to maintain indices
        for i in reversed(returns_to_process):
            return_time, original_person = self.pending_returns.pop(i)

            # Create return journey from their current destination
            # back to ground floor
            generator = PersonGenerator(self)
            return_person = generator.create_return_journey(
                original_person, original_person.destination_floor
            )

            # Add return journey to the building
            self.add_person_request(return_person)

            # Remove from active visitors
            if original_person.id in self.active_visitors:
                del self.active_visitors[original_person.id]

    def assign_elevator_to_request(
        self, floor: int, direction: Direction, destination_floor: int = None
    ):
        """Assign the best available elevator to handle a request"""
        # Check if any elevator already has this request assigned
        for elevator in self.elevators:
            if direction == Direction.UP and floor in elevator.up_requests:
                # Already assigned, don't assign another
                return
            if direction == Direction.DOWN and floor in elevator.down_requests:
                # Already assigned, don't assign another
                return

        # No elevator assigned yet, find the best one
        if best_elevator := self.find_best_elevator(
            floor, direction, destination_floor
        ):
            best_elevator.add_request(floor, direction)

    def find_best_elevator(
        self, floor: int, direction: Direction, destination_floor: int = None
    ) -> Optional[Elevator]:
        """Find the most suitable elevator for a request.
        Uses strategy if provided, otherwise falls back to scoring algorithm."""
        available_elevators = [
            e for e in self.elevators if e.state != ElevatorState.MAINTENANCE
        ]

        if not available_elevators:
            return None

        # Use strategy if provided
        if self.strategy is not None:
            config = get_config()
            # Convert config to ElevatorConfig
            elevator_config = ElevatorConfig(
                num_floors=self.num_floors,
                num_elevators=self.num_elevators,
                distance_weight=config.distance_weight,
                full_penalty=config.full_penalty,
                same_direction_bonus=config.same_direction_bonus,
                opposite_direction_penalty=config.opposite_direction_penalty,
                load_factor_weight=config.load_factor_weight,
                idle_bonus=config.idle_bonus,
            )
            elevator_index = self.strategy.assign_elevator(
                available_elevators,
                floor,
                direction,
                elevator_config,
                destination_floor=destination_floor,
            )
            return (
                None if elevator_index is None else available_elevators[elevator_index]
            )
        # Fallback to default scoring algorithm
        best_elevator = None
        best_score = float("inf")

        for elevator in available_elevators:
            score = self.calculate_elevator_score(elevator, floor, direction)
            if score < best_score:
                best_score = score
                best_elevator = elevator

        return best_elevator

    def calculate_elevator_score(
        self, elevator: Elevator, floor: int, direction: Direction
    ) -> float:
        """Calculate a score for how suitable an elevator is for a request
        (lower is better) - aligned with NearestCarStrategy"""
        config = get_config()

        # Can't assign if full
        if elevator.is_full:
            return config.full_penalty

        distance = abs(elevator.current_floor - floor)
        score = distance * config.distance_weight

        # Bonus if elevator is idle
        if elevator.state == ElevatorState.IDLE:
            score += config.idle_bonus

        # Bonus if elevator is already moving in the right direction
        # and not too loaded (< 70% capacity)
        elif (
            elevator.direction == direction
            and elevator.passenger_count < elevator.capacity * 0.7
        ):
            score += config.same_direction_bonus

        # Penalty if elevator is moving in opposite direction
        elif elevator.direction not in [Direction.IDLE, direction]:
            score += config.opposite_direction_penalty

        # Consider current load (if load balancing enabled)
        if config.enable_load_balancing:
            load_factor = elevator.passenger_count / elevator.capacity
            score += load_factor * config.load_factor_weight

        return score

    def get_waiting_people(self, floor: int, direction: Direction) -> List[Person]:
        """Get list of people waiting at a floor in a specific direction"""
        if direction == Direction.UP:
            return self.waiting_up[floor].copy()
        elif direction == Direction.DOWN:
            return self.waiting_down[floor].copy()
        return []

    def remove_waiting_people(
        self, floor: int, direction: Direction, people: List[Person]
    ):
        """Remove people from waiting list (they boarded an elevator)"""
        if direction == Direction.UP:
            for person in people:
                if person in self.waiting_up[floor]:
                    self.waiting_up[floor].remove(person)
        elif direction == Direction.DOWN:
            for person in people:
                if person in self.waiting_down[floor]:
                    self.waiting_down[floor].remove(person)

    def get_building_status(self) -> Dict:
        """Get current status of the entire building"""
        total_waiting = sum(len(people) for people in self.waiting_up.values()) + sum(
            len(people) for people in self.waiting_down.values()
        )

        total_passengers = sum(e.passenger_count for e in self.elevators)

        avg_wait_time = 0
        if total_waiting > 0:
            all_waiting = []
            for people in self.waiting_up.values():
                all_waiting.extend(people)
            for people in self.waiting_down.values():
                all_waiting.extend(people)
            avg_wait_time = int(
                sum(p.wait_time for p in all_waiting) / len(all_waiting)
            )

        return {
            "total_waiting": total_waiting,
            "total_passengers": total_passengers,
            "avg_wait_time": avg_wait_time,
            "total_completed": self.total_people_completed,
            "elevators": [
                {
                    "id": e.id,
                    "floor": e.current_floor,
                    "direction": e.direction.value,
                    "passengers": e.passenger_count,
                    "capacity": e.capacity,
                    "served": e.total_passengers_served,
                }
                for e in self.elevators
            ],
        }

    def __repr__(self):
        return (
            f"Building: {self.num_floors} floors, " f"{len(self.elevators)} elevators"
        )


class PersonGenerator:
    """Generates realistic patterns of people requesting elevators"""

    def __init__(self, building: Building):
        self.building = building
        self.person_id_counter = 0

        # Traffic patterns (probability distributions)
        self.floor_popularity = self.generate_floor_popularity()

    def generate_floor_popularity(self) -> Dict[int, float]:
        """Generate realistic floor popularity
        (ground floor and top floors more popular)"""
        popularity = {}
        total_floors = self.building.num_floors

        for floor in range(1, total_floors + 1):
            if floor == 1:  # Ground floor - very popular
                popularity[floor] = 0.3
            elif floor <= 3:  # Lower floors - popular (shops, restaurants)
                popularity[floor] = 0.15
            elif (
                floor >= total_floors - 2
            ):  # Top floors - popular (restaurants, entertainment)
                popularity[floor] = 0.12
            else:  # Middle floors - moderate popularity
                popularity[floor] = 0.05

        # Normalize probabilities
        total_prob = sum(popularity.values())
        for value in popularity.values():
            value /= total_prob

        return popularity

    def generate_person(self) -> Person:
        """Generate a new mall visitor entering from ground floor"""
        self.person_id_counter += 1

        # All visitors enter from ground floor
        current_floor = 1

        # Choose destination floor (2 to top floor)
        destination_floor = self.choose_destination_for_visitor()

        # Random visit duration between 20-120 minutes
        visit_duration = random.uniform(20 * 60, 120 * 60)  # Convert to seconds

        return Person(
            id=self.person_id_counter,
            current_floor=current_floor,
            destination_floor=destination_floor,
            arrival_time=time.time(),
            visit_duration=visit_duration,
            is_leaving=False,
        )

    def choose_destination_for_visitor(self) -> int:
        """Choose destination floor for a new visitor entering the mall"""
        total_floors = self.building.num_floors

        # Weight floors by type/purpose
        floor_weights = []
        for floor in range(2, total_floors + 1):
            if floor <= 3:  # Lower floors - shops, very popular
                weight = 3.0
            elif floor >= total_floors - 2:  # Top floors - restaurants/entertainment
                weight = 2.5
            else:  # Middle floors - offices, moderate popularity
                weight = 1.0
            floor_weights.append(weight)

        # Choose weighted random floor (excluding ground floor)
        floors = list(range(2, total_floors + 1))
        return random.choices(floors, weights=floor_weights)[0]

    def create_return_journey(self, person: Person, current_floor: int) -> Person:
        """Create a return journey for a visitor leaving the mall"""
        self.person_id_counter += 1

        return Person(
            id=self.person_id_counter,
            current_floor=current_floor,
            destination_floor=1,  # Always return to ground floor to exit
            arrival_time=time.time(),
            is_leaving=True,
        )

    def generate_rush_pattern(
        self, duration_minutes: int = 60, people_per_minute: float = 2.0
    ) -> List[Person]:
        """Generate a rush hour pattern of people"""
        people = []

        # Generate arrivals over time with some randomness
        for minute in range(duration_minutes):
            # Peak times have more people
            if 10 <= minute <= 20 or 45 <= minute <= 55:  # Morning and evening rush
                rate = people_per_minute * 2
            else:
                rate = people_per_minute * 0.5

            # Generate people for this minute (using Poisson-like distribution)
            # Simple approximation: rate + random variation
            base_people = int(rate)
            extra_chance = rate - base_people
            if random.random() < extra_chance:
                base_people += 1

            num_people = max(0, base_people + random.randint(-1, 1))
            for _ in range(num_people):
                person = self.generate_person()
                # Adjust arrival time to be spread throughout the minute
                person.arrival_time += minute * 60 + random.uniform(0, 60)
                people.append(person)

        return people
