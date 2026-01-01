"""
Elevator Simulation Engine
=========================

This module contains the main simulation logic that orchestrates
elevator movement,
passenger handling, and real-time scheduling.
"""

import time
import threading
from typing import List, Dict, Optional
from queue import PriorityQueue
from dataclasses import dataclass
import random

from src.utils.config_loader import get_config
from src.core.strategy_factory import create_strategy
from .elevator_simulator import (
    Building,
    Elevator,
    Person,
    PersonGenerator,
    Direction,
    ElevatorState,
)


@dataclass
class SimulationEvent:
    """Represents an event in the simulation timeline"""

    timestamp: float
    event_type: str
    elevator_id: Optional[int] = None
    floor: Optional[int] = None
    data: Optional[Dict] = None

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class ElevatorController:
    """Advanced controller for managing individual elevator operations"""

    def __init__(
        self,
        elevator: Elevator,
        building: Building,
        debug: bool = False,
        time_scale: float = 1.0,
        strategy=None,
    ):
        self.elevator = elevator
        self.building = building
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.debug = debug
        self.time_scale = time_scale
        self.strategy = strategy

        # Event queue for this elevator
        self.event_queue: PriorityQueue = PriorityQueue()

        # Performance metrics
        self.idle_time = 0
        self.active_time = 0
        self.last_activity_time = time.time()

        # Track assignments for ML-based strategy
        # person_id -> assignment_idx
        self.pending_assignments: Dict[int, int] = {}

    def start(self):
        """Start the elevator controller in a separate thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_control_loop, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop the elevator controller"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _run_control_loop(self):
        """Main control loop for the elevator"""
        config = get_config()
        while self.is_running:
            try:
                self._process_elevator_step()
                time.sleep(config.control_loop_interval * self.time_scale)
            except Exception as e:
                print(f"Error in elevator {self.elevator.id} control loop: {e}")

    def _process_elevator_step(self):
        """Process one step of elevator operation"""
        current_time = time.time()

        # Update activity tracking
        if self.elevator.state != ElevatorState.IDLE:
            self.active_time += current_time - self.last_activity_time
        else:
            self.idle_time += current_time - self.last_activity_time
        self.last_activity_time = current_time

        # Update direction based on requests first
        old_direction = self.elevator.direction
        self.elevator.update_direction()

        if self.debug and old_direction != self.elevator.direction:
            if (
                self.elevator.up_requests
                or self.elevator.down_requests
                or self.elevator.destination_floors
            ):
                print(
                    f"E{self.elevator.id} Floor={self.elevator.current_floor}: "
                    f"{old_direction.value} -> {self.elevator.direction.value} "
                    f"(Dest={sorted(self.elevator.destination_floors)}, "
                    f"Up={sorted(self.elevator.up_requests)}, "
                    f"Down={sorted(self.elevator.down_requests)})"
                )

        # Check if we need to stop at current floor
        if self._should_stop_at_current_floor():
            self._handle_floor_stop()
            return

        # Move towards next destination if we have one
        next_stop = self.elevator.get_next_stop()
        if next_stop is not None and next_stop != self.elevator.current_floor:
            self._move_towards_floor(next_stop)
        else:
            # No requests, go idle
            self.elevator.state = ElevatorState.IDLE
            self.elevator.direction = Direction.IDLE

    def _should_stop_at_current_floor(self) -> bool:
        """Determine if elevator should stop at current floor"""
        current_floor = self.elevator.current_floor

        # Stop if passengers want to get off
        if current_floor in self.elevator.destination_floors:
            return True

        # Check if there are people actually waiting, not just requests
        has_people_waiting_up = (
            len(self.building.get_waiting_people(current_floor, Direction.UP)) > 0
        )
        has_people_waiting_down = (
            len(self.building.get_waiting_people(current_floor, Direction.DOWN)) > 0
        )

        # Clean up stale requests - requests for current floor where nobody is waiting
        if current_floor in self.elevator.up_requests and not has_people_waiting_up:
            if self.debug:
                print(
                    f"E{self.elevator.id} Removing stale UP request at floor {current_floor}"
                )
            self.elevator.up_requests.discard(current_floor)
        if current_floor in self.elevator.down_requests and not has_people_waiting_down:
            if self.debug:
                print(
                    f"E{self.elevator.id} Removing stale DOWN request at floor {current_floor}"
                )
            self.elevator.down_requests.discard(current_floor)

        # Stop if there are people waiting in our direction and we have space
        if not self.elevator.is_full:
            if self.elevator.direction == Direction.UP and has_people_waiting_up:
                return True
            if self.elevator.direction == Direction.DOWN and has_people_waiting_down:
                return True
            if self.elevator.direction == Direction.IDLE and (
                has_people_waiting_up or has_people_waiting_down
            ):
                return True

            # If no more requests in current direction but people waiting opposite direction, stop
            if self.elevator.direction == Direction.UP:
                has_more_up_requests = self.elevator.has_requests_in_direction(
                    Direction.UP, current_floor
                )
                if not has_more_up_requests and has_people_waiting_down:
                    return True
            elif self.elevator.direction == Direction.DOWN:
                has_more_down_requests = self.elevator.has_requests_in_direction(
                    Direction.DOWN, current_floor
                )
                if not has_more_down_requests and has_people_waiting_up:
                    return True

        return False

    def _handle_floor_stop(self):
        """Handle stopping at current floor"""
        current_floor = self.elevator.current_floor
        self.elevator.state = ElevatorState.LOADING

        # Always check for waiting passengers at this floor
        waiting_people = []

        # Get people waiting in the elevator's current direction
        if self.elevator.direction == Direction.UP:
            waiting_people.extend(
                self.building.get_waiting_people(current_floor, Direction.UP)
            )
        elif self.elevator.direction == Direction.DOWN:
            waiting_people.extend(
                self.building.get_waiting_people(current_floor, Direction.DOWN)
            )
        elif self.elevator.direction == Direction.IDLE:
            # If idle, pick up everyone waiting
            waiting_people.extend(
                self.building.get_waiting_people(current_floor, Direction.UP)
            )
            waiting_people.extend(
                self.building.get_waiting_people(current_floor, Direction.DOWN)
            )

        # Handle the stop (unboard and board)
        passengers_leaving, passengers_boarding = self.elevator.handle_floor_stop(
            current_floor, waiting_people
        )

        if self.debug and (passengers_leaving or passengers_boarding):
            print(
                f"E{self.elevator.id} STOP Floor={current_floor} Dir={self.elevator.direction.value}: "
                f"Boarded={len(passengers_boarding)}, Left={len(passengers_leaving)}, "
                f"Onboard={self.elevator.passenger_count}/{self.elevator.capacity}"
            )
            # Verify we're actually at the floor
            if self.elevator.current_floor != current_floor:
                print(
                    f"  WARNING: Elevator actual floor={self.elevator.current_floor}, "
                    f"but stopping at floor={current_floor}"
                )

        # Update building's waiting lists for boarded passengers
        for person in passengers_boarding:
            if person.direction == Direction.UP:
                self.building.remove_waiting_people(
                    current_floor, Direction.UP, [person]
                )
            else:
                self.building.remove_waiting_people(
                    current_floor, Direction.DOWN, [person]
                )

            # Track for DestinationDispatchStrategy
            if self.strategy is not None:
                from src.core.advanced_strategies import (
                    DestinationDispatchStrategy,
                    MLBasedStrategy,
                )

                if isinstance(self.strategy, DestinationDispatchStrategy):
                    # Register destination when passenger boards
                    self.strategy.register_destination(
                        self.elevator.id - 1,  # Convert to 0-indexed
                        current_floor,
                        person.destination_floor,
                    )

                if isinstance(self.strategy, MLBasedStrategy) and len(self.strategy.assignment_history) > 0:
                    assignment_idx = len(self.strategy.assignment_history) - 1
                    # Record wait time and update from feedback
                    wait_time = person.wait_time
                    self.strategy.update_from_feedback(wait_time, assignment_idx)

        # Track destination clearing for DestinationDispatchStrategy
        if self.strategy is not None and passengers_leaving:
            from src.core.advanced_strategies import DestinationDispatchStrategy

            if isinstance(self.strategy, DestinationDispatchStrategy):
                for person in passengers_leaving:
                    # Clear destination when passenger reaches their floor
                    self.strategy.clear_destination(
                        self.elevator.id - 1,  # Convert to 0-indexed
                        person.destination_floor,
                    )

        # Check if there are still people waiting after boarding
        # Only remove requests if the waiting area is now empty
        still_waiting_up = len(
            self.building.get_waiting_people(current_floor, Direction.UP)
        )
        still_waiting_down = len(
            self.building.get_waiting_people(current_floor, Direction.DOWN)
        )

        # Remove requests only if no one is still waiting in that direction
        if current_floor in self.elevator.up_requests and still_waiting_up == 0:
            self.elevator.up_requests.discard(current_floor)
        if current_floor in self.elevator.down_requests and still_waiting_down == 0:
            self.elevator.down_requests.discard(current_floor)

        # Update statistics
        for person in passengers_leaving:
            self.building.total_people_completed += 1
            self.building.completed_journeys.append(person)

        # Simulate loading/unloading time
        loading_time = 0.5 + (len(passengers_leaving) + len(passengers_boarding)) * 0.2
        time.sleep(loading_time * self.time_scale)

        self.elevator.state = ElevatorState.MOVING

    def _move_towards_floor(self, target_floor: int):
        """Move elevator towards target floor"""
        current_floor = self.elevator.current_floor

        if target_floor > current_floor:
            self.elevator.direction = Direction.UP
            # Simulate gradual movement
            self._simulate_movement(target_floor)
        elif target_floor < current_floor:
            self.elevator.direction = Direction.DOWN
            # Simulate gradual movement
            self._simulate_movement(target_floor)

        self.elevator.state = ElevatorState.MOVING

    def _simulate_movement(self, target_floor: int):
        """Simulate gradual elevator movement"""
        current_floor = self.elevator.current_floor

        if current_floor == target_floor:
            return

        # Determine next floor to move to
        if target_floor > current_floor:
            next_floor = current_floor + 1
        else:
            next_floor = current_floor - 1

        # Update elevator position
        self.elevator.current_floor = next_floor
        self.elevator.total_distance_traveled += 1

        # Small delay to simulate movement (configurable)
        config = get_config()
        time.sleep(config.movement_delay_factor / self.elevator.speed * self.time_scale)


class TrafficManager:
    """Manages realistic traffic patterns and person generation"""

    def __init__(self, building: Building, time_scale: float = 1.0):
        config = get_config()
        self.building = building
        self.person_generator = PersonGenerator(building)
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.time_scale = time_scale

        # Traffic patterns from config
        self.base_arrival_rate = config.base_arrival_rate
        self.rush_multiplier = config.rush_multiplier
        self.lunch_multiplier = config.lunch_multiplier
        self.night_multiplier = config.night_multiplier

    def start(self):
        """Start traffic generation"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._generate_traffic, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop traffic generation"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _generate_traffic(self):
        """Generate realistic traffic patterns"""
        start_time = time.time()

        while self.is_running:
            current_time = time.time()
            elapsed_minutes = (current_time - start_time) / 60

            # Determine current traffic rate based on time
            rate = self._get_current_traffic_rate(elapsed_minutes)

            # Generate people based on Poisson distribution
            # Scale rate by time_scale: faster simulation = more passengers per wall-clock second
            scaled_rate = rate / self.time_scale
            if (
                random.random() < scaled_rate / 60
            ):  # Convert per-minute to per-second probability
                person = self.person_generator.generate_person()
                self.building.add_person_request(person)
                self.building.total_people_generated += 1

            # Process pending return journeys for visitors
            self.building.process_pending_returns()

            config = get_config()
            # Scale sleep interval: faster simulation = check more frequently
            time.sleep(config.traffic_check_interval * self.time_scale)

    def _get_current_traffic_rate(self, elapsed_minutes: float) -> float:
        """Get traffic rate based on time of day simulation"""
        # Simulate a day with rush hours
        minute_in_day = elapsed_minutes % (24 * 60)  # 24-hour cycle
        hour = minute_in_day / 60

        # Define rush hours and peak times
        if 8 <= hour <= 10 or 17 <= hour <= 19:  # Morning and evening rush
            return self.base_arrival_rate * self.rush_multiplier
        elif 12 <= hour <= 14:  # Lunch rush
            return self.base_arrival_rate * self.lunch_multiplier
        elif 6 <= hour <= 23:  # Active hours
            return self.base_arrival_rate
        else:  # Night hours
            return self.base_arrival_rate * self.night_multiplier


