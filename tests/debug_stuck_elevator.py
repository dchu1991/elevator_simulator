"""Debug script to trace why Elevator 1 gets stuck"""

import sys
from pathlib import Path
import time

# Add project root to path (parent of tests directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.elevator_simulator import Person, Direction
from src.core.simulation_engine import SimulationEngine


def main():
    print("=" * 60)
    print("DEBUGGING STUCK ELEVATOR 1")
    print("=" * 60)

    # Create simulation with 10 floors, 3 elevators
    sim = SimulationEngine(num_floors=10, num_elevators=3)
    sim.start_simulation()

    # Add 8 people at floor 1 going to different floors
    print("\nAdding 8 people at floor 1 going to floors 2-9...")
    for i, floor in enumerate(range(2, 10), start=1):
        person = Person(
            id=i, current_floor=1, destination_floor=floor, arrival_time=time.time()
        )
        sim.building.add_person_request(person)
        time.sleep(0.1)

    # Wait for assignment and boarding
    time.sleep(3)

    # Check elevator states
    print("\n" + "=" * 60)
    print("ELEVATOR STATES AFTER 3 SECONDS:")
    print("=" * 60)
    for elev in sim.building.elevators:
        print(f"\nElevator {elev.id}:")
        print(f"  Floor: {elev.current_floor}")
        print(f"  State: {elev.state.name}")
        print(f"  Direction: {elev.direction.name}")
        print(f"  Passengers: {len(elev.passengers)}/{elev.capacity}")
        print(f"  Destination floors: {sorted(elev.destination_floors)}")
        print(f"  Up requests: {sorted(elev.up_requests)}")
        print(f"  Down requests: {sorted(elev.down_requests)}")

        # Manually check what should happen
        if elev.id == 1:
            print("\n  DEBUG Elevator 1:")
            print(
                f"    has_requests UP from floor 1? {elev.has_requests_in_direction(Direction.UP, 1)}"
            )
            print(
                f"    has_requests DOWN from floor 1? {elev.has_requests_in_direction(Direction.DOWN, 1)}"
            )
            next_stop = elev.get_next_stop()
            print(f"    get_next_stop() returns: {next_stop}")

    # Monitor for 20 seconds
    for t in range(5, 25, 5):
        time.sleep(5)
        print(f"\n{'=' * 60}")
        print(f"STATUS AT {t} SECONDS:")
        print("=" * 60)

        for elev in sim.building.elevators:
            print(
                f"Elevator {elev.id}: Floor {elev.current_floor}, "
                f"{elev.direction.name}, {len(elev.passengers)}/{elev.capacity} pax, "
                f"dest={sorted(elev.destination_floors)}"
            )

            if elev.id == 1:
                print(
                    f"  UP req: {sorted(elev.up_requests)}, DOWN req: {sorted(elev.down_requests)}"
                )
                print(
                    f"  has_requests UP? {elev.has_requests_in_direction(Direction.UP, elev.current_floor)}"
                )
                print(f"  get_next_stop()? {elev.get_next_stop()}")

    sim.stop_simulation()
    print("\nTest completed!")


if __name__ == "__main__":
    main()
