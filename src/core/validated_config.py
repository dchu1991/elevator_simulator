"""
Configuration Validation with Pydantic
======================================

Type-safe configuration with validation rules.
Replaces the dataclass-based ElevatorConfig with Pydantic models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import json


class BuildingConfig(BaseModel):
    """Building-specific configuration"""

    num_floors: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Number of floors in the building",
    )
    num_elevators: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Number of elevators",
    )
    floor_height_meters: float = Field(
        default=3.5,
        gt=0,
        le=10,
        description="Height of each floor in meters",
    )

    @field_validator("num_elevators")
    @classmethod
    def validate_elevator_ratio(cls, v, info):
        """Ensure reasonable elevator-to-floor ratio"""
        if "num_floors" in info.data:
            ratio = info.data["num_floors"] / v
            if ratio > 20:
                raise ValueError(
                    f"Too few elevators for {info.data['num_floors']} floors. "
                    f"Recommended: at least {info.data['num_floors'] // 15} elevators"
                )
        return v


class ElevatorConfig(BaseModel):
    """Individual elevator configuration"""

    elevator_capacity: int = Field(
        default=8,
        ge=2,
        le=30,
        description="Maximum number of passengers per elevator",
    )
    elevator_speed: float = Field(
        default=2.0,
        gt=0,
        le=10,
        description="Elevator speed in floors per second",
    )
    door_open_time: float = Field(
        default=2.0,
        ge=0.5,
        le=10,
        description="Time to open/close doors (seconds)",
    )
    loading_time_per_person: float = Field(
        default=1.0,
        ge=0.1,
        le=5,
        description="Time for one person to board/exit (seconds)",
    )


class StrategyConfig(BaseModel):
    """Strategy algorithm configuration"""

    strategy_name: str = Field(
        default="nearest",
        description="Name of the strategy to use",
    )

    # Scoring weights
    distance_weight: float = Field(
        default=1.0,
        ge=0,
        description="Weight for distance in scoring",
    )
    load_weight: float = Field(
        default=1.0,
        ge=0,
        description="Weight for elevator load in scoring",
    )
    full_penalty: float = Field(
        default=50.0,
        ge=0,
        description="Penalty for full elevators",
    )
    idle_bonus: float = Field(
        default=-5.0,
        description="Bonus for idle elevators (negative = prefer idle)",
    )
    same_direction_bonus: float = Field(
        default=-5.0,
        description="Bonus for same direction (negative = prefer)",
    )
    opposite_direction_penalty: float = Field(
        default=20.0,
        ge=0,
        description="Penalty for opposite direction",
    )

    @field_validator("strategy_name")
    @classmethod
    def validate_strategy_name(cls, v):
        """Ensure strategy name is valid"""
        valid_strategies = [
            "nearest",
            "scan",
            "round_robin",
            "look",
            "destination_dispatch",
            "ml_based",
            "adaptive",
        ]
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid strategy '{v}'. Must be one of: {', '.join(valid_strategies)}"
            )
        return v


class TrafficConfig(BaseModel):
    """Traffic generation configuration"""

    base_arrival_rate: float = Field(
        default=20.0,
        ge=0.1,
        le=1000,
        description="Base arrival rate (people per minute)",
    )
    rush_multiplier: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Traffic multiplier during rush hours",
    )
    peak_hours: List[int] = Field(
        default=[8, 9, 12, 13, 17, 18],
        description="Peak hours (0-23)",
    )
    enable_realistic_visitors: bool = Field(
        default=True,
        description="Use realistic floor popularity distribution",
    )

    @field_validator("peak_hours")
    @classmethod
    def validate_peak_hours(cls, v):
        """Ensure peak hours are valid"""
        if not all(0 <= hour <= 23 for hour in v):
            raise ValueError("Peak hours must be between 0 and 23")
        return sorted(set(v))  # Remove duplicates and sort


class SimulationConfig(BaseModel):
    """Simulation timing and control configuration"""

    time_scale: float = Field(
        default=1.0,
        gt=0,
        le=100,
        description="Time scale multiplier (1.0 = real-time)",
    )
    control_loop_interval: float = Field(
        default=0.1,
        gt=0,
        le=1.0,
        description="Control loop interval (seconds)",
    )
    stats_recording_interval: float = Field(
        default=10.0,
        gt=0,
        description="Statistics recording interval (seconds)",
    )
    enable_events: bool = Field(
        default=False,
        description="Enable event bus for monitoring",
    )
    enable_persistence: bool = Field(
        default=False,
        description="Enable simulation recording",
    )


class ElevatorSystemConfig(BaseModel):
    """Complete elevator system configuration with validation"""

    building: BuildingConfig = Field(default_factory=BuildingConfig)
    elevator: ElevatorConfig = Field(default_factory=ElevatorConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    traffic: TrafficConfig = Field(default_factory=TrafficConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)

    # Metadata
    config_version: str = Field(default="2.0", description="Configuration version")
    description: Optional[str] = Field(
        default=None, description="Configuration description"
    )

    @model_validator(mode="after")
    def validate_complete_config(self):
        """Validate relationships between config sections"""
        # Check elevator capacity vs traffic
        max_capacity = self.building.num_elevators * self.elevator.elevator_capacity
        if max_capacity < 10:
            raise ValueError(
                f"Total system capacity ({max_capacity}) is very low. "
                f"Consider more elevators or larger capacity."
            )

        # Warn if speed is very high
        if self.elevator.elevator_speed > 5.0:
            import warnings

            warnings.warn(
                f"Elevator speed {self.elevator.elevator_speed} is very high. "
                f"This may cause unrealistic behavior."
            )

        return self

    @classmethod
    def load_from_file(cls, filepath: str) -> "ElevatorSystemConfig":
        """Load configuration from JSON file"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(path, "r") as f:
            data = json.load(f)

        return cls(**data)

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            # Use model_dump() for Pydantic v2
            json.dump(self.model_dump(), f, indent=2)

    def to_legacy_format(self) -> dict:
        """Convert to legacy config format for backward compatibility"""
        return {
            "building": {
                "num_floors": self.building.num_floors,
                "num_elevators": self.building.num_elevators,
                "elevator_capacity": self.elevator.elevator_capacity,
                "elevator_speed": self.elevator.elevator_speed,
            },
            "strategy": {
                "distance_weight": self.strategy.distance_weight,
                "load_factor_weight": self.strategy.load_weight,
                "full_penalty": self.strategy.full_penalty,
                "idle_bonus": self.strategy.idle_bonus,
                "same_direction_bonus": self.strategy.same_direction_bonus,
                "opposite_direction_penalty": self.strategy.opposite_direction_penalty,
            },
            "traffic": {
                "base_arrival_rate": self.traffic.base_arrival_rate,
                "rush_multiplier": self.traffic.rush_multiplier,
                "enable_realistic_visitors": self.traffic.enable_realistic_visitors,
            },
            "simulation": {
                "control_loop_interval_ms": int(
                    self.simulation.control_loop_interval * 1000
                ),
                "stats_recording_interval_s": self.simulation.stats_recording_interval,
            },
        }

    model_config = {
        "validate_assignment": True,  # Validate on assignment
        "extra": "forbid",  # Forbid extra fields
        "json_schema_extra": {
            "examples": [
                {
                    "building": {"num_floors": 20, "num_elevators": 4},
                    "elevator": {"elevator_capacity": 8, "elevator_speed": 2.0},
                    "strategy": {"strategy_name": "nearest"},
                    "traffic": {"base_arrival_rate": 20.0},
                    "simulation": {"time_scale": 1.0},
                }
            ]
        },
    }


