"""
Demo Scenario Loader
====================

Loads and manages demo scenarios from configuration file.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ManualRequest:
    """Represents a manual elevator request"""

    from_floor: int
    to_floor: int


@dataclass
class DemoScenario:
    """Represents a demo scenario configuration"""

    id: str
    name: str
    description: str
    num_floors: int
    num_elevators: int
    duration_seconds: int
    manual_requests: List[ManualRequest]
    request_delay: float
    traffic_enabled: bool
    traffic_automatic: bool
    monitoring_enabled: bool
    monitoring_interval: int
    monitoring_stats: List[str]
    visualization_enabled: bool
    visualization_type: str
    visualization_interval: float
    visualization_frames: int
    show_elevator_performance: bool
    show_final_stats: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DemoScenario":
        """Create scenario from dictionary"""
        building = data.get("building", {})
        manual_reqs = data.get("manual_requests", [])
        traffic = data.get("traffic", {})
        monitoring = data.get("monitoring", {})
        visualization = data.get("visualization", {})

        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Scenario"),
            description=data.get("description", ""),
            num_floors=building.get("num_floors", 15),
            num_elevators=building.get("num_elevators", 3),
            duration_seconds=data.get("duration_seconds", 120),
            manual_requests=[
                ManualRequest(req["from_floor"], req["to_floor"])
                for req in manual_reqs
            ],
            request_delay=data.get("request_delay", 0.0),
            traffic_enabled=traffic.get("enabled", False),
            traffic_automatic=traffic.get("automatic", False),
            monitoring_enabled=monitoring.get("enabled", False),
            monitoring_interval=monitoring.get("interval_seconds", 30),
            monitoring_stats=monitoring.get("show_stats", []),
            visualization_enabled=visualization.get("enabled", False),
            visualization_type=visualization.get("type", "none"),
            visualization_interval=visualization.get("update_interval", 1.0),
            visualization_frames=visualization.get("frames", 0),
            show_elevator_performance=data.get(
                "show_elevator_performance", False
            ),
            show_final_stats=data.get("show_final_stats", True),
        )


class DemoScenarioLoader:
    """Loads demo scenarios from JSON configuration"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to config/demo_scenarios.json
            default_path = (
                Path(__file__).parent.parent.parent
                / "config"
                / "demo_scenarios.json"
            )
            self.config_path = default_path
        else:
            self.config_path = Path(config_path)

        self._scenarios: Dict[str, DemoScenario] = {}
        self._default_scenario_id: str = "quick_demo"
        self._load_scenarios()

    def _load_scenarios(self):
        """Load scenarios from JSON file"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._default_scenario_id = data.get(
                "default_scenario", "quick_demo"
            )

            for scenario_data in data.get("scenarios", []):
                scenario = DemoScenario.from_dict(scenario_data)
                self._scenarios[scenario.id] = scenario

        except FileNotFoundError:
            print(
                f"Warning: Demo scenarios config not found at {self.config_path}"
            )
            print("Using built-in defaults")
            self._create_default_scenarios()
        except json.JSONDecodeError as e:
            print(f"Error parsing demo scenarios config: {e}")
            print("Using built-in defaults")
            self._create_default_scenarios()

    def _create_default_scenarios(self):
        """Create default scenarios if config file is not available"""
        # Create a basic quick demo scenario
        self._scenarios["quick_demo"] = DemoScenario(
            id="quick_demo",
            name="Quick Demonstration",
            description="2-minute demonstration",
            num_floors=15,
            num_elevators=3,
            duration_seconds=120,
            manual_requests=[],
            request_delay=0.0,
            traffic_enabled=True,
            traffic_automatic=True,
            monitoring_enabled=True,
            monitoring_interval=30,
            monitoring_stats=[
                "generated",
                "completed",
                "waiting",
                "avg_wait_time",
            ],
            visualization_enabled=False,
            visualization_type="none",
            visualization_interval=1.0,
            visualization_frames=0,
            show_elevator_performance=False,
            show_final_stats=True,
        )

    def get_scenario(self, scenario_id: str) -> Optional[DemoScenario]:
        """Get a scenario by ID"""
        return self._scenarios.get(scenario_id)

    def get_default_scenario(self) -> Optional[DemoScenario]:
        """Get the default scenario"""
        if self._default_scenario_id in self._scenarios:
            return self._scenarios[self._default_scenario_id]
        if self._scenarios:
            return list(self._scenarios.values())[0]
        return None

    def list_scenarios(self) -> List[str]:
        """List all available scenario IDs"""
        return list(self._scenarios.keys())

    def get_scenario_info(self, scenario_id: str) -> Optional[str]:
        """Get scenario name and description"""
        scenario = self.get_scenario(scenario_id)
        return f"{scenario.name}: {scenario.description}" if scenario else None


# Singleton instance
_loader: Optional[DemoScenarioLoader] = None


def get_demo_loader(config_path: Optional[str] = None) -> DemoScenarioLoader:
    """Get or create the demo scenario loader singleton"""
    global _loader
    if _loader is None:
        _loader = DemoScenarioLoader(config_path)
    return _loader


def load_scenario(scenario_id: str) -> Optional[DemoScenario]:
    """Load a specific demo scenario by ID"""
    loader = get_demo_loader()
    return loader.get_scenario(scenario_id)


def load_default_scenario() -> DemoScenario:
    """Load the default demo scenario"""
    loader = get_demo_loader()
    return loader.get_default_scenario()
