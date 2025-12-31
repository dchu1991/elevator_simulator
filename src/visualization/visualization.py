"""
Elevator Visualization System
============================

This module provides real-time visualization of the elevator simulation,
including ASCII art display, statistics dashboards, and interactive controls.
"""

import os
import time
import threading
from typing import Dict, List, Optional
from collections import deque

from src.core.elevator_simulator import (
    Elevator,
    Direction,
    ElevatorState,
)
from src.core.simulation_engine import SimulationEngine


class ASCIIDisplay:
    """ASCII-based real-time visualization of the elevator system"""

    def __init__(self, simulation: SimulationEngine):
        self.simulation = simulation
        self.building = simulation.building
        self.is_running = False
        self.display_thread: Optional[threading.Thread] = None
        self.refresh_rate = 1.0  # seconds between updates

        # Display settings
        self.elevator_width = 8
        self.floor_height = 1
        self.show_details = True

    def start(self):
        """Start the visual display in a separate thread"""
        if not self.is_running:
            self.is_running = True
            self.display_thread = threading.Thread(
                target=self._display_loop, daemon=True
            )
            self.display_thread.start()

    def stop(self):
        """Stop the visual display"""
        self.is_running = False
        if self.display_thread:
            self.display_thread.join(timeout=1.0)

    def _display_loop(self):
        """Main display refresh loop"""
        while self.is_running:
            try:
                self._clear_screen()
                self._render_building()
                time.sleep(self.refresh_rate)
            except Exception as e:
                print(f"Display error: {e}")
                break

    def _clear_screen(self):
        """Clear the terminal screen"""
        os.system("cls" if os.name == "nt" else "clear")

    def _render_building(self):
        """Render the complete building view"""
        # Header
        stats = self.simulation.get_current_statistics()
        elapsed_time = stats.get("elapsed_time", 0)

        print("=" * 80)
        print(f"{'ELEVATOR MALL SIMULATOR':^80}")
        print("=" * 80)
        print(
            f"Time: {elapsed_time:.1f}s | "
            f"Generated: {stats['total_people_generated']} | "
            f"Completed: {stats['total_people_completed']} | "
            f"Waiting: {stats['people_waiting']}"
        )
        print(
            f"Average Wait: {stats['avg_wait_time']:.1f}s | "
            f"Throughput: {stats['throughput']:.1f}/hour"
        )
        print("")

        # Building visualization
        self._render_floors()

        # Elevator details
        print("\n" + "=" * 80)
        print("ELEVATOR STATUS")
        print("=" * 80)
        self._render_elevator_details()

        # Traffic summary
        print("\n" + "=" * 80)
        print("FLOOR ACTIVITY")
        print("=" * 80)
        self._render_floor_activity()

    def _render_floors(self):
        """Render the building floors with elevators"""
        elevators = self.building.elevators
        num_floors = self.building.num_floors

        # Calculate layout
        elevator_columns = []
        for i, elevator in enumerate(elevators):
            col_start = i * (self.elevator_width + 2) + 5
            elevator_columns.append(col_start)

        # Header for elevators
        header_line = "Floor"
        for i, elevator in enumerate(elevators):
            col_start = elevator_columns[i]
            header = f"Elev{elevator.id}".center(self.elevator_width)
            header_line += " " * (col_start - len(header_line)) + header

        print(header_line)
        print("-" * len(header_line))

        # Render floors from top to bottom
        for floor in range(num_floors, 0, -1):
            self._render_single_floor(floor, elevators, elevator_columns)

    def _render_single_floor(
        self,
        floor: int,
        elevators: List[Elevator],
        elevator_columns: List[int],
    ):
        """Render a single floor line"""
        line = f"{floor:2d}:  "

        # Add elevator representations
        for i, elevator in enumerate(elevators):
            col_start = elevator_columns[i]

            # Pad to column start
            while len(line) < col_start:
                line += " "

            # Render elevator shaft and car
            elevator_display = self._get_elevator_display(elevator, floor)
            line += elevator_display

        # Add waiting people count
        waiting_up = len(self.building.waiting_up[floor])
        waiting_down = len(self.building.waiting_down[floor])

        if waiting_up > 0 or waiting_down > 0:
            line += f"  ↑{waiting_up} ↓{waiting_down}"

        print(line)

    def _get_elevator_display(self, elevator: Elevator, floor: int) -> str:
        """Get the visual representation of an elevator at a specific floor"""
        width = self.elevator_width

        if elevator.current_floor == floor:
            # Elevator is at this floor
            passengers = elevator.passenger_count
            capacity = elevator.capacity

            # Direction indicator
            if elevator.direction == Direction.UP:
                direction_char = "↑"
            elif elevator.direction == Direction.DOWN:
                direction_char = "↓"
            else:
                direction_char = "●"

            # State indicator
            if elevator.state == ElevatorState.LOADING:
                state_char = "◆"
            elif elevator.state == ElevatorState.MOVING:
                state_char = direction_char
            else:
                state_char = "○"

            # Passenger count display
            passenger_display = f"{passengers}/{capacity}"

            # Build elevator car display
            car_content = f"{state_char}{passenger_display}"
            car_display = f"[{car_content:^{width - 2}}]"

            return car_display
        else:
            # Empty shaft
            if floor in elevator.up_requests or floor in elevator.down_requests:
                # There's a request for this floor
                return f"{'◇':^{width}}"
            else:
                # Empty shaft
                return f"{'│':^{width}}"

    def _render_elevator_details(self):
        """Render detailed elevator information"""
        for elevator in self.building.elevators:
            if status := self.simulation.get_elevator_status(elevator.id):
                # Basic info
                print(
                    f"Elevator {status['id']}: Floor {status['current_floor']} | "
                    f"{status['direction']} | {status['state']} | "
                    f"Load: {len(status['passengers'])}/{status['capacity']}"
                )

                # Passengers
                if status["passengers"]:
                    passenger_info = ", ".join(
                        [f"P{p['id']}→{p['destination']}" for p in status["passengers"]]
                    )
                    print(f"  Passengers: {passenger_info}")

                # Requests
                requests = []
                if status["up_requests"]:
                    requests.append(f"Up: {sorted(status['up_requests'])}")
                if status["down_requests"]:
                    requests.append(f"Down: {sorted(status['down_requests'])}")
                if status["destination_floors"]:
                    requests.append(f"Dest: {sorted(status['destination_floors'])}")

                if requests:
                    print(f"  Requests: {' | '.join(requests)}")

                # Performance
                print(
                    f"  Served: {status['total_served']} | "
                    f"Distance: {status['distance_traveled']:.1f} floors | "
                    f"Efficiency: {status['efficiency']:.1f}%"
                )
                print()

    def _render_floor_activity(self):
        """Render floor-by-floor activity summary"""
        active_floors = []

        for floor in range(1, self.building.num_floors + 1):
            waiting_up = len(self.building.waiting_up[floor])
            waiting_down = len(self.building.waiting_down[floor])

            if waiting_up > 0 or waiting_down > 0:
                active_floors.append((floor, waiting_up, waiting_down))

        if active_floors:
            for floor, up, down in active_floors:
                people_up = [
                    f"P{p.id}→{p.destination_floor}"
                    for p in self.building.waiting_up[floor]
                ]
                people_down = [
                    f"P{p.id}→{p.destination_floor}"
                    for p in self.building.waiting_down[floor]
                ]

                floor_info = f"Floor {floor:2d}: "
                if people_up:
                    floor_info += f"UP({len(people_up)}): {', '.join(people_up[:3])}"
                    if len(people_up) > 3:
                        floor_info += f" +{len(people_up) - 3} more"

                if people_down:
                    if people_up:
                        floor_info += " | "
                    floor_info += (
                        f"DOWN({len(people_down)}): {', '.join(people_down[:3])}"
                    )
                    if len(people_down) > 3:
                        floor_info += f" +{len(people_down) - 3} more"

                print(floor_info)
        else:
            print("No people currently waiting.")