class ConfigFactory:
    """Factory for creating common configurations"""

    @staticmethod
    def small_building() -> ElevatorSystemConfig:
        """Configuration for small building (5-10 floors)"""
        return ElevatorSystemConfig(
            building=BuildingConfig(num_floors=8, num_elevators=2),
            elevator=ElevatorConfig(elevator_capacity=6, elevator_speed=1.5),
            traffic=TrafficConfig(base_arrival_rate=10.0),
        )

    @staticmethod
    def medium_building() -> ElevatorSystemConfig:
        """Configuration for medium building (10-30 floors)"""
        return ElevatorSystemConfig(
            building=BuildingConfig(num_floors=20, num_elevators=4),
            elevator=ElevatorConfig(elevator_capacity=8, elevator_speed=2.0),
            traffic=TrafficConfig(base_arrival_rate=20.0),
        )

    @staticmethod
    def large_building() -> ElevatorSystemConfig:
        """Configuration for large building (30+ floors)"""
        return ElevatorSystemConfig(
            building=BuildingConfig(num_floors=50, num_elevators=8),
            elevator=ElevatorConfig(elevator_capacity=10, elevator_speed=3.0),
            traffic=TrafficConfig(base_arrival_rate=40.0, rush_multiplier=4.0),
        )

    @staticmethod
    def fast_testing() -> ElevatorSystemConfig:
        """Configuration optimized for fast testing"""
        return ElevatorSystemConfig(
            building=BuildingConfig(num_floors=10, num_elevators=3),
            elevator=ElevatorConfig(
                elevator_capacity=6,  # Increased to meet validation (3*6=18 > 10)
                elevator_speed=10.0,  # Very fast
                door_open_time=0.5,
                loading_time_per_person=0.1,
            ),
            traffic=TrafficConfig(base_arrival_rate=30.0),
            simulation=SimulationConfig(time_scale=0.1),  # 10x faster
        )

    @staticmethod
    def benchmark() -> ElevatorSystemConfig:
        """Configuration for benchmarking strategies"""
        return ElevatorSystemConfig(
            building=BuildingConfig(num_floors=20, num_elevators=4),
            elevator=ElevatorConfig(elevator_capacity=8, elevator_speed=2.0),
            traffic=TrafficConfig(base_arrival_rate=25.0, rush_multiplier=3.0),
            simulation=SimulationConfig(time_scale=0.2, enable_events=True),
        )


