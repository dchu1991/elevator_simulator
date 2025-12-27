"""
Elevator Mall Simulator - Main Entry Point
==========================================

A comprehensive elevator simulation for a multi-story mall with realistic
traffic patterns, intelligent scheduling, and real-time visualization.

Usage:
    uv run main.py demo                    - Run a quick 2-minute demonstration
    uv run main.py pygame                  - Run with pygame graphical visualization
    uv run main.py interactive             - Start interactive mode with live controls
    uv run main.py stats                   - Run statistics-focused simulation (10 minutes)
    uv run main.py custom                  - Configure custom simulation parameters

Options:
    --floors, -f    Number of floors (5-50)
    --elevators, -e Number of elevators (1-8)
    --debug, -d     Enable debug mode with detailed logging
"""

import sys
import argparse

from src.utils.config_loader import get_config
from src.core.simulation_engine import SimulationEngine, run_demo_simulation
from src.visualization.visualization import (
    StatisticsTracker,
    InteractiveController,
    run_statistics_simulation,
)
from src.visualization.pygame_visualization import run_pygame_simulation


def run_custom_simulation():
    """Run simulation with user-specified parameters"""
    print("=== Custom Elevator Simulation Setup ===")

    try:
        custom_default()
    except ValueError:
        print("Invalid input. Using default parameters.")
        run_visual_simulation(5, 15, 3)
    except KeyboardInterrupt:
        print("\nSimulation cancelled.")


# TODO Rename this here and in `run_custom_simulation`
def custom_default():
    num_floors = int(input("Number of floors (5-50, default 15): ") or "15")
    num_elevators = int(input("Number of elevators (1-8, default 3): ") or "3")
    duration = int(input("Duration in minutes (1-30, default 5): ") or "5")

    # Validate inputs
    num_floors = max(5, min(50, num_floors))
    num_elevators = max(1, min(8, num_elevators))
    duration = max(1, min(30, duration))

    print(
        f"\nStarting simulation: {num_floors} floors, "
        f"{num_elevators} elevators, {duration} minutes"
    )

    # Ask for display mode
    print("\nDisplay modes:")
    print("1. Visual (ASCII art)")
    print("2. Statistics only")
    print("3. Interactive")

    mode = input("Choose mode (1-3, default 1): ") or "1"

    if mode == "1":
        run_visual_simulation(duration, num_floors, num_elevators)
    elif mode == "2":
        run_statistics_simulation(duration, num_floors, num_elevators)
    elif mode == "3":
        sim = SimulationEngine(num_floors, num_elevators)
        controller = InteractiveController(sim)
        controller.start_interactive_mode()
    else:
        print("Invalid mode, using visual mode")
        run_visual_simulation(duration, num_floors, num_elevators)


def run_benchmark():
    """Run performance benchmarks with different configurations"""
    print("=== Elevator System Benchmarks ===")

    configurations = [
        (10, 2, "Small building"),
        (20, 4, "Medium building"),
        (30, 6, "Large building"),
        (50, 8, "Skyscraper"),
    ]

    results = []

    for floors, elevators, description in configurations:
        print(f"\nTesting {description}: {floors} floors, {elevators} elevators")

        sim = SimulationEngine(floors, elevators)
        stats_tracker = StatisticsTracker(sim)

        sim.start_simulation()
        stats_tracker.start_tracking(interval=1.0)

        try:
            # Run for 2 minutes
            import time

            time.sleep(120)
        finally:
            stats_tracker.stop_tracking()
            sim.stop_simulation()

        # Collect results
        final_stats = sim.get_current_statistics()
        results.append(
            {
                "config": description,
                "floors": floors,
                "elevators": elevators,
                "throughput": final_stats["throughput"],
                "avg_wait": final_stats["avg_wait_time"],
                "completed": final_stats["total_people_completed"],
            }
        )

    # Display benchmark results
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print(
        f"{'Configuration':<15} {'Floors':<7} {'Elevators':<10} "
        f"{'Throughput':<12} {'Avg Wait':<10} {'Completed':<10}"
    )
    print("-" * 80)

    for result in results:
        print(
            f"{result['config']:<15} {result['floors']:<7} "
            f"{result['elevators']:<10} {result['throughput']:<12.1f} "
            f"{result['avg_wait']:<10.1f} {result['completed']:<10}"
        )


