"""
Strategy Comparison Benchmark
==============================

Compare different elevator strategies across multiple metrics.
Uses multiprocessing for parallel execution.
Results are saved to JSON and CSV files for later analysis.
"""

import time
import json
import csv
from datetime import datetime
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from src.core.simulation_engine import SimulationEngine
from src.core.strategy_factory import create_strategy


def run_strategy_test(strategy_name, duration_minutes=5):
    """Run a test with a specific strategy and collect metrics

    This function is designed to run in a separate process.
    """
    print(f"[{strategy_name.upper()}] Starting test...")
    start_time = time.time()

    # Create simulation with specific strategy
    sim = SimulationEngine(
        num_floors=20, num_elevators=4, time_scale=0.1, debug=False  # 10x speed
    )

    # Override strategy
    strategy = create_strategy(strategy_name)
    sim.building.strategy = strategy
    for controller in sim.elevator_controllers:
        controller.strategy = strategy

    sim.start_simulation()

    # Track elevator fullness during simulation
    fullness_samples = []
    sample_count = 60  # Sample 60 times during the run
    sample_interval = (duration_minutes * 60 * 0.1) / sample_count

    for _ in range(sample_count):
        time.sleep(sample_interval)
        # Sample current elevator states
        sample = {
            "full_count": sum(1 for e in sim.building.elevators if e.is_full),
            "avg_load": sum(
                e.passenger_count / e.capacity for e in sim.building.elevators
            )
            / len(sim.building.elevators),
            "max_load": max(
                e.passenger_count / e.capacity for e in sim.building.elevators
            ),
        }
        fullness_samples.append(sample)

    # Collect final stats
    stats = sim.get_current_statistics()

    # Calculate peak wait time from waiting people
    peak_wait = 0.0
    for floor in range(1, 21):
        for person in sim.building.waiting_up[floor]:
            peak_wait = max(peak_wait, person.wait_time)
        for person in sim.building.waiting_down[floor]:
            peak_wait = max(peak_wait, person.wait_time)

    sim.stop_simulation()

    elapsed = time.time() - start_time

    # Calculate fullness metrics
    avg_full_count = sum(s["full_count"] for s in fullness_samples) / len(
        fullness_samples
    )
    avg_load_factor = sum(s["avg_load"] for s in fullness_samples) / len(
        fullness_samples
    )
    peak_load = max(s["max_load"] for s in fullness_samples)
    percent_time_any_full = (
        sum(1 for s in fullness_samples if s["full_count"] > 0)
        / len(fullness_samples)
        * 100
    )

    print(
        f"[{strategy_name.upper()}] Completed in {elapsed:.1f}s - "
        f"{stats['total_people_completed']} served, "
        f"{avg_load_factor*100:.1f}% avg load, "
        f"{percent_time_any_full:.0f}% time with full elevator"
    )

    return {
        "strategy": strategy_name,
        "total_completed": stats["total_people_completed"],
        "avg_wait_time": stats["avg_wait_time"],
        "peak_wait_time": peak_wait,
        "throughput": stats["throughput"],
        "people_waiting": stats["people_waiting"],
        "avg_load_factor": avg_load_factor,
        "peak_load": peak_load,
        "avg_full_count": avg_full_count,
        "percent_time_any_full": percent_time_any_full,
        "elevator_stats": [
            {
                "id": e["id"],
                "served": e["passengers_served"],
                "efficiency": e["efficiency"],
            }
            for e in stats["elevator_stats"]
        ],
    }


def calculate_load_balance_score(elevator_stats):
    """Calculate how balanced the load is (lower = better balance)

    Uses coefficient of variation (CV): std_dev / mean
    Perfect balance = 0, higher = more imbalanced
    """
    import statistics

    served_counts = [e["served"] for e in elevator_stats]

    if sum(served_counts) == 0:
        return 0.0

    mean = statistics.mean(served_counts)
    if mean == 0:
        return 0.0

    std_dev = statistics.stdev(served_counts) if len(served_counts) > 1 else 0
    return std_dev / mean


def print_comparison(results):
    """Print comparison table"""
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON RESULTS")
    print("=" * 80)

    # Header
    print(
        f"{'Strategy':<20} {'Completed':<12} {'Avg Wait':<12} "
        f"{'Peak Wait':<12} {'Throughput':<12} {'Balance':<10}"
    )
    print("-" * 80)

    # Data rows
    for result in results:
        balance = calculate_load_balance_score(result["elevator_stats"])
        print(
            f"{result['strategy']:<20} "
            f"{result['total_completed']:<12} "
            f"{result['avg_wait_time']:<12.2f} "
            f"{result['peak_wait_time']:<12.1f} "
            f"{result['throughput']:<12.1f} "
            f"{balance:<10.3f}"
        )

    print("\n" + "=" * 80)
    print("ELEVATOR CAPACITY UTILIZATION")
    print("=" * 80)

    print(
        f"{'Strategy':<20} {'Avg Load':<12} {'Peak Load':<12} "
        f"{'Avg Full':<12} {'% Time Full':<12}"
    )
    print("-" * 80)

    for result in results:
        print(
            f"{result['strategy']:<20} "
            f"{result['avg_load_factor']*100:<12.1f} "
            f"{result['peak_load']*100:<12.1f} "
            f"{result['avg_full_count']:<12.2f} "
            f"{result['percent_time_any_full']:<12.0f}"
        )

    print("\n" + "=" * 80)
    print("DETAILED ELEVATOR LOAD DISTRIBUTION")
    print("=" * 80)

    for result in results:
        print(f"\n{result['strategy'].upper()}:")
        for elev in result["elevator_stats"]:
            print(
                f"  Elevator {elev['id']}: {elev['served']} served "
                f"({elev['efficiency']:.1f}% efficiency)"
            )

    # Determine winners
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    best_wait = min(results, key=lambda x: x["avg_wait_time"])
    best_throughput = max(results, key=lambda x: x["throughput"])
    best_balance = min(
        results, key=lambda x: calculate_load_balance_score(x["elevator_stats"])
    )

    print(
        f"\n✓ Best Average Wait Time: {best_wait['strategy']} "
        f"({best_wait['avg_wait_time']:.2f}s)"
    )
    print(
        f"✓ Best Throughput: {best_throughput['strategy']} "
        f"({best_throughput['throughput']:.1f} people/hour)"
    )
    print(
        f"✓ Best Load Balance: {best_balance['strategy']} "
        f"(CV: {calculate_load_balance_score(best_balance['elevator_stats']):.3f})"
    )

    print("\nInterpretation:")
    print("  • Lower wait time = faster service")
    print("  • Higher throughput = more people moved")
    print("  • Lower balance score = more even distribution of work")
    print("  • Choose strategy based on your priority!")