class StatisticsTracker:
    """Advanced statistics tracking and analysis"""

    def __init__(self, simulation: SimulationEngine):
        self.simulation = simulation
        self.stats_history: deque = deque(maxlen=1000)  # Keep last 1000 data points
        self.is_tracking = False
        self.tracking_thread: Optional[threading.Thread] = None

        # Performance metrics
        self.peak_waiting_time = 0
        self.peak_waiting_count = 0
        self.total_wait_time = 0
        self.completed_trips = 0

    def start_tracking(self, interval: float = 5.0):
        """Start continuous statistics tracking"""
        if not self.is_tracking:
            self.is_tracking = True
            self.tracking_thread = threading.Thread(
                target=self._tracking_loop, args=(interval,), daemon=True
            )
            self.tracking_thread.start()

    def stop_tracking(self):
        """Stop statistics tracking"""
        self.is_tracking = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)

    def _tracking_loop(self, interval: float):
        """Main tracking loop"""
        while self.is_tracking:
            try:
                stats = self.simulation.get_current_statistics()
                self._process_statistics(stats)
                self.stats_history.append(stats)
                time.sleep(interval)
            except Exception as e:
                print(f"Statistics tracking error: {e}")
                break

    def _process_statistics(self, stats: Dict):
        """Process and update cumulative statistics"""
        # Update peak metrics
        if stats["avg_wait_time"] > self.peak_waiting_time:
            self.peak_waiting_time = stats["avg_wait_time"]

        if stats["people_waiting"] > self.peak_waiting_count:
            self.peak_waiting_count = stats["people_waiting"]

        # Update cumulative metrics
        new_completions = stats["total_people_completed"] - self.completed_trips
        if new_completions > 0:
            self.completed_trips = stats["total_people_completed"]
            # Estimate total wait time (this is approximate)
            self.total_wait_time += stats["avg_wait_time"] * new_completions

    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.stats_history:
            return "No statistics available yet."

        latest = self.stats_history[-1]

        # Calculate averages over time
        if len(self.stats_history) > 1:
            avg_throughput = sum(s["throughput"] for s in self.stats_history) / len(
                self.stats_history
            )
            avg_wait_time = sum(s["avg_wait_time"] for s in self.stats_history) / len(
                self.stats_history
            )
            avg_people_waiting = sum(
                s["people_waiting"] for s in self.stats_history
            ) / len(self.stats_history)
        else:
            avg_throughput = latest["throughput"]
            avg_wait_time = latest["avg_wait_time"]
            avg_people_waiting = latest["people_waiting"]

        # Generate elevator efficiency summary
        elevator_summary: list[str] = []
        elevator_summary.extend(
            f"  Elevator {elevator_stat['id']}: {elevator_stat['passengers_served']} served, {elevator_stat['efficiency']:.1f}% efficiency, {elevator_stat['distance_traveled']:.1f} floors traveled"
            for elevator_stat in latest["elevator_stats"]
        )
        report_lines = [
            "=" * 60,
            "ELEVATOR SYSTEM PERFORMANCE REPORT",
            "=" * 60,
            f"Simulation Time: {latest['elapsed_time']:.1f} seconds",
            "",
            "TRAFFIC METRICS:",
            f"  Total People Generated: {latest['total_people_generated']}",
            f"  Total People Completed: {latest['total_people_completed']}",
            f"  Current Wait Queue: {latest['people_waiting']}",
            f"  Current In Transit: {latest['people_in_transit']}",
            "",
            "PERFORMANCE METRICS:",
            f"  Current Throughput: {latest['throughput']:.1f} people/hour",
            f"  Average Throughput: {avg_throughput:.1f} people/hour",
            f"  Current Avg Wait Time: {latest['avg_wait_time']:.1f} seconds",
            f"  Overall Avg Wait Time: {avg_wait_time:.1f} seconds",
            f"  Peak Wait Time: {self.peak_waiting_time:.1f} seconds",
            f"  Peak Queue Size: {self.peak_waiting_count} people",
            "",
            "ELEVATOR PERFORMANCE:",
            *elevator_summary,
        ]

        # System efficiency
        if latest["total_people_generated"] > 0:
            completion_rate = (
                latest["total_people_completed"] / latest["total_people_generated"]
            ) * 100
            report_lines.extend(
                [
                    "",
                    "SYSTEM EFFICIENCY:",
                    f"  Completion Rate: {completion_rate:.1f}%",
                    f"  Average Queue Size: {avg_people_waiting:.1f} people",
                ]
            )

        return "\n".join(report_lines)

    def get_trend_analysis(self) -> Dict:
        """Analyze trends in the statistics history"""
        if len(self.stats_history) < 10:
            return {"status": "Insufficient data for trend analysis"}

        # Get recent and older data points
        recent_stats = list(self.stats_history)[-5:]
        older_stats = (
            list(self.stats_history)[-15:-10]
            if len(self.stats_history) >= 15
            else list(self.stats_history)[:5]
        )

        # Calculate trends
        recent_avg_wait = sum(s["avg_wait_time"] for s in recent_stats) / len(
            recent_stats
        )
        older_avg_wait = sum(s["avg_wait_time"] for s in older_stats) / len(older_stats)

        recent_throughput = sum(s["throughput"] for s in recent_stats) / len(
            recent_stats
        )
        older_throughput = sum(s["throughput"] for s in older_stats) / len(older_stats)

        wait_trend = "improving" if recent_avg_wait < older_avg_wait else "worsening"
        throughput_trend = (
            "improving" if recent_throughput > older_throughput else "declining"
        )

        return {
            "status": "Analysis complete",
            "wait_time_trend": wait_trend,
            "wait_time_change": recent_avg_wait - older_avg_wait,
            "throughput_trend": throughput_trend,
            "throughput_change": recent_throughput - older_throughput,
            "recent_avg_wait": recent_avg_wait,
            "recent_throughput": recent_throughput,
        }


