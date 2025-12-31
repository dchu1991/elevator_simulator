"""
Dependency Injection Container
==============================

Simple DI container for managing component dependencies.
Demonstrates Inversion of Control principle.
"""

from typing import Dict, Any, Callable, TypeVar, Type
from src.core.interfaces import ElevatorConfig
from src.core.strategies import NearestCarStrategy, SCANStrategy, RoundRobinStrategy
from src.utils.config_loader import get_config as load_config_from_file


T = TypeVar("T")


class Container:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance"""
        self._singletons[name] = instance

    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function for creating instances"""
        self._factories[name] = factory

    def register_type(self, name: str, type_class: Type[T]) -> None:
        """Register a type to be instantiated"""
        self._services[name] = type_class

    def resolve(self, name: str) -> Any:
        """Resolve a dependency by name"""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]

        # Check factories
        if name in self._factories:
            return self._factories[name](self)

        # Check registered types
        if name in self._services:
            return self._services[name]()

        raise ValueError(f"No registration found for '{name}'")

    def resolve_type(self, type_class: Type[T]) -> T:
        """Resolve by type (convenience method)"""
        name = type_class.__name__
        return self.resolve(name)


def create_default_container() -> Container:
    """Create container with default dependencies"""
    container = Container()

    # Load config from file and convert to new ElevatorConfig dataclass
    file_config = load_config_from_file()

    # Map properties from old config to new dataclass
    config = ElevatorConfig(
        num_floors=file_config.num_floors,
        num_elevators=file_config.num_elevators,
        elevator_capacity=file_config.elevator_capacity,
        elevator_speed=file_config.elevator_speed,
        distance_weight=file_config.distance_weight,
        full_penalty=file_config.full_penalty,
        same_direction_bonus=file_config.same_direction_bonus,
        opposite_direction_penalty=file_config.opposite_direction_penalty,
        load_factor_weight=file_config.load_factor_weight,
        idle_bonus=file_config.idle_bonus,
        base_arrival_rate=file_config.base_arrival_rate,
        rush_multiplier=file_config.rush_multiplier,
        lunch_multiplier=file_config.lunch_multiplier,
        night_multiplier=file_config.night_multiplier,
        enable_realistic_visitors=file_config.enable_realistic_visitors,
        control_loop_interval=file_config.control_loop_interval,
        traffic_check_interval=file_config.traffic_check_interval,
        movement_delay_factor=file_config.movement_delay_factor,
        stats_recording_interval=file_config.stats_recording_interval,
        enable_load_balancing=file_config.enable_load_balancing,
    )

    # Register config as singleton
    container.register_singleton("config", config)
    container.register_singleton("ElevatorConfig", config)

    # Register default strategy
    container.register_singleton("strategy", NearestCarStrategy())

    # Register alternative strategies (can be swapped)
    container.register_factory("scan_strategy", lambda c: SCANStrategy())
    container.register_factory("round_robin_strategy", lambda c: RoundRobinStrategy())

    return container


def create_test_container(
    strategy_name: str = "nearest", config_overrides: Dict[str, Any] = None
) -> Container:
    """Create container for testing with custom configuration"""
    container = Container()

    # Create test config with overrides
    config = ElevatorConfig()
    if config_overrides:
        for key, value in config_overrides.items():
            setattr(config, key, value)

    container.register_singleton("config", config)
    container.register_singleton("ElevatorConfig", config)

    # Register strategy based on name
    strategies = {
        "nearest": NearestCarStrategy(),
        "scan": SCANStrategy(),
        "round_robin": RoundRobinStrategy(),
    }

    container.register_singleton(
        "strategy", strategies.get(strategy_name, NearestCarStrategy())
    )

    return container
