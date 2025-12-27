"""
Example: Using SimulationEngine with Context Manager
====================================================

Demonstrates the context manager pattern for automatic resource cleanup.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.simulation_engine import SimulationEngine
import time


def example_basic_context_manager():
    """Basic usage with context manager"""
    print("Example 1: Basic Context Manager Usage")
    print("-" * 50)

    with SimulationEngine(num_floors=10, num_elevators=2) as sim:
        sim.start_simulation()
        print(f"Simulation running: {sim.is_running}")

        # Simulate for a few seconds
        time.sleep(3)

        # Get statistics
        stats = sim.get_current_statistics()
        print(f"People waiting: {stats['people_waiting']}")
        print(f"People completed: {stats['total_people_completed']}")

    # Simulation automatically stopped when exiting context
    print(f"After context exit, simulation running: {sim.is_running}")
    print()


def example_exception_safety():
    """Context manager ensures cleanup even with exceptions"""
    print("Example 2: Exception Safety")
    print("-" * 50)

    try:
        with SimulationEngine(num_floors=5, num_elevators=1) as sim:
            sim.start_simulation()
            print(f"Simulation started: {sim.is_running}")

            # Simulate some work that might raise an exception
            time.sleep(2)

            # Simulate an error
            raise ValueError("Simulated error during processing")

    except ValueError as e:
        print(f"Caught exception: {e}")
        print(f"Simulation properly cleaned up: {not sim.is_running}")
    print()


def example_multiple_sessions():
    """Multiple simulation sessions in sequence"""
    print("Example 3: Multiple Sessions")
    print("-" * 50)

    configurations = [
        (5, 1, "Small building"),
        (10, 2, "Medium building"),
        (15, 3, "Large building"),
    ]

    for floors, elevators, description in configurations:
        print(f"\nTesting {description}: {floors} floors, {elevators} elevators")

        with SimulationEngine(floors, elevators) as sim:
            sim.start_simulation()
            time.sleep(2)

            stats = sim.get_current_statistics()
            print(f"  Completed: {stats['total_people_completed']}")

        # Each simulation is properly cleaned up before the next one starts
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("SimulationEngine Context Manager Examples")
    print("=" * 60)
    print()

    example_basic_context_manager()
    example_exception_safety()
    example_multiple_sessions()

    print("=" * 60)
    print("All examples completed successfully! ✓")
    print("=" * 60)
