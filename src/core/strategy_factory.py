"""
Strategy Factory
================

Factory for creating elevator assignment strategies based on configuration.
"""

from typing import Optional
from src.core.interfaces import ElevatorAssignmentStrategy
from src.core.strategies import NearestCarStrategy, RoundRobinStrategy, SCANStrategy
from src.core.advanced_strategies import (
    LOOKStrategy,
    DestinationDispatchStrategy,
    MLBasedStrategy,
    AdaptiveStrategy,
)


def create_strategy(strategy_type: str) -> ElevatorAssignmentStrategy:
    """
    Create an elevator assignment strategy based on type.

    Args:
        strategy_type: Type of strategy ('default', 'scan', 'round_robin', 'look',
                       'destination_dispatch', 'ml', 'adaptive')

    Returns:
        Instance of the requested strategy

    Raises:
        ValueError: If strategy_type is unknown
    """
    strategy_type = strategy_type.lower()

    if strategy_type == "default":
        return NearestCarStrategy()
    elif strategy_type == "scan":
        return SCANStrategy()
    elif strategy_type == "round_robin":
        return RoundRobinStrategy()
    elif strategy_type == "look":
        return LOOKStrategy()
    elif strategy_type == "destination_dispatch":
        return DestinationDispatchStrategy()
    elif strategy_type == "ml":
        return MLBasedStrategy()
    elif strategy_type == "adaptive":
        return AdaptiveStrategy()
    else:
        raise ValueError(
            f"Unknown strategy type: {strategy_type}. "
            f"Valid options: default, scan, round_robin, look, destination_dispatch, ml, adaptive"
        )
