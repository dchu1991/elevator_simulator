"""
Configuration loader for elevator simulation.

This module loads and validates configuration from elevator_config.json
and provides easy access to all settings.
"""

import json
import os
from typing import Dict, Any


class ElevatorConfig:
    """Load and manage elevator simulation configuration"""

    def __init__(self, config_path: str = "config/elevator_config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def reload(self):
        """Reload configuration from file"""
        self.load_config()

    # Building parameters
    @property
    def num_floors(self) -> int:
        return self.config.get("building", {}).get("num_floors", 20)

    @property
    def num_elevators(self) -> int:
        return self.config.get("building", {}).get("num_elevators", 4)

    @property
    def elevator_capacity(self) -> int:
        return self.config.get("building", {}).get("elevator_capacity", 8)

    @property
    def elevator_speed(self) -> float:
        return self.config.get("building", {}).get("elevator_speed", 2.0)

    # Strategy parameters
    @property
    def distance_weight(self) -> float:
        return self.config.get("strategy", {}).get("distance_weight", 1.0)

    @property
    def full_penalty(self) -> int:
        return self.config.get("strategy", {}).get("full_penalty", 50)

    @property
    def same_direction_bonus(self) -> int:
        return self.config.get("strategy", {}).get("same_direction_bonus", -10)

    @property
    def opposite_direction_penalty(self) -> int:
        return self.config.get("strategy", {}).get("opposite_direction_penalty", 20)

    @property
    def load_factor_weight(self) -> int:
        return self.config.get("strategy", {}).get("load_factor_weight", 10)

    @property
    def idle_bonus(self) -> int:
        return self.config.get("strategy", {}).get("idle_bonus", 0)

    # Traffic parameters
    @property
    def base_arrival_rate(self) -> float:
        return self.config.get("traffic", {}).get("base_arrival_rate", 6.0)

    @property
    def rush_multiplier(self) -> float:
        return self.config.get("traffic", {}).get("rush_multiplier", 3.0)

    @property
    def lunch_multiplier(self) -> float:
        return self.config.get("traffic", {}).get("lunch_multiplier", 2.0)

    @property
    def night_multiplier(self) -> float:
        return self.config.get("traffic", {}).get("night_multiplier", 0.2)

    @property
    def enable_realistic_visitors(self) -> bool:
        return self.config.get("traffic", {}).get("enable_realistic_visitors", True)

    # Simulation parameters
    @property
    def control_loop_interval(self) -> float:
        """Returns interval in seconds"""
        ms = self.config.get("simulation", {}).get("control_loop_interval_ms", 100)
        return ms / 1000.0

    @property
    def traffic_check_interval(self) -> float:
        return self.config.get("simulation", {}).get("traffic_check_interval_s", 1.0)

    @property
    def movement_delay_factor(self) -> float:
        return self.config.get("simulation", {}).get("movement_delay_factor", 0.5)

    @property
    def stats_recording_interval(self) -> float:
        return self.config.get("simulation", {}).get("stats_recording_interval_s", 10.0)

    # Behavior parameters
    @property
    def enable_load_balancing(self) -> bool:
        return self.config.get("behavior", {}).get("enable_load_balancing", True)

    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary"""
        return self.config.copy()

    def __repr__(self) -> str:
        return (
            f"ElevatorConfig({self.num_floors} floors, "
            f"{self.num_elevators} elevators)"
        )


# Global config instance
_config_instance = None


def get_config(config_path: str = "config/elevator_config.json") -> ElevatorConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ElevatorConfig(config_path)
    return _config_instance


def reload_config():
    """Reload the global configuration from file"""
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload()
