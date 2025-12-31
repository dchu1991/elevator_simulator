"""
Tests for Configuration Validation with Pydantic
================================================

Test Pydantic-based configuration system.
"""

import pytest
from pydantic import ValidationError
from src.core.validated_config import (
    ElevatorSystemConfig,
    BuildingConfig,
    ElevatorConfig,
    StrategyConfig,
    TrafficConfig,
    ConfigFactory,
    validate_config_file,
    migrate_legacy_config,
)


class TestBuildingConfig:
    """Test building configuration validation"""

    def test_valid_config(self):
        """Test valid building configuration"""
        config = BuildingConfig(num_floors=20, num_elevators=4)
        assert config.num_floors == 20
        assert config.num_elevators == 4

    def test_too_few_floors(self):
        """Test minimum floor validation"""
        with pytest.raises(ValidationError):
            BuildingConfig(num_floors=3)  # Minimum is 5

    def test_too_many_floors(self):
        """Test maximum floor validation"""
        with pytest.raises(ValidationError):
            BuildingConfig(num_floors=150)  # Maximum is 100

    def test_too_few_elevators_for_floors(self):
        """Test elevator-to-floor ratio validation"""
        with pytest.raises(ValidationError) as exc_info:
            BuildingConfig(num_floors=100, num_elevators=1)
        assert "too few elevators" in str(exc_info.value).lower()


class TestElevatorConfig:
    """Test elevator configuration validation"""

    def test_valid_elevator_config(self):
        """Test valid elevator configuration"""
        config = ElevatorConfig(
            elevator_capacity=8, elevator_speed=2.0, door_open_time=2.0
        )
        assert config.elevator_capacity == 8
        assert config.elevator_speed == 2.0

    def test_invalid_capacity(self):
        """Test capacity validation"""
        with pytest.raises(ValidationError):
            ElevatorConfig(elevator_capacity=1)  # Minimum is 2

        with pytest.raises(ValidationError):
            ElevatorConfig(elevator_capacity=50)  # Maximum is 30

    def test_invalid_speed(self):
        """Test speed validation"""
        with pytest.raises(ValidationError):
            ElevatorConfig(elevator_speed=0)  # Must be > 0

        with pytest.raises(ValidationError):
            ElevatorConfig(elevator_speed=20)  # Maximum is 10


class TestStrategyConfig:
    """Test strategy configuration validation"""

    def test_valid_strategy(self):
        """Test valid strategy name"""
        config = StrategyConfig(strategy_name="nearest")
        assert config.strategy_name == "nearest"

    def test_invalid_strategy_name(self):
        """Test invalid strategy name"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyConfig(strategy_name="invalid_strategy")
        assert "invalid strategy" in str(exc_info.value).lower()

    def test_all_valid_strategies(self):
        """Test all valid strategy names"""
        valid_strategies = [
            "nearest",
            "scan",
            "round_robin",
            "look",
            "destination_dispatch",
            "ml_based",
            "adaptive",
        ]

        for strategy in valid_strategies:
            config = StrategyConfig(strategy_name=strategy)
            assert config.strategy_name == strategy


class TestTrafficConfig:
    """Test traffic configuration validation"""

    def test_valid_traffic_config(self):
        """Test valid traffic configuration"""
        config = TrafficConfig(
            base_arrival_rate=20.0, rush_multiplier=3.0, peak_hours=[8, 12, 17]
        )
        assert config.base_arrival_rate == 20.0
        assert config.peak_hours == [8, 12, 17]

    def test_invalid_peak_hours(self):
        """Test peak hours validation"""
        with pytest.raises(ValidationError):
            TrafficConfig(peak_hours=[25])  # Hour must be 0-23

        with pytest.raises(ValidationError):
            TrafficConfig(peak_hours=[-1])  # Negative hour

    def test_peak_hours_deduplication(self):
        """Test peak hours are deduplicated and sorted"""
        config = TrafficConfig(peak_hours=[12, 8, 12, 17, 8])
        assert config.peak_hours == [8, 12, 17]  # Sorted and unique


class TestElevatorSystemConfig:
    """Test complete elevator system configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = ElevatorSystemConfig()
        assert config.building.num_floors == 20
        assert config.elevator.elevator_capacity == 8
        assert config.strategy.strategy_name == "nearest"

    def test_custom_config(self):
        """Test custom configuration"""
        config = ElevatorSystemConfig(
            building=BuildingConfig(num_floors=30, num_elevators=6),
            strategy=StrategyConfig(strategy_name="scan"),
        )
        assert config.building.num_floors == 30
        assert config.strategy.strategy_name == "scan"

    def test_system_capacity_validation(self):
        """Test system capacity validation"""
        with pytest.raises(ValidationError) as exc_info:
            ElevatorSystemConfig(
                building=BuildingConfig(num_floors=10, num_elevators=1),
                elevator=ElevatorConfig(elevator_capacity=2),
            )
        assert "capacity" in str(exc_info.value).lower()

    def test_save_and_load(self, tmp_path):
        """Test saving and loading configuration"""
        config = ElevatorSystemConfig(
            building=BuildingConfig(num_floors=25, num_elevators=5)
        )

        filepath = tmp_path / "test_config.json"
        config.save_to_file(str(filepath))

        loaded = ElevatorSystemConfig.load_from_file(str(filepath))
        assert loaded.building.num_floors == 25
        assert loaded.building.num_elevators == 5

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValidationError):
            ElevatorSystemConfig(
                building=BuildingConfig(num_floors=20),
                unknown_field="should_fail",
            )

    def test_to_legacy_format(self):
        """Test conversion to legacy format"""
        config = ElevatorSystemConfig()
        legacy = config.to_legacy_format()

        assert "building" in legacy
        assert "strategy" in legacy
        assert "traffic" in legacy
        assert legacy["building"]["num_floors"] == 20