class SimulationEngine:
    """Main simulation engine that coordinates all components"""

    def __init__(
        self,
        num_floors: int = 20,
        num_elevators: int = 4,
        debug: bool = False,
        time_scale: float = 1.0,
    ):
        # Create strategy based on config
        config = get_config()
        strategy = create_strategy(config.strategy_type)

        self.building = Building(num_floors, num_elevators, strategy=strategy)
        self.traffic_manager = TrafficManager(self.building, time_scale)
        self.elevator_controllers: List[ElevatorController] = []
        self.debug = debug
        self.time_scale = time_scale  # 1.0 = normal speed, 0.1 = 10x faster

        # Create controllers for each elevator
        for elevator in self.building.elevators:
            controller = ElevatorController(
                elevator,
                self.building,
                debug=debug,
                time_scale=time_scale,
                strategy=strategy,
            )
            self.elevator_controllers.append(controller)

        # Simulation state
        self.is_running = False
        self.start_time = None
        self.simulation_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats_history: List[Dict] = []
        self.stats_interval = 10.0  # Record stats every 10 seconds
        self.last_stats_time = 0

    def __enter__(self):
        """Enter context manager - returns self for use in with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - ensures simulation is stopped"""
        if self.is_running:
            self.stop_simulation()
        return False  # Don't suppress exceptions

    def start_simulation(self):
        """Start the complete simulation"""
        if self.is_running:
            return

        self.is_running = True
        self.start_time = time.time()

        print("Starting elevator simulation...")
        print(
            f"Building: {self.building.num_floors} floors, "
            f"{len(self.building.elevators)} elevators"
        )

        # Start all components
        for controller in self.elevator_controllers:
            controller.start()

        self.traffic_manager.start()

        # Start main simulation monitoring thread
        self.simulation_thread = threading.Thread(
            target=self._run_simulation_monitor, daemon=True
        )
        self.simulation_thread.start()

        print("Simulation started successfully!")

    def stop_simulation(self):
        """Stop the simulation"""
        print("Stopping simulation...")
        self.is_running = False

        # Stop all components
        self.traffic_manager.stop()

        for controller in self.elevator_controllers:
            controller.stop()

        if self.simulation_thread:
            self.simulation_thread.join(timeout=2.0)

        print("Simulation stopped.")

    def _run_simulation_monitor(self):
        """Monitor simulation and collect statistics"""
        while self.is_running:
            current_time = time.time()

            # Record statistics periodically
            if current_time - self.last_stats_time >= self.stats_interval:
                stats = self._collect_statistics()
                self.stats_history.append(stats)
                self.last_stats_time = current_time

            time.sleep(1.0)

    def _collect_statistics(self) -> Dict:
        """Collect comprehensive simulation statistics"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time if self.start_time else 0

        # Building statistics
        building_status = self.building.get_building_status()

        # Elevator efficiency metrics
        elevator_stats = []
        for controller in self.elevator_controllers:
            elevator = controller.elevator
            total_time = controller.active_time + controller.idle_time
            efficiency = (
                (controller.active_time / total_time * 100) if total_time > 0 else 0
            )

            elevator_stats.append(
                {
                    "id": elevator.id,
                    "efficiency": efficiency,
                    "passengers_served": elevator.total_passengers_served,
                    "distance_traveled": elevator.total_distance_traveled,
                    "current_floor": elevator.current_floor,
                    "state": elevator.state.value,
                    "direction": elevator.direction.value,
                }
            )

        # Calculate average wait times from completed journeys
        avg_journey_time = 0.0
        if self.building.completed_journeys:
            if recent_journeys := [
                j
                for j in self.building.completed_journeys
                if j.boarding_time is not None and j.boarding_time > current_time - 300
            ]:
                avg_journey_time = sum(
                    (j.boarding_time - j.arrival_time)
                    for j in recent_journeys
                    if j.boarding_time is not None
                ) / len(recent_journeys)

        # Adjust wait times for time_scale (timestamps are in real time, not simulated time)
        adjusted_avg_wait = building_status["avg_wait_time"] / self.time_scale
        adjusted_avg_journey = avg_journey_time / self.time_scale

        return {
            "timestamp": current_time,
            "elapsed_time": elapsed_time,
            "total_people_generated": self.building.total_people_generated,
            "total_people_completed": self.building.total_people_completed,
            "people_waiting": building_status["total_waiting"],
            "people_in_transit": building_status["total_passengers"],
            "avg_wait_time": adjusted_avg_wait,
            "avg_journey_time": adjusted_avg_journey,
            "elevator_stats": elevator_stats,
            "throughput": (
                self.building.total_people_completed / (elapsed_time / 3600)
                if elapsed_time > 0
                else 0
            ),  # people per hour
        }

    def get_current_statistics(self) -> Dict:
        """Get current simulation statistics"""
        return self._collect_statistics()

    def get_elevator_status(self, elevator_id: int) -> Optional[Dict]:
        """Get detailed status of a specific elevator"""
        if 1 <= elevator_id <= len(self.building.elevators):
            elevator = self.building.elevators[elevator_id - 1]
            controller = self.elevator_controllers[elevator_id - 1]

            return {
                "id": elevator.id,
                "current_floor": elevator.current_floor,
                "direction": elevator.direction.value,
                "state": elevator.state.value,
                "passengers": [
                    {
                        "id": p.id,
                        "destination": p.destination_floor,
                        "wait_time": p.wait_time,
                    }
                    for p in elevator.passengers
                ],
                "capacity": elevator.capacity,
                "speed": elevator.speed,
                "up_requests": list(elevator.up_requests),
                "down_requests": list(elevator.down_requests),
                "destination_floors": list(elevator.destination_floors),
                "total_served": elevator.total_passengers_served,
                "distance_traveled": elevator.total_distance_traveled,
                "efficiency": (
                    (
                        controller.active_time
                        / (controller.active_time + controller.idle_time)
                        * 100
                    )
                    if (controller.active_time + controller.idle_time) > 0
                    else 0
                ),
            }
        return None

    def add_manual_request(self, from_floor: int, to_floor: int) -> bool:
        """Manually add a person request (for testing/demo purposes)"""
        if not (
            1 <= from_floor <= self.building.num_floors
            and 1 <= to_floor <= self.building.num_floors
        ):
            return False

        if from_floor == to_floor:
            return False

        person = Person(
            id=self.building.total_people_generated + 1,
            current_floor=from_floor,
            destination_floor=to_floor,
            arrival_time=time.time(),
        )

        self.building.add_person_request(person)
        self.building.total_people_generated += 1
        return True

    def get_building_overview(self) -> str:
        """Get a text overview of the current building state"""
        lines = [
            "=== ELEVATOR MALL SIMULATOR ===",
            f"Floors: {self.building.num_floors} | Elevators: {len(self.building.elevators)}",
            "",
            "ELEVATOR STATUS:",
        ]
        for elevator in self.building.elevators:
            passengers_str = (
                ", ".join(
                    [f"{p.id}→{p.destination_floor}" for p in elevator.passengers]
                )
                or "Empty"
            )
            lines.append(
                f"  Elevator {elevator.id}: Floor {elevator.current_floor} | {elevator.direction.value} | [{passengers_str}]"
            )

        lines.append("")

        # Waiting people summary
        total_waiting_up = sum(
            len(people) for people in self.building.waiting_up.values()
        )
        total_waiting_down = sum(
            len(people) for people in self.building.waiting_down.values()
        )
        lines.append(
            f"WAITING: {total_waiting_up} going UP, {total_waiting_down} going DOWN"
        )

        # Show floors with waiting people
        for floor in range(self.building.num_floors, 0, -1):
            up_count = len(self.building.waiting_up[floor])
            down_count = len(self.building.waiting_down[floor])
            if up_count > 0 or down_count > 0:
                lines.append(f"  Floor {floor:2d}: ↑{up_count} ↓{down_count}")

        return "\n".join(lines)


# Demo and testing functions
def run_demo_simulation(
    duration_minutes: int = 5,
    num_floors: int = 15,
    num_elevators: int = 3,
    scenario_id: str = None,
):
    """Run a demonstration of the elevator simulation

    Args:
        duration_minutes: Duration in minutes (used if scenario_id is None)
        num_floors: Number of floors (used if scenario_id is None)
        num_elevators: Number of elevators (used if scenario_id is None)
        scenario_id: ID of scenario from config/demo_scenarios.json
    """
    from src.utils.demo_loader import load_default_scenario, load_scenario

    # Load scenario from config if specified
    if scenario_id:
        scenario = load_scenario(scenario_id)
        if not scenario:
            print(f"Warning: Scenario '{scenario_id}' not found, using defaults")
            scenario = None
    else:
        scenario = load_default_scenario()

    if scenario:
        # Use scenario configuration
        num_floors = scenario.num_floors
        num_elevators = scenario.num_elevators
        duration_seconds = scenario.duration_seconds
        monitoring_interval = (
            scenario.monitoring_interval if scenario.monitoring_enabled else 30
        )
    else:
        # Use provided parameters
        duration_seconds = duration_minutes * 60
        monitoring_interval = 30

    print(
        f"Running quick demonstration with {num_floors} floors and {num_elevators} elevators..."
    )
    print("Starting Elevator Mall Demo...")

    # Create simulation with specified parameters
    sim = SimulationEngine(num_floors=num_floors, num_elevators=num_elevators)

    # Start simulation
    sim.start_simulation()

    try:
        # Run for specified duration with status updates
        start_time = time.time()
        last_update = 0.0

        while time.time() - start_time < duration_seconds:
            current_time = time.time() - start_time

            # Print status at intervals
            if current_time - last_update >= monitoring_interval:
                print(f"\n--- Status at {current_time:.1f}s ---")
                stats = sim.get_current_statistics()
                print(
                    f"Generated: {stats['total_people_generated']} | Completed: {stats['total_people_completed']} | Waiting: {stats['people_waiting']}"
                )
                print(
                    f"Average wait time: {stats['avg_wait_time']:.1f}s | Throughput: {stats['throughput']:.1f} people/hour"
                )
                last_update = current_time

            time.sleep(1)

    finally:
        _clean_up_demo(sim)


def _clean_up_demo(sim):
    sim.stop_simulation()

    # Print final statistics
    final_stats = sim.get_current_statistics()
    print("\n=== FINAL STATISTICS ===")
    print(f"Total people processed: {final_stats['total_people_completed']}")
    print(f"Average wait time: {final_stats['avg_wait_time']:.1f} seconds")
    print(f"Throughput: {final_stats['throughput']:.1f} people per hour")

    for elevator_stat in final_stats["elevator_stats"]:
        print(
            f"Elevator {elevator_stat['id']}: {elevator_stat['passengers_served']} served, {elevator_stat['efficiency']:.1f}% efficiency"
        )


if __name__ == "__main__":
    # Run demo if script is executed directly
    run_demo_simulation(duration_minutes=2)