def show_help():
    """Display help information"""
    config = get_config()
    help_text = f"""
Elevator Mall Simulator
======================

This simulator models a realistic elevator system in a multi-story mall with:
- Intelligent elevator scheduling and dispatch
- Realistic traffic patterns with rush hours
- Configurable strategy parameters (see elevator_config.json)

Current Configuration:
  Building: {config.num_floors} floors, {config.num_elevators} elevators
  Capacity: {config.elevator_capacity} passengers per elevator
  Speed: {config.elevator_speed} floors/second
  
  Strategy:
    Distance weight: {config.distance_weight}
    Same direction bonus: {config.same_direction_bonus}
    Opposite direction penalty: {config.opposite_direction_penalty}
    Full elevator penalty: {config.full_penalty}
    Load balancing: {'enabled' if config.enable_load_balancing else 'disabled'}
  
  Traffic:
    Base arrival rate: {config.base_arrival_rate} people/minute
    Rush hour multiplier: {config.rush_multiplier}x
    Lunch multiplier: {config.lunch_multiplier}x

To customize these settings, edit config/elevator_config.json
See docs/CONFIG_GUIDE.md for detailed documentation.

Available Commands:
  demo        - Quick 2-minute demonstration
  visual      - ASCII art visualization (5 minutes)
  pygame      - Modern graphical visualization (requires pygame)
  interactive - Interactive mode with live controls
  stats       - Statistics-focused run (10 minutes)
  custom      - Configure your own simulation
  benchmark   - Performance comparison across configurations
  help        - Show this help message

Example:
  uv run main.py demo
  uv run main.py pygame --floors 15 --elevators 3
  uv run main.py interactive
"""
    print(help_text)


def main():
    """Main entry point with command-line interface"""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Elevator Mall Simulator - "
        "A comprehensive elevator system simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run main.py demo                          # Quick demonstration
  uv run main.py demo --floors 20              # Demo with 20 floors
  uv run main.py visual --elevators 6          # Visual mode with 6 elevators
  uv run main.py pygame --floors 20 --debug    # Pygame with debug logging
  uv run main.py interactive --floors 15 --elevators 4  # Custom interactive
  uv run main.py stats -f 25 -e 5 -d          # Stats mode with debug enabled
        """,
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default="demo",
        choices=[
            "demo",
            "pygame",
            "interactive",
            "stats",
            "custom",
            "benchmark",
            "help",
        ],
        help="Simulation mode to run",
    )

    parser.add_argument(
        "--floors",
        "-f",
        type=int,
        default=None,
        help="Number of floors (5-50, default varies by mode)",
    )

    parser.add_argument(
        "--elevators",
        "-e",
        type=int,
        default=None,
        help="Number of elevators (1-8, default varies by mode)",
    )

    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode with detailed logging",
    )

    # If no arguments, show help for interactive usage
    if len(sys.argv) == 1:
        print(__doc__)
        print(
            "\nAvailable modes: demo, pygame, interactive, stats, "
            "custom, benchmark, help"
        )
        mode = (
            input("Choose a mode (or press Enter for demo): ").strip().lower()
        ) or "demo"
        # Set defaults for interactive mode
        floors = None
        elevators = None
        debug = False
    else:
        args = parser.parse_args()
        mode = args.mode
        floors = args.floors
        elevators = args.elevators
        debug = args.debug

        # Validate ranges
        if floors is not None and not (5 <= floors <= 50):
            print("Error: Number of floors must be between 5 and 50")
            return
        if elevators is not None and not (1 <= elevators <= 8):
            print("Error: Number of elevators must be between 1 and 8")
            return

    # Route to appropriate function
    try:
        if mode == "demo":
            # Set defaults for demo mode
            demo_floors = floors if floors is not None else 15
            demo_elevators = elevators if elevators is not None else 3
            if debug:
                print("Debug mode enabled")
            print(
                f"Running pygame demonstration with {demo_floors} floors "
                f"and {demo_elevators} elevators..."
            )
            run_pygame_simulation(
                num_floors=demo_floors,
                num_elevators=demo_elevators,
                duration_minutes=2,
                debug=debug,
            )

        elif mode == "pygame":
            # Set defaults for pygame mode
            pygame_floors = floors if floors is not None else 15
            pygame_elevators = elevators if elevators is not None else 3
            if debug:
                print("Debug mode enabled")
            print(
                f"Starting pygame visualization with {pygame_floors} floors "
                f"and {pygame_elevators} elevators..."
            )
            run_pygame_simulation(
                num_floors=pygame_floors,
                num_elevators=pygame_elevators,
                duration_minutes=10,
                debug=debug,
            )

        elif mode == "interactive":
            _default_interactive_mode(floors, elevators)
        elif mode == "stats":
            # Set defaults for stats mode
            stats_floors = floors if floors is not None else 20
            stats_elevators = elevators if elevators is not None else 4
            print(
                f"Running statistics simulation with {stats_floors} floors "
                f"and {stats_elevators} elevators..."
            )
            run_statistics_simulation(
                duration_minutes=10,
                num_floors=stats_floors,
                num_elevators=stats_elevators,
            )

        elif mode == "custom":
            run_custom_simulation()

        elif mode == "benchmark":
            run_benchmark()

        elif mode == "help":
            show_help()

        else:
            print(f"Unknown mode: {mode}")
            show_help()

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\nError running simulation: {e}")
        print("Use 'uv run main.py help' for usage information.")


def _default_interactive_mode(floors, elevators):
    # Set defaults for interactive mode
    interactive_floors = floors if floors is not None else 15
    interactive_elevators = elevators if elevators is not None else 4
    print(
        f"Starting interactive mode with {interactive_floors} floors "
        f"and {interactive_elevators} elevators..."
    )
    sim = SimulationEngine(
        num_floors=interactive_floors,
        num_elevators=interactive_elevators,
    )
    controller = InteractiveController(sim)
    controller.start_interactive_mode()


if __name__ == "__main__":
    main()
