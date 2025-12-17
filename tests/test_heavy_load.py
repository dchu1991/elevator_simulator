"""
Heavy Load Test - Stress test the elevator system with lots of requests
"""

import itertools
import sys
from pathlib import Path
import time

# Add project root to path (parent of tests directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
from src.core.simulation_engine import SimulationEngine


def test_heavy_load():
    """Test with heavy traffic load"""
    print("=" * 60)
    print("HEAVY TRAFFIC LOAD TEST")
    print("=" * 60)
    print("Testing: 10 floors, 3 elevators, 120 seconds")
    print("Adding many manual requests to simulate heavy load...")
    print()

    # Create simulation
    sim = SimulationEngine(num_floors=10, num_elevators=3)
    sim.start_simulation()

    requests = [
        (i, j) for i, j in itertools.product(range(1, 11), range(1, 11)) if i != j
    ]
    print(f"Adding {len(requests)} manual requests rapidly...")

    # Add first batch quickly
    for i, (from_floor, to_floor) in enumerate(requests[:30]):
        sim.add_manual_request(from_floor, to_floor)
        if i % 5 == 0:
            print(f"  Added {i+1} requests...")
        time.sleep(0.1)  # Small delay

    print("\nMonitoring system performance...")
    print()

    start_time = time.time()
    last_update = 0

    # Monitor for 2 minutes
    while time.time() - start_time < 120:
        current_time = time.time() - start_time

        # Add more requests periodically
        if int(current_time) % 10 == 0 and len(requests) > 30:
            idx = min(30 + int(current_time) // 10, len(requests) - 1)
            if idx < len(requests):
                from_floor, to_floor = requests[idx]
                sim.add_manual_request(from_floor, to_floor)

        # Status update every 10 seconds
        if current_time - last_update >= 10:
            stats = sim.get_current_statistics()
            print(f"\n--- Status at {current_time:.0f}s ---")
            print(
                f"Generated: {stats['total_people_generated']} | "
                f"Completed: {stats['total_people_completed']} | "
                f"Waiting: {stats['people_waiting']}"
            )
            print(
                f"Avg Wait: {stats['avg_wait_time']:.1f}s | "
                f"Throughput: {stats['throughput']:.1f} people/hour"
            )

            # Show elevator status
            for i, elevator in enumerate(sim.building.elevators, 1):
                requests_count = (
                    len(elevator.up_requests)
                    + len(elevator.down_requests)
                    + len(elevator.destination_floors)
                )
                print(
                    f"  Elevator {i}: Floor {elevator.current_floor}, "
                    f"{elevator.direction.value}, "
                    f"{elevator.passenger_count}/{elevator.capacity} passengers, "
                    f"{requests_count} pending requests"
                )

            last_update = current_time

        time.sleep(1)

    # Final statistics
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    final_stats = sim.get_current_statistics()
    print(f"Total Generated: {final_stats['total_people_generated']}")
    print(f"Total Completed: {final_stats['total_people_completed']}")
    print(f"Still Waiting: {final_stats['people_waiting']}")
    print(f"Average Wait Time: {final_stats['avg_wait_time']:.1f} seconds")
    print(f"Throughput: {final_stats['throughput']:.1f} people/hour")
    print()

    for elevator_stat in final_stats["elevator_stats"]:
        print(
            f"Elevator {elevator_stat['id']}: "
            f"{elevator_stat['passengers_served']} served, "
            f"{elevator_stat['efficiency']:.1f}% efficiency"
        )

    sim.stop_simulation()
    print("\nTest completed!")


if __name__ == "__main__":
    test_heavy_load()