def save_results(results, duration_minutes):
    """Save benchmark results to JSON and CSV files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("benchmark_results")
    output_dir.mkdir(exist_ok=True)

    # Prepare data for saving
    benchmark_data = {
        "timestamp": timestamp,
        "datetime": datetime.now().isoformat(),
        "duration_minutes": duration_minutes,
        "num_strategies": len(results),
        "results": results,
    }

    # Save to JSON (complete data)
    json_file = output_dir / f"benchmark_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"\n📊 Detailed results saved to: {json_file}")

    # Save to CSV (summary data for easy analysis)
    csv_file = output_dir / f"benchmark_{timestamp}.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "strategy",
                "total_completed",
                "avg_wait_time",
                "peak_wait_time",
                "throughput",
                "people_waiting",
                "avg_load_factor",
                "peak_load",
                "avg_full_count",
                "percent_time_any_full",
                "load_balance_cv",
            ],
        )
        writer.writeheader()

        for result in results:
            balance_cv = calculate_load_balance_score(result["elevator_stats"])
            writer.writerow(
                {
                    "strategy": result["strategy"],
                    "total_completed": result["total_completed"],
                    "avg_wait_time": result["avg_wait_time"],
                    "peak_wait_time": result["peak_wait_time"],
                    "throughput": result["throughput"],
                    "people_waiting": result["people_waiting"],
                    "avg_load_factor": result["avg_load_factor"],
                    "peak_load": result["peak_load"],
                    "avg_full_count": result["avg_full_count"],
                    "percent_time_any_full": result["percent_time_any_full"],
                    "load_balance_cv": balance_cv,
                }
            )
    print(f"📈 Summary CSV saved to: {csv_file}")

    # Also save elevator details to separate CSV
    details_csv = output_dir / f"benchmark_{timestamp}_elevator_details.csv"
    with open(details_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["strategy", "elevator_id", "passengers_served", "efficiency"]
        )
        writer.writeheader()

        for result in results:
            for elev in result["elevator_stats"]:
                writer.writerow(
                    {
                        "strategy": result["strategy"],
                        "elevator_id": elev["id"],
                        "passengers_served": elev["served"],
                        "efficiency": elev["efficiency"],
                    }
                )
    print(f"🏢 Elevator details saved to: {details_csv}")

    return json_file, csv_file, details_csv


if __name__ == "__main__":
    # Required for multiprocessing on Windows
    mp.freeze_support()

    strategies_to_test = [
        "default",  # NearestCarStrategy
        "round_robin",  # Round robin
        "scan",  # SCAN algorithm
        "look",  # LOOK algorithm
        "destination_dispatch",  # Destination dispatch (now with working tracking!)
        "ml",  # ML-based
        "adaptive",  # Adaptive
    ]

    print("=" * 80)
    print("PARALLEL STRATEGY BENCHMARK")
    print("=" * 80)
    print(f"Testing {len(strategies_to_test)} strategies in parallel...")
    print(f"Using {min(mp.cpu_count(), len(strategies_to_test))} CPU cores")
    print("=" * 80)

    start_time = time.time()
    results = []

    # Use ProcessPoolExecutor for parallel execution
    with ProcessPoolExecutor(
        max_workers=min(mp.cpu_count(), len(strategies_to_test))
    ) as executor:
        # Submit all tasks
        future_to_strategy = {
            executor.submit(run_strategy_test, strategy, 5): strategy
            for strategy in strategies_to_test
        }

        # Collect results as they complete
        for future in as_completed(future_to_strategy):
            strategy = future_to_strategy[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[{strategy.upper()}] Error: {e}")

    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"All tests completed in {total_time:.1f}s")
    print(
        f"Average time per test: {total_time / len(results):.1f}s (with parallelization)"
    )
    print("=" * 80)

    if results:
        print_comparison(results)

        # Save results to files
        duration_minutes = 5  # This should match the test duration
        json_file, csv_file, details_csv = save_results(results, duration_minutes)

        print("\n" + "=" * 80)
        print("💾 All data saved! You can now:")
        print(f"  • Load JSON in Python: json.load(open('{json_file}'))")
        print(f"  • Open CSV in Excel: {csv_file}")
        print(f"  • Analyze with pandas: pd.read_csv('{csv_file}')")
        print("=" * 80)
    else:
        print("No results to compare!")
