"""Quick test to verify strategy tracking is being called"""

import time
from src.core.simulation_engine import SimulationEngine
from src.core.advanced_strategies import DestinationDispatchStrategy, MLBasedStrategy
from src.core.strategy_factory import create_strategy

# Test DestinationDispatchStrategy tracking
print("Testing DestinationDispatchStrategy tracking...")
strategy = DestinationDispatchStrategy()
print(f"Initial state: elevator_destinations = {dict(strategy.elevator_destinations)}")

sim = SimulationEngine(num_floors=10, num_elevators=2, debug=False)
sim.building.strategy = strategy  # Use our test strategy

# Manually inject strategy into controllers
for controller in sim.elevator_controllers:
    controller.strategy = strategy

sim.start_simulation()

# Add a few manual requests
for i in range(5):
    sim.add_manual_request(from_floor=1, to_floor=5 + i)
    time.sleep(0.5)

# Let simulation run
time.sleep(5)

print(f"\nAfter 5 seconds:")
print(f"  elevator_destinations = {dict(strategy.elevator_destinations)}")
print(f"  Number of groups: {len(strategy.destination_groups)}")

time.sleep(5)

print(f"\nAfter 10 seconds:")
print(f"  elevator_destinations = {dict(strategy.elevator_destinations)}")
print(f"  Number of groups: {len(strategy.destination_groups)}")

sim.stop_simulation()

print("\n" + "=" * 60)
print("Testing MLBasedStrategy tracking...")
strategy2 = MLBasedStrategy()
print(f"Initial weights: {strategy2.strategy_weights}")
print(f"Initial history length: {len(strategy2.assignment_history)}")

sim2 = SimulationEngine(num_floors=10, num_elevators=2, debug=False)
sim2.building.strategy = strategy2

# Manually inject strategy into controllers
for controller in sim2.elevator_controllers:
    controller.strategy = strategy2

sim2.start_simulation()

# Add requests
for i in range(5):
    sim2.add_manual_request(from_floor=1, to_floor=5 + i)
    time.sleep(0.5)

time.sleep(5)

print(f"\nAfter 5 seconds:")
print(f"  Weights: {strategy2.strategy_weights}")
print(f"  History length: {len(strategy2.assignment_history)}")

time.sleep(5)

print(f"\nAfter 10 seconds:")
print(f"  Weights: {strategy2.strategy_weights}")
print(f"  History length: {len(strategy2.assignment_history)}")

sim2.stop_simulation()

print("\n✓ Tracking test complete!")