# Utility functions
def validate_config_file(filepath: str) -> tuple[bool, Optional[str]]:
    """
    Validate a configuration file.

    Returns:
        (is_valid, error_message)
    """
    try:
        ElevatorSystemConfig.load_from_file(filepath)
        return True, None
    except Exception as e:
        return False, str(e)


def migrate_legacy_config(old_config: dict) -> ElevatorSystemConfig:
    """
    Migrate from legacy config format to Pydantic config.

    Args:
        old_config: Dictionary from old config system

    Returns:
        New ElevatorSystemConfig
    """
    # Extract and map old config fields
    building = old_config.get("building", {})
    strategy = old_config.get("strategy", {})
    traffic = old_config.get("traffic", {})
    simulation = old_config.get("simulation", {})

    return ElevatorSystemConfig(
        building=BuildingConfig(
            num_floors=building.get("num_floors", 20),
            num_elevators=building.get("num_elevators", 4),
        ),
        elevator=ElevatorConfig(
            elevator_capacity=building.get("elevator_capacity", 8),
            elevator_speed=building.get("elevator_speed", 2.0),
        ),
        strategy=StrategyConfig(
            distance_weight=strategy.get("distance_weight", 1.0),
            load_weight=strategy.get("load_factor_weight", 1.0),
            full_penalty=strategy.get("full_penalty", 50.0),
            idle_bonus=strategy.get("idle_bonus", -5.0),
            same_direction_bonus=strategy.get("same_direction_bonus", -5.0),
            opposite_direction_penalty=strategy.get("opposite_direction_penalty", 20.0),
        ),
        traffic=TrafficConfig(
            base_arrival_rate=traffic.get("base_arrival_rate", 20.0),
            rush_multiplier=traffic.get("rush_multiplier", 3.0),
            enable_realistic_visitors=traffic.get("enable_realistic_visitors", True),
        ),
        simulation=SimulationConfig(
            control_loop_interval=simulation.get("control_loop_interval_ms", 100)
            / 1000.0,
            stats_recording_interval=simulation.get("stats_recording_interval_s", 10.0),
        ),
    )