class InteractiveController:
    """Interactive control interface for the simulation"""

    def __init__(self, simulation: SimulationEngine):
        self.simulation = simulation
        self.display = ASCIIDisplay(simulation)
        self.stats_tracker = StatisticsTracker(simulation)

    def start_interactive_mode(self):
        """Start interactive mode with live display and controls"""
        print("Starting Interactive Elevator Simulation...")
        print(
            "Commands: 'q' to quit, 'r' for report, 'a' to add request, 's' for statistics"
        )
        print("Press Enter to begin...")
        input()

        # Start simulation and stats tracking but NOT the automatic display
        self.simulation.start_simulation()
        self.stats_tracker.start_tracking()

        try:
            # Show initial status
            self._show_current_status()
            self._interactive_loop()
        finally:
            # Clean shutdown
            self.stats_tracker.stop_tracking()
            self.simulation.stop_simulation()

    def _interactive_loop(self):
        """Main interactive control loop"""
        while True:
            try:
                # Show current status immediately
                print("\nCommands: (q)uit, (r)eport, (a)dd request, (s)tats, (h)elp")
                choice = input("Command: ").strip().lower()

                if choice == "q":
                    break
                elif choice == "r":
                    print("\n" + self.stats_tracker.generate_report())
                    input("Press Enter to continue...")
                elif choice == "a":
                    self._add_manual_request()
                    # Give time for elevator to respond and show updated status
                    print("\nWaiting for elevator response...")
                    time.sleep(3)
                    self._show_current_status()
                elif choice == "s":
                    trend = self.stats_tracker.get_trend_analysis()
                    print(f"\nTrend Analysis: {trend}")
                    input("Press Enter to continue...")
                elif choice == "h":
                    self._show_help()
                elif choice in ["status", ""]:
                    self._show_current_status()
                else:
                    print("Unknown command. Type 'h' for help.")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def _show_current_status(self):
        """Show current building status"""
        print("\n" + "=" * 60)
        print("CURRENT STATUS")
        print("=" * 60)

        stats = self.simulation.get_current_statistics()
        print(
            f"Time: {stats.get('elapsed_time', 0):.1f}s | "
            f"Generated: {stats['total_people_generated']} | "
            f"Completed: {stats['total_people_completed']} | "
            f"Waiting: {stats['people_waiting']}"
        )
        print(
            f"Average Wait: {stats['avg_wait_time']:.1f}s | "
            f"Throughput: {stats['throughput']:.1f}/hour"
        )

        # Show elevator positions
        print("\nElevator Positions:")
        for elevator in self.simulation.building.elevators:
            if status := self.simulation.get_elevator_status(elevator.id):
                passengers_info = f"{len(status['passengers'])}/{status['capacity']}"
                print(
                    f"  Elevator {status['id']}: Floor {status['current_floor']} | "
                    f"{status['direction']} | {status['state']} | "
                    f"Passengers: {passengers_info}"
                )

                if status["passengers"]:
                    passenger_list = ", ".join(
                        [f"P{p['id']}→{p['destination']}" for p in status["passengers"]]
                    )
                    print(f"    Carrying: {passenger_list}")

        # Show waiting people
        total_waiting = 0
        for floor in range(1, self.simulation.building.num_floors + 1):
            waiting_up = len(self.simulation.building.waiting_up[floor])
            waiting_down = len(self.simulation.building.waiting_down[floor])
            if waiting_up > 0 or waiting_down > 0:
                total_waiting += waiting_up + waiting_down
                print(f"  Floor {floor}: ↑{waiting_up} ↓{waiting_down}")

        if total_waiting == 0:
            print("  No people waiting.")

        print("=" * 60)

    def _add_manual_request(self):
        """Add a manual elevator request"""
        try:
            print("\n--- Adding New Elevator Request ---")
            from_floor = int(
                input(f"From floor (1-{self.simulation.building.num_floors}): ")
            )
            to_floor = int(
                input(f"To floor (1-{self.simulation.building.num_floors}): ")
            )

            if self.simulation.add_manual_request(from_floor, to_floor):
                print(f"✓ Added request: Floor {from_floor} → Floor {to_floor}")
                print("📍 Person is now waiting for an elevator...")

                # Show immediate status
                direction = "UP" if to_floor > from_floor else "DOWN"
                waiting_count_before = len(
                    self.simulation.building.waiting_up[from_floor]
                    if direction == "UP"
                    else self.simulation.building.waiting_down[from_floor]
                )
                print(
                    f"📊 Floor {from_floor} now has {waiting_count_before} people waiting to go {direction}"
                )

            else:
                print("❌ Invalid request (same floor or out of range).")
        except ValueError:
            print("❌ Please enter valid floor numbers.")
        except KeyboardInterrupt:
            print("\n❌ Request cancelled.")

    def _show_help(self):
        """Show help information"""
        help_text = """
ELEVATOR SIMULATOR HELP
=======================

Commands:
  q - Quit the simulation
  r - Show detailed performance report
  a - Add manual elevator request
  s - Show trend analysis
  h - Show this help

Display Legend:
  [↑2/8] - Elevator going UP with 2/8 passengers
  [↓5/8] - Elevator going DOWN with 5/8 passengers
  [○3/8] - Elevator IDLE with 3/8 passengers
  [◆4/8] - Elevator LOADING with 4/8 passengers
  ↑3 ↓2  - 3 people waiting to go UP, 2 waiting to go DOWN
  ◇      - Floor has pending elevator request
  │      - Empty elevator shaft

The simulation runs continuously, generating people with realistic
patterns including rush hours and varying floor popularity.
        """
        print(help_text)
        input("Press Enter to continue...")


