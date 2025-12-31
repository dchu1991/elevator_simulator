"""
Example: Using Dependency Injection
===================================

Demonstrates how DI improves testability and modularity.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.container import create_default_container, create_test_container
from src.core.interfaces import ElevatorConfig
from src.core.strategies import NearestCarStrategy, SCANStrategy, RoundRobinStrategy


def example_basic_di():
    """Basic dependency injection example"""
    print("=" * 60)
    print("Example 1: Basic Dependency Injection")
    print("=" * 60)

    # Create container with default dependencies
    container = create_default_container()

    # Resolve dependencies
    config = container.resolve("config")
    strategy = container.resolve("strategy")

    print(
        f"Config loaded: {config.num_floors} floors, {config.num_elevators} elevators"
    )
    print(f"Strategy: {strategy.__class__.__name__}")
    print(f"Elevator speed: {config.elevator_speed} floors/sec")
    print()


def example_strategy_swapping():
    """Demonstrate swapping strategies at runtime"""
    print("=" * 60)
    print("Example 2: Swapping Strategies")
    print("=" * 60)

    # Test with different strategies
    strategies = [
        ("nearest", "NearestCarStrategy"),
        ("scan", "SCANStrategy"),
        ("round_robin", "RoundRobinStrategy"),
    ]

    for strategy_name, expected_class in strategies:
        container = create_test_container(strategy_name=strategy_name)
        strategy = container.resolve("strategy")
        print(f"Strategy '{strategy_name}': {strategy.__class__.__name__}")

    print()


def example_config_override():
    """Demonstrate config overrides for testing"""
    print("=" * 60)
    print("Example 3: Config Overrides for Testing")
    print("=" * 60)

    # Create test container with custom config
    container = create_test_container(
        config_overrides={
            "num_floors": 5,
            "num_elevators": 1,
            "elevator_speed": 10.0,  # Super fast for testing
            "base_arrival_rate": 1.0,  # Low traffic for testing
        }
    )

    config = container.resolve("config")
    print(f"Test config: {config.num_floors} floors, {config.num_elevators} elevator")
    print(f"Speed: {config.elevator_speed} (faster for tests)")
    print(f"Traffic rate: {config.base_arrival_rate} people/min (lower for tests)")
    print()


def example_manual_injection():
    """Show how to inject dependencies manually"""
    print("=" * 60)
    print("Example 4: Manual Dependency Injection")
    print("=" * 60)

    # Create custom config
    config = ElevatorConfig(
        num_floors=10,
        num_elevators=2,
        elevator_speed=3.0,
        distance_weight=2.0,  # Prioritize distance more
        idle_bonus=-15,  # Strongly prefer idle elevators
    )

    # Create custom strategy
    strategy = SCANStrategy()

    print(f"Custom config created: {config.num_floors} floors")
    print(f"Custom strategy: {strategy.__class__.__name__}")
    print(f"Distance weight: {config.distance_weight} (higher = distance matters more)")
    print(f"Idle bonus: {config.idle_bonus} (negative = prefer idle)")
    print()


def example_benefits():
    """Explain the benefits of DI"""
    print("=" * 60)
    print("Benefits of Dependency Injection")
    print("=" * 60)

    benefits = [
        "✓ Testability: Easy to inject mock dependencies for unit tests",
        "✓ Flexibility: Swap implementations without changing code",
        "✓ Configurability: Different configs for dev/test/prod",
        "✓ Decoupling: Components don't create their own dependencies",
        "✓ Reusability: Same component works with different dependencies",
        "✓ Maintainability: Clear dependency graph, easier to understand",
    ]

    for benefit in benefits:
        print(f"  {benefit}")

    print()


if __name__ == "__main__":
    example_basic_di()
    example_strategy_swapping()
    example_config_override()
    example_manual_injection()
    example_benefits()

    print("=" * 60)
    print("Next steps:")
    print("  1. Refactor SimulationEngine to accept injected dependencies")
    print("  2. Refactor Building to use injected strategy")
    print("  3. Add event bus for observer pattern")
    print("  4. Create more strategies (LOOK, Destination Dispatch, etc.)")
    print("=" * 60)
