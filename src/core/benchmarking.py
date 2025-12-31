"""
Performance Benchmarking Framework
==================================

Compare elevator assignment strategies systematically.
Provides tools for benchmarking, metrics collection, and comparison.
"""

import time
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""

    strategy_name: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Simulation parameters
    num_floors: int = 0
    num_elevators: int = 0
    duration_seconds: float = 0.0
    time_scale: float = 1.0

    # Performance metrics
    total_generated: int = 0
    total_completed: int = 0
    total_waiting: int = 0

    avg_wait_time: float = 0.0
    avg_journey_time: float = 0.0
    max_wait_time: float = 0.0
    min_wait_time: float = 0.0

    throughput_per_hour: float = 0.0
    elevator_utilization: float = 0.0

    # Elevator-specific stats
    avg_distance_traveled: float = 0.0
    avg_passengers_served: float = 0.0
    avg_idle_time: float = 0.0

    # Additional metrics
    peak_queue_size: int = 0
    avg_queue_size: float = 0.0

    # Execution time
    wall_clock_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkResult":
        """Create from dictionary"""
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ComparisonReport:
    """Comparison report for multiple strategies"""

    results: List[BenchmarkResult]
    test_config: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_winner(self, metric: str = "avg_wait_time") -> BenchmarkResult:
        """
        Get the best performing strategy for a given metric.

        Args:
            metric: Metric to compare (default: avg_wait_time)

        Returns:
            Best performing BenchmarkResult
        """
        if not self.results:
            raise ValueError("No results to compare")

        # For wait times, lower is better
        if "wait" in metric or "time" in metric:
            return min(self.results, key=lambda r: getattr(r, metric))
        # For throughput/utilization, higher is better
        else:
            return max(self.results, key=lambda r: getattr(r, metric))

    def print_comparison(self):
        """Print formatted comparison table"""
        if not self.results:
            print("No results to compare")
            return

        print("\n" + "=" * 80)
        print("PERFORMANCE COMPARISON")
        print("=" * 80)
        print(f"Test Configuration: {self.test_config}")
        print(f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Header
        print(
            f"{'Strategy':<20} {'Avg Wait':<12} {'Throughput':<12} {'Utilization':<12} {'Completed':<12}"
        )
        print("-" * 80)

        # Results
        for result in self.results:
            print(
                f"{result.strategy_name:<20} "
                f"{result.avg_wait_time:>10.2f}s "
                f"{result.throughput_per_hour:>10.1f}/hr "
                f"{result.elevator_utilization:>10.1f}% "
                f"{result.total_completed:>11d}"
            )

        print("=" * 80)

        # Winners
        print("\nBEST PERFORMERS:")
        print(f"  Lowest Wait Time: {self.get_winner('avg_wait_time').strategy_name}")
        print(
            f"  Highest Throughput: {self.get_winner('throughput_per_hour').strategy_name}"
        )
        print(
            f"  Best Utilization: {self.get_winner('elevator_utilization').strategy_name}"
        )
        print()

    def save_to_file(self, filepath: str):
        """Save comparison report to JSON file"""
        data = {
            "test_config": self.test_config,
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ComparisonReport":
        """Load comparison report from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)

        return cls(
            test_config=data["test_config"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            results=[BenchmarkResult.from_dict(r) for r in data["results"]],
        )


class StrategyBenchmark:
    """Benchmark framework for comparing strategies"""

    def __init__(self, output_dir: str = "benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_benchmark(
        self,
        strategy_name: str,
        create_simulation_func: Callable,
        duration: float = 120.0,
        **config_params,
    ) -> BenchmarkResult:
        """
        Run a single benchmark.

        Args:
            strategy_name: Name of the strategy being tested
            create_simulation_func: Function that creates and returns SimulationEngine
            duration: How long to run simulation (seconds)
            **config_params: Additional config parameters

        Returns:
            BenchmarkResult with metrics
        """
        print(f"\nRunning benchmark: {strategy_name}")
        print(f"Duration: {duration}s")
        print(f"Config: {config_params}")

        # Create simulation
        sim = create_simulation_func(strategy_name=strategy_name, **config_params)

        # Start timing
        start_time = time.time()

        # Run simulation
        with sim:
            time.sleep(duration * sim.time_scale)
            stats = sim.get_current_statistics()

        wall_clock_time = time.time() - start_time

        # Create result
        result = BenchmarkResult(
            strategy_name=strategy_name,
            num_floors=config_params.get("num_floors", 20),
            num_elevators=config_params.get("num_elevators", 4),
            duration_seconds=duration,
            time_scale=getattr(sim, "time_scale", 1.0),
            total_generated=stats.get("total_generated", 0),
            total_completed=stats.get("total_completed", 0),
            total_waiting=stats.get("total_waiting", 0),
            avg_wait_time=stats.get("avg_wait_time", 0.0),
            avg_journey_time=stats.get("avg_journey_time", 0.0),
            max_wait_time=stats.get("max_wait_time", 0.0),
            throughput_per_hour=stats.get("throughput", 0.0),
            elevator_utilization=stats.get("avg_utilization", 0.0),
            wall_clock_time=wall_clock_time,
        )

        print(f"✓ Completed: {result.total_completed} passengers")
        print(f"✓ Avg wait: {result.avg_wait_time:.2f}s")
        print(f"✓ Throughput: {result.throughput_per_hour:.1f}/hr")

        return result

    def compare_strategies(
        self,
        strategies: List[str],
        create_simulation_func: Callable,
        duration: float = 120.0,
        runs_per_strategy: int = 1,
        **config_params,
    ) -> ComparisonReport:
        """
        Compare multiple strategies.

        Args:
            strategies: List of strategy names to compare
            create_simulation_func: Function that creates SimulationEngine
            duration: Duration per run (seconds)
            runs_per_strategy: Number of runs per strategy (for averaging)
            **config_params: Config parameters

        Returns:
            ComparisonReport with results
        """
        print("\n" + "=" * 80)
        print("STRATEGY COMPARISON BENCHMARK")
        print("=" * 80)
        print(f"Strategies: {', '.join(strategies)}")
        print(f"Runs per strategy: {runs_per_strategy}")
        print(f"Duration per run: {duration}s")
        print("=" * 80)

        all_results = []

        for strategy in strategies:
            strategy_results = []

            for run in range(runs_per_strategy):
                if runs_per_strategy > 1:
                    print(f"\n[Run {run + 1}/{runs_per_strategy}]")

                result = self.run_benchmark(
                    strategy, create_simulation_func, duration, **config_params
                )
                strategy_results.append(result)

            # If multiple runs, average the results
            if runs_per_strategy > 1:
                averaged = self._average_results(strategy_results)
                all_results.append(averaged)
            else:
                all_results.append(strategy_results[0])

        # Create comparison report
        report = ComparisonReport(
            results=all_results,
            test_config={
                "duration": duration,
                "runs_per_strategy": runs_per_strategy,
                **config_params,
            },
        )

        # Save report
        filename = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report.save_to_file(str(self.output_dir / filename))

        return report

    def _average_results(self, results: List[BenchmarkResult]) -> BenchmarkResult:
        """Average multiple benchmark results"""
        if not results:
            raise ValueError("No results to average")

        n = len(results)

        return BenchmarkResult(
            strategy_name=results[0].strategy_name,
            num_floors=results[0].num_floors,
            num_elevators=results[0].num_elevators,
            duration_seconds=results[0].duration_seconds,
            time_scale=results[0].time_scale,
            total_generated=sum(r.total_generated for r in results) // n,
            total_completed=sum(r.total_completed for r in results) // n,
            total_waiting=sum(r.total_waiting for r in results) // n,
            avg_wait_time=sum(r.avg_wait_time for r in results) / n,
            avg_journey_time=sum(r.avg_journey_time for r in results) / n,
            max_wait_time=max(r.max_wait_time for r in results),
            min_wait_time=(
                min(r.min_wait_time for r in results)
                if results[0].min_wait_time > 0
                else 0
            ),
            throughput_per_hour=sum(r.throughput_per_hour for r in results) / n,
            elevator_utilization=sum(r.elevator_utilization for r in results) / n,
            wall_clock_time=sum(r.wall_clock_time for r in results) / n,
        )


class QuickBenchmark:
    """Quick benchmark utilities for common scenarios"""

    @staticmethod
    def quick_compare(
        strategies: List[str], duration: float = 60.0
    ) -> ComparisonReport:
        """
        Quick comparison of strategies with default settings.

        Args:
            strategies: List of strategy names
            duration: Duration per test (seconds)

        Returns:
            ComparisonReport
        """
        from src.core.container import create_test_container

        def create_sim(strategy_name: str, **kwargs):
            """Create simulation with specified strategy"""
            container = create_test_container(
                strategy_name=strategy_name,
                config_overrides={
                    "num_floors": kwargs.get("num_floors", 20),
                    "num_elevators": kwargs.get("num_elevators", 4),
                },
            )

            config = container.resolve("config")
            strategy = container.resolve("strategy")

            # Import here to avoid circular dependency
            from src.core.simulation_engine import SimulationEngine

            return SimulationEngine(
                num_floors=config.num_floors,
                num_elevators=config.num_elevators,
                time_scale=0.2,  # Fast for benchmarking
                config=config,
                strategy=strategy,
            )

        benchmark = StrategyBenchmark()
        return benchmark.compare_strategies(
            strategies=strategies,
            create_simulation_func=create_sim,
            duration=duration,
            num_floors=20,
            num_elevators=4,
        )
