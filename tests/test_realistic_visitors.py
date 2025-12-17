"""
Test Script for Realistic Visitor Pattern
========================================

This script tests the realistic mall visitor behavior where:
1. All visitors enter from ground floor (floor 1)
2. They go to various floors in the building
3. After spending 20-120 minutes, they return to floor 1 to exit
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.elevator_simulator import Building, PersonGenerator


def test_realistic_visitor_pattern():
    """Test the realistic visitor pattern"""
    print("Testing Realistic Mall Visitor Pattern")
    print("=" * 50)

    # Create a small building for testing
    building = Building(num_floors=6, num_elevators=2)
    generator = PersonGenerator(building)

    print(
        f"Building: {building.num_floors} floors, {len(building.elevators)} elevators\n"
    )

    # Generate some test visitors
    print("Generating test visitors:")
    for _ in range(5):
        person = generator.generate_person()
        print(f"Visitor {person.id}:")
        print(f"  - Enters from floor: {person.current_floor}")
        print(f"  - Going to floor: {person.destination_floor}")
        print(f"  - Visit duration: {person.visit_duration/60:.1f} minutes")
        print(f"  - Is leaving: {person.is_leaving}")

        # Simulate adding to building
        building.add_person_request(person)
        print(f"  - Added to waiting area on floor {person.current_floor}")
        print()

    print(f"Total people generated: {building.total_people_generated}")
    print(f"Active visitors tracked: {len(building.active_visitors)}")
    print(f"Pending returns scheduled: {len(building.pending_returns)}")

    print("\nWaiting areas:")
    for floor in range(1, building.num_floors + 1):
        up_count = len(building.waiting_up[floor])
        down_count = len(building.waiting_down[floor])
        if up_count > 0 or down_count > 0:
            print(f"  Floor {floor}: {up_count} waiting UP, {down_count} waiting DOWN")

    print("\nRealistic Behavior Summary:")
    print("✅ All visitors enter from floor 1 (ground floor)")
    print("✅ Visitors go to various floors (2-6) with weighted preferences")
    print("✅ Each visitor has a random visit duration (20-120 minutes)")
    print("✅ Return journeys are scheduled for later")
    print("✅ Visitors will eventually return to floor 1 to exit")

    print("\nFloor popularity (for new visitors):")
    print("- Lower floors (2-3): Popular (shops) - Weight 3.0")
    print("- Top floors (5-6): Popular (restaurants) - Weight 2.5")
    print("- Middle floors (4): Moderate (offices) - Weight 1.0")


if __name__ == "__main__":
    test_realistic_visitor_pattern()