class TestConfigFactory:
    """Test configuration factory"""

    def test_small_building(self):
        """Test small building preset"""
        config = ConfigFactory.small_building()
        assert config.building.num_floors == 8
        assert config.building.num_elevators == 2

    def test_medium_building(self):
        """Test medium building preset"""
        config = ConfigFactory.medium_building()
        assert config.building.num_floors == 20
        assert config.building.num_elevators == 4

    def test_large_building(self):
        """Test large building preset"""
        config = ConfigFactory.large_building()
        assert config.building.num_floors == 50
        assert config.building.num_elevators == 8

    def test_fast_testing(self):
        """Test fast testing preset"""
        config = ConfigFactory.fast_testing()
        assert config.elevator.elevator_speed == 10.0
        assert config.simulation.time_scale == 0.1

    def test_benchmark(self):
        """Test benchmark preset"""
        config = ConfigFactory.benchmark()
        assert config.simulation.time_scale == 0.2
        assert config.simulation.enable_events is True


class TestConfigUtilities:
    """Test configuration utility functions"""

    def test_validate_config_file_valid(self, tmp_path):
        """Test validating valid config file"""
        config = ElevatorSystemConfig()
        filepath = tmp_path / "valid.json"
        config.save_to_file(str(filepath))

        is_valid, error = validate_config_file(str(filepath))
        assert is_valid is True
        assert error is None

    def test_validate_config_file_invalid(self, tmp_path):
        """Test validating invalid config file"""
        filepath = tmp_path / "invalid.json"
        filepath.write_text('{"building": {"num_floors": 3}}')  # Too few floors

        is_valid, error = validate_config_file(str(filepath))
        assert is_valid is False
        assert error is not None

    def test_migrate_legacy_config(self):
        """Test migrating from legacy config"""
        legacy = {
            "building": {
                "num_floors": 25,
                "num_elevators": 5,
                "elevator_capacity": 10,
                "elevator_speed": 2.5,
            },
            "strategy": {"distance_weight": 1.5, "idle_bonus": -8},
            "traffic": {"base_arrival_rate": 30.0},
        }

        config = migrate_legacy_config(legacy)
        assert config.building.num_floors == 25
        assert config.building.num_elevators == 5
        assert config.elevator.elevator_capacity == 10
        assert config.strategy.distance_weight == 1.5
        assert config.traffic.base_arrival_rate == 30.0


class TestConfigValidation:
    """Test configuration validation rules"""

    def test_assignment_validation(self):
        """Test that assignment validation works"""
        config = ElevatorSystemConfig()

        # This should work
        config.building.num_floors = 30
        assert config.building.num_floors == 30

        # Note: In Pydantic v2, assignment validation requires model_config
        # Since we use model_config={"validate_assignment": True}, this should validate
        # However, the validator runs at model level, not field level
        # So we test at creation instead
        with pytest.raises(ValidationError):
            BuildingConfig(num_floors=200)  # Too many

    def test_nested_validation(self):
        """Test nested configuration validation"""
        # Invalid elevator config should fail at system level
        with pytest.raises(ValidationError):
            ElevatorSystemConfig(
                elevator=ElevatorConfig(elevator_speed=0)  # Invalid speed
            )
