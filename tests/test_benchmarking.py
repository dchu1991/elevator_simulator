"""
Tests for Performance Benchmarking Framework
============================================

Test benchmark results, comparison reports, and benchmarking framework.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from src.core.benchmarking import (
    BenchmarkResult,
    ComparisonReport,
    StrategyBenchmark,
    QuickBenchmark,
)


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass"""

    def test_create_benchmark_result(self):
        """Create a benchmark result with metrics"""
        result = BenchmarkResult(
            strategy_name="nearest",
            num_floors=20,
            num_elevators=4,
            duration_seconds=120.0,
            total_completed=100,
            avg_wait_time=15.5,
            throughput_per_hour=45.0,
        )

        assert result.strategy_name == "nearest"
        assert result.num_floors == 20
        assert result.total_completed == 100
        assert result.avg_wait_time == 15.5

    def test_result_to_dict(self):
        """Test converting result to dictionary"""
        result = BenchmarkResult(
            strategy_name="scan", total_completed=50, avg_wait_time=20.0
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["strategy_name"] == "scan"
        assert data["total_completed"] == 50
        assert isinstance(data["timestamp"], str)  # ISO format

    def test_result_from_dict(self):
        """Test creating result from dictionary"""
        data = {
            "strategy_name": "nearest",
            "timestamp": datetime.now().isoformat(),
            "num_floors": 15,
            "num_elevators": 3,
            "duration_seconds": 60.0,
            "time_scale": 1.0,
            "total_generated": 100,
            "total_completed": 90,
            "total_waiting": 10,
            "avg_wait_time": 12.5,
            "avg_journey_time": 25.0,
            "max_wait_time": 45.0,
            "min_wait_time": 5.0,
            "throughput_per_hour": 54.0,
            "elevator_utilization": 75.0,
            "avg_distance_traveled": 100.0,
            "avg_passengers_served": 30.0,
            "avg_idle_time": 10.0,
            "peak_queue_size": 8,
            "avg_queue_size": 3.5,
            "wall_clock_time": 2.5,
        }

        result = BenchmarkResult.from_dict(data)

        assert result.strategy_name == "nearest"
        assert result.num_floors == 15
        assert result.total_completed == 90
        assert isinstance(result.timestamp, datetime)

    def test_serialization_roundtrip(self):
        """Test serialize and deserialize preserves data"""
        original = BenchmarkResult(
            strategy_name="round_robin",
            total_completed=75,
            avg_wait_time=18.3,
            throughput_per_hour=37.5,
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = BenchmarkResult.from_dict(data)

        assert restored.strategy_name == original.strategy_name
        assert restored.total_completed == original.total_completed
        assert restored.avg_wait_time == original.avg_wait_time


class TestComparisonReport:
    """Test ComparisonReport functionality"""

    @pytest.fixture
    def sample_results(self):
        """Create sample benchmark results"""
        return [
            BenchmarkResult(
                strategy_name="nearest",
                avg_wait_time=15.0,
                throughput_per_hour=50.0,
                elevator_utilization=70.0,
                total_completed=100,
            ),
            BenchmarkResult(
                strategy_name="scan",
                avg_wait_time=18.0,
                throughput_per_hour=45.0,
                elevator_utilization=65.0,
                total_completed=90,
            ),
            BenchmarkResult(
                strategy_name="round_robin",
                avg_wait_time=20.0,
                throughput_per_hour=40.0,
                elevator_utilization=60.0,
                total_completed=80,
            ),
        ]

    def test_create_comparison_report(self, sample_results):
        """Create a comparison report"""
        report = ComparisonReport(
            results=sample_results, test_config={"duration": 120, "num_floors": 20}
        )

        assert len(report.results) == 3
        assert report.test_config["duration"] == 120
        assert isinstance(report.timestamp, datetime)

    def test_get_winner_wait_time(self, sample_results):
        """Get best strategy for wait time (lower is better)"""
        report = ComparisonReport(results=sample_results)

        winner = report.get_winner("avg_wait_time")

        assert winner.strategy_name == "nearest"
        assert winner.avg_wait_time == 15.0

    def test_get_winner_throughput(self, sample_results):
        """Get best strategy for throughput (higher is better)"""
        report = ComparisonReport(results=sample_results)

        winner = report.get_winner("throughput_per_hour")

        assert winner.strategy_name == "nearest"
        assert winner.throughput_per_hour == 50.0

    def test_get_winner_utilization(self, sample_results):
        """Get best strategy for utilization (higher is better)"""
        report = ComparisonReport(results=sample_results)

        winner = report.get_winner("elevator_utilization")

        assert winner.strategy_name == "nearest"
        assert winner.elevator_utilization == 70.0

    def test_get_winner_empty_results(self):
        """Get winner with no results raises error"""
        report = ComparisonReport(results=[])

        with pytest.raises(ValueError, match="No results to compare"):
            report.get_winner("avg_wait_time")

    def test_print_comparison(self, sample_results, capsys):
        """Test printing comparison table"""
        report = ComparisonReport(results=sample_results)

        report.print_comparison()

        captured = capsys.readouterr()
        assert "PERFORMANCE COMPARISON" in captured.out
        assert "nearest" in captured.out
        assert "scan" in captured.out
        assert "BEST PERFORMERS" in captured.out

    def test_save_to_file(self, sample_results):
        """Test saving report to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            report = ComparisonReport(
                results=sample_results, test_config={"duration": 120}
            )

            report.save_to_file(str(filepath))

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)
                assert "results" in data
                assert len(data["results"]) == 3

    def test_load_from_file(self, sample_results):
        """Test loading report from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"

            # Save first
            original = ComparisonReport(
                results=sample_results, test_config={"duration": 120}
            )
            original.save_to_file(str(filepath))

            # Load
            loaded = ComparisonReport.load_from_file(str(filepath))

            assert len(loaded.results) == 3
            assert loaded.test_config["duration"] == 120
            assert loaded.results[0].strategy_name == "nearest"

    def test_save_creates_directory(self, sample_results):
        """Test that save creates parent directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "report.json"
            report = ComparisonReport(results=sample_results)

            report.save_to_file(str(filepath))

            assert filepath.exists()


class TestStrategyBenchmark:
    """Test StrategyBenchmark class"""

    @pytest.fixture
    def benchmark(self):
        """Create benchmark with temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield StrategyBenchmark(output_dir=tmpdir)

    def test_create_benchmark(self):
        """Create a benchmark instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark = StrategyBenchmark(output_dir=tmpdir)
            assert benchmark.output_dir.exists()

    def test_run_benchmark_basic(self, benchmark):
        """Test running a basic benchmark"""

        def create_mock_sim(strategy_name, **kwargs):
            """Mock simulation"""

            class MockSim:
                time_scale = 0.1

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def get_current_statistics(self):
                    return {
                        "total_generated": 100,
                        "total_completed": 95,
                        "total_waiting": 5,
                        "avg_wait_time": 12.5,
                        "avg_journey_time": 25.0,
                        "max_wait_time": 45.0,
                        "throughput": 47.5,
                        "avg_utilization": 72.0,
                    }

            return MockSim()

        result = benchmark.run_benchmark(
            strategy_name="test_strategy",
            create_simulation_func=create_mock_sim,
            duration=1.0,
            num_floors=20,
            num_elevators=4,
        )

        assert result.strategy_name == "test_strategy"
        assert result.total_completed == 95
        assert result.avg_wait_time == 12.5
        assert result.wall_clock_time > 0

    def test_compare_strategies(self, benchmark):
        """Test comparing multiple strategies"""

        def create_mock_sim(strategy_name, **kwargs):
            """Mock simulation with different results per strategy"""

            class MockSim:
                time_scale = 0.1

                def __init__(self, strategy):
                    self.strategy = strategy

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def get_current_statistics(self):
                    # Different stats based on strategy
                    if self.strategy == "fast":
                        wait_time = 10.0
                        completed = 100
                    else:
                        wait_time = 15.0
                        completed = 90

                    return {
                        "total_generated": 100,
                        "total_completed": completed,
                        "total_waiting": 100 - completed,
                        "avg_wait_time": wait_time,
                        "avg_journey_time": 25.0,
                        "max_wait_time": 45.0,
                        "throughput": 50.0,
                        "avg_utilization": 70.0,
                    }

            return MockSim(strategy_name)

        report = benchmark.compare_strategies(
            strategies=["fast", "slow"],
            create_simulation_func=create_mock_sim,
            duration=0.5,
            runs_per_strategy=1,
            num_floors=20,
            num_elevators=4,
        )

        assert len(report.results) == 2
        assert report.results[0].strategy_name == "fast"
        assert report.results[1].strategy_name == "slow"

    def test_average_results(self, benchmark):
        """Test averaging multiple results"""
        results = [
            BenchmarkResult(
                strategy_name="test",
                avg_wait_time=10.0,
                total_completed=100,
                throughput_per_hour=50.0,
            ),
            BenchmarkResult(
                strategy_name="test",
                avg_wait_time=12.0,
                total_completed=90,
                throughput_per_hour=45.0,
            ),
            BenchmarkResult(
                strategy_name="test",
                avg_wait_time=11.0,
                total_completed=95,
                throughput_per_hour=47.5,
            ),
        ]

        averaged = benchmark._average_results(results)

        assert averaged.strategy_name == "test"
        assert averaged.avg_wait_time == pytest.approx(11.0)
        assert averaged.total_completed == 95  # Integer division
        assert averaged.throughput_per_hour == pytest.approx(47.5)

    def test_average_results_empty(self, benchmark):
        """Test averaging with no results raises error"""
        with pytest.raises(ValueError, match="No results to average"):
            benchmark._average_results([])

    def test_benchmark_creates_output_dir(self):
        """Test that benchmark creates output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "benchmarks"
            benchmark = StrategyBenchmark(output_dir=str(output_dir))

            assert output_dir.exists()
            assert output_dir.is_dir()


class TestQuickBenchmark:
    """Test QuickBenchmark utility class"""

    def test_quick_benchmark_exists(self):
        """Test QuickBenchmark class exists and can be instantiated"""
        qb = QuickBenchmark()
        assert qb is not None

    def test_quick_compare_signature(self):
        """Test quick_compare has correct signature"""
        # Just verify the method exists with correct params
        import inspect

        sig = inspect.signature(QuickBenchmark.quick_compare)
        params = list(sig.parameters.keys())

        assert "strategies" in params
        assert "duration" in params


class TestBenchmarkIntegration:
    """Integration tests for benchmarking"""

    def test_full_benchmark_workflow(self):
        """Test complete benchmark workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:

            def create_mock_sim(strategy_name, **kwargs):
                """Mock simulation"""

                class MockSim:
                    time_scale = 0.01

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        pass

                    def get_current_statistics(self):
                        return {
                            "total_generated": 50,
                            "total_completed": 48,
                            "total_waiting": 2,
                            "avg_wait_time": 8.5,
                            "avg_journey_time": 20.0,
                            "max_wait_time": 30.0,
                            "throughput": 28.8,
                            "avg_utilization": 65.0,
                        }

                return MockSim()

            # Create benchmark
            benchmark = StrategyBenchmark(output_dir=tmpdir)

            # Run comparison
            report = benchmark.compare_strategies(
                strategies=["strategy_a", "strategy_b"],
                create_simulation_func=create_mock_sim,
                duration=0.5,
                runs_per_strategy=1,
                num_floors=10,
                num_elevators=2,
            )

            # Verify results
            assert len(report.results) == 2
            assert report.test_config["duration"] == 0.5

            # Verify file was saved
            json_files = list(Path(tmpdir).glob("comparison_*.json"))
            assert len(json_files) == 1

            # Verify can load it back
            loaded = ComparisonReport.load_from_file(str(json_files[0]))
            assert len(loaded.results) == 2

    def test_benchmark_result_accuracy(self):
        """Test that benchmark captures accurate metrics"""

        def create_mock_sim(strategy_name, **kwargs):
            class MockSim:
                time_scale = 0.1

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def get_current_statistics(self):
                    return {
                        "total_generated": 200,
                        "total_completed": 195,
                        "total_waiting": 5,
                        "avg_wait_time": 14.2,
                        "avg_journey_time": 28.5,
                        "max_wait_time": 55.0,
                        "throughput": 58.5,
                        "avg_utilization": 78.5,
                    }

            return MockSim()

        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark = StrategyBenchmark(output_dir=tmpdir)

            result = benchmark.run_benchmark(
                strategy_name="accurate_test",
                create_simulation_func=create_mock_sim,
                duration=1.0,
                num_floors=25,
                num_elevators=5,
            )

            # Verify all metrics captured
            assert result.total_generated == 200
            assert result.total_completed == 195
            assert result.total_waiting == 5
            assert result.avg_wait_time == 14.2
            assert result.throughput_per_hour == 58.5
            assert result.elevator_utilization == 78.5
            assert result.num_floors == 25
            assert result.num_elevators == 5
