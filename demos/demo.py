"""
Quick demo script to showcase the Elevator Mall Simulator
========================================================

This script demonstrates the elevator system with different scenarios.
Scenarios are loaded from config/demo_scenarios.json
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
from src.core.simulation_engine import SimulationEngine
from src.utils.demo_loader import DemoScenario, get_demo_loader


def run_scenario(scenario: DemoScenario):
    """Run a demo scenario based on configuration"""
    print("=" * 60)
    print(f"{scenario.name.upper()}")
    print("=" * 60)
    print(f"{scenario.description}")
    print()

    # Create simulation with context manager
    print(f"Using strategy: {scenario.strategy_name}")
    with SimulationEngine(
        num_floors=scenario.num_floors,
        num_elevators=scenario.num_elevators,
        time_scale=0.2,
    ) as sim:
        sim.start_simulation()

        print(
            f"Starting with {scenario.num_floors} floors and {scenario.num_elevators} elevators..."
        )

        # Add manual requests if configured
        if scenario.manual_requests:
            print("Adding manual requests...")
            for request in scenario.manual_requests:
                sim.add_manual_request(request.from_floor, request.to_floor)
                print(f"  Added: Floor {request.from_floor} → Floor {request.to_floor}")
                if scenario.request_delay > 0:
                    time.sleep(scenario.request_delay)

        # Run monitoring if enabled
        if scenario.monitoring_enabled:
            _track_progress_monitor(scenario, sim)
        elif scenario.visualization_enabled and scenario.visualization_type == "ascii":
            # ASCII visualization mode
            print("Watch the elevator in action!")
            print("(ASCII display will update every second)")
            print()

            for frame in range(scenario.visualization_frames):
                print(f"\n--- Frame {frame + 1}/{scenario.visualization_frames} ---")

                stats = sim.get_current_statistics()
                if elevator_status := sim.get_elevator_status(1):
                    print(
                        f"Building Status: {stats['people_waiting']} waiting, {stats['total_people_completed']} completed"
                    )
                    print(
                        f"Elevator 1: Floor {elevator_status['current_floor']}, {elevator_status['direction']}, {len(elevator_status['passengers'])} passengers"
                    )

                    for floor in range(scenario.num_floors, 0, -1):
                        elevator_here = (
                            "🛗" if elevator_status["current_floor"] == floor else "│"
                        )
                        waiting_up = len(sim.building.waiting_up[floor])
                        waiting_down = len(sim.building.waiting_down[floor])
                        waiting_str = (
                            f" ↑{waiting_up} ↓{waiting_down}"
                            if (waiting_up + waiting_down) > 0
                            else ""
                        )
                        print(f"Floor {floor}: {elevator_here}{waiting_str}")

                    time.sleep(scenario.visualization_interval)
        else:
            # Just run for duration
            time.sleep(scenario.duration_seconds)

        # Show elevator performance if configured
        if scenario.show_elevator_performance:
            print("\nElevator Performance:")
            for i, elevator in enumerate(sim.building.elevators, 1):
                controller = sim.elevator_controllers[i - 1]
                efficiency = (
                    (
                        controller.active_time
                        / (controller.active_time + controller.idle_time)
                        * 100
                    )
                    if (controller.active_time + controller.idle_time) > 0
                    else 0
                )
                print(
                    f"  Elevator {i}: {elevator.total_passengers_served} passengers served, "
                    f"{elevator.total_distance_traveled:.1f} floors traveled, "
                    f"{efficiency:.1f}% efficiency"
                )

        # Show final statistics if configured
        if scenario.show_final_stats:
            final_stats = sim.get_current_statistics()
            print("\nFinal Results:")
            print(f"  Total Completed: {final_stats['total_people_completed']}")
            print(f"  Average Wait Time: {final_stats['avg_journey_time']:.1f} seconds")
            print(f"  Currently Waiting: {final_stats['people_waiting']}")
            print(f"  System Throughput: {final_stats['throughput']:.1f} people/hour")

    print()


def _track_progress_monitor(scenario, sim):
    duration = scenario.duration_seconds
    interval = scenario.monitoring_interval
    print(f"\nMonitoring for {duration} seconds...")

    start_time = time.time()
    last_update = 0.0

    while time.time() - start_time < duration:
        current_time = time.time() - start_time

        if current_time - last_update >= interval:
            stats = sim.get_current_statistics()
            status_parts = []

            for stat_name in scenario.monitoring_stats:
                if stat_name == "avg_wait_time":
                    status_parts.append(f"{stats['avg_journey_time']:.1f}s avg wait")
                elif stat_name == "completed":
                    status_parts.append(f"{stats['total_people_completed']} completed")
                elif stat_name == "generated":
                    status_parts.append(f"{stats['total_people_generated']} generated")
                elif stat_name == "throughput":
                    status_parts.append(f"{stats['throughput']:.1f} people/hour")

                elif stat_name == "waiting":
                    status_parts.append(f"{stats['people_waiting']} waiting")
            print(f"  {current_time:.0f}s: {', '.join(status_parts)}")
            last_update = current_time

        time.sleep(1)


def main():
    """Run all demo scenarios from config"""
    print("🏢 ELEVATOR MALL SIMULATOR DEMONSTRATION 🏢")
    print("=" * 60)
    print()

    try:
        load_and_run_demos()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback

        traceback.print_exc()


def load_and_run_demos():
    loader = get_demo_loader()
    scenarios_to_run = ["scenario_1", "scenario_2", "scenario_3"]

    for scenario_id in scenarios_to_run:
        if scenario := loader.get_scenario(scenario_id):
            run_scenario(scenario)
        else:
            print(f"Warning: Scenario '{scenario_id}' not found")

    print("=" * 60)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nDemo Scenarios:")
    print("  uv run demos/demo.py         # Run predefined demo scenarios")
    print("  Edit config/demo_scenarios.json to customize scenarios")
    print("\nMain Simulator Modes:")
    print("  uv run main.py demo          # Quick pygame demo (2 min)")
    print("  uv run main.py pygame        # Pygame visualization")
    print("  uv run main.py interactive   # Interactive mode")
    print("  uv run main.py stats         # Statistics tracking (10 min)")
    print("  uv run main.py benchmark     # Performance benchmarks")
    print("\nConfiguration:")
    print("  Edit config/elevator_config.json for:")
    print("    - strategy_type: default, look, destination_dispatch, ml, adaptive")
    print("    - traffic patterns (base_arrival_rate, rush_multiplier)")
    print("    - building parameters (floors, elevators, capacity)")


if __name__ == "__main__":
    main()