# Convenience functions for different visualization modes
def run_visual_simulation(
    duration_minutes: int = 10, num_floors: int = 15, num_elevators: int = 3
):
    """Run simulation with ASCII visualization"""
    sim = SimulationEngine(
        num_floors=num_floors, num_elevators=num_elevators, time_scale=0.5
    )
    display = ASCIIDisplay(sim)

    sim.start_simulation()
    display.start()

    try:
        time.sleep(duration_minutes * 60)
    finally:
        display.stop()
        sim.stop_simulation()


def run_statistics_simulation(
    duration_minutes: int = 10, num_floors: int = 20, num_elevators: int = 4
):
    """Run simulation focused on statistics collection"""
    sim = SimulationEngine(
        num_floors=num_floors, num_elevators=num_elevators, time_scale=1.0
    )
    stats = StatisticsTracker(sim)

    sim.start_simulation()
    stats.start_tracking(interval=2.0)

    print(f"Running statistics simulation for {duration_minutes} minutes...")

    try:
        # Periodic status updates
        for minute in range(duration_minutes):
            time.sleep(60)  # Wait one minute
            current_stats = sim.get_current_statistics()
            print(
                f"Minute {minute + 1}: {current_stats['total_people_completed']} completed, "
                f"{current_stats['people_waiting']} waiting, "
                f"{current_stats['avg_wait_time']:.1f}s avg wait"
            )

    finally:
        _clean_up_simulation(stats, sim)


def _clean_up_simulation(stats, sim):
    stats.stop_tracking()
    sim.stop_simulation()

    # Final report
    print("\n" + "=" * 80)
    print("FINAL SIMULATION REPORT")
    print("=" * 80)
    print(stats.generate_report())

    # Trend analysis
    trend = stats.get_trend_analysis()
    if trend["status"] == "Analysis complete":
        print("\nPerformance Trends:")
        print(
            f"  Wait times: {trend['wait_time_trend']} (change: {trend['wait_time_change']:+.1f}s)"
        )
        print(
            f"  Throughput: {trend['throughput_trend']} (change: {trend['throughput_change']:+.1f}/hour)"
        )


if __name__ == "__main__":
    # Run a demonstration
    run_visual_simulation(duration_minutes=3, num_floors=12, num_elevators=3)
