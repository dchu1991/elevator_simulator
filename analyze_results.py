"""
Analyze Benchmark Results
=========================

Load and analyze saved benchmark results.
Usage: python analyze_results.py [benchmark_file.json]
"""

import json
import sys
from pathlib import Path
import pandas as pd


def load_latest_results():
    """Load the most recent benchmark results"""
    results_dir = Path("benchmark_results")
    if not results_dir.exists():
        print("No benchmark results found. Run benchmark_strategies.py first!")
        return None

    # Find most recent JSON file
    json_files = sorted(results_dir.glob("benchmark_*.json"), reverse=True)
    if not json_files:
        print("No benchmark JSON files found!")
        return None

    latest = json_files[0]
    print(f"Loading: {latest}")

    with open(latest, "r") as f:
        return json.load(f)


def compare_strategies(data):
    """Compare strategies across metrics"""
    results = data["results"]

    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)

    # Use pandas for nice formatting
    df = pd.DataFrame(
        [
            {
                "Strategy": r["strategy"],
                "Completed": r["total_completed"],
                "Avg Wait (s)": r["avg_wait_time"],
                "Peak Wait (s)": r["peak_wait_time"],
                "Throughput": r["throughput"],
                "Avg Load (%)": r["avg_load_factor"] * 100,
                "Time Full (%)": r["percent_time_any_full"],
            }
            for r in results
        ]
    )
    print(df.to_string(index=False))

    # Rankings
    print("\n" + "=" * 80)
    print("RANKINGS")
    print("=" * 80)

    print("\nBy Throughput (Higher is Better):")
    print(
        df.nlargest(3, "Throughput")[["Strategy", "Throughput"]].to_string(index=False)
    )

    print("\nBy Average Wait Time (Lower is Better):")
    print(
        df.nsmallest(3, "Avg Wait (s)")[["Strategy", "Avg Wait (s)"]].to_string(
            index=False
        )
    )

    print("\nBy Load Factor (Higher = Better Utilization):")
    print(
        df.nlargest(3, "Avg Load (%)")[["Strategy", "Avg Load (%)"]].to_string(
            index=False
        )
    )


def analyze_elevator_distribution(data):
    """Analyze how work is distributed among elevators"""
    print("\n" + "=" * 80)
    print("ELEVATOR WORK DISTRIBUTION")
    print("=" * 80)

    for result in data["results"]:
        strategy = result["strategy"]
        elevators = result["elevator_stats"]

        served_counts = [e["served"] for e in elevators]
        total_served = sum(served_counts)

        if total_served == 0:
            continue

        print(f"\n{strategy.upper()}:")
        print(f"  Total Served: {total_served}")
        print(f"  Distribution:")
        for e in elevators:
            percentage = (e["served"] / total_served * 100) if total_served > 0 else 0
            print(f"    Elevator {e['id']}: {e['served']:3d} ({percentage:5.1f}%)")


def export_for_plotting(data):
    """Export data in format ready for plotting"""
    if not HAS_PANDAS:
        print("\n⚠ Pandas not available - skipping CSV export for plotting")
        print("  Install pandas: uv pip install pandas")
        return

    output_dir = Path("benchmark_results")

    # Strategy comparison data
    df_summary = pd.DataFrame(
        [
            {
                "strategy": r["strategy"],
                "completed": r["total_completed"],
                "avg_wait": r["avg_wait_time"],
                "throughput": r["throughput"],
                "avg_load": r["avg_load_factor"],
            }
            for r in data["results"]
        ]
    )

    csv_file = output_dir / "latest_summary.csv"
    df_summary.to_csv(csv_file, index=False)
    print(f"\n✓ Exported summary to: {csv_file}")

    # Elevator distribution data
    elevator_data = []
    for result in data["results"]:
        for elev in result["elevator_stats"]:
            elevator_data.append(
                {
                    "strategy": result["strategy"],
                    "elevator_id": elev["id"],
                    "served": elev["served"],
                    "efficiency": elev["efficiency"],
                }
            )

    df_elevators = pd.DataFrame(elevator_data)
    csv_file = output_dir / "latest_elevators.csv"
    df_elevators.to_csv(csv_file, index=False)
    print(f"✓ Exported elevator details to: {csv_file}")

    print("\nYou can now plot these with:")
    print("  import pandas as pd")
    print("  import matplotlib.pyplot as plt")
    print(f"  df = pd.read_csv('{csv_file}')")
    print(
        "  df.pivot(index='elevator_id', columns='strategy', values='served').plot(kind='bar')"
    )


if __name__ == "__main__":
    # Load results
    if len(sys.argv) > 1:
        # Load specific file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"File not found: {file_path}")
            sys.exit(1)
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        # Load latest
        data = load_latest_results()

    if data is None:
        sys.exit(1)

    print(f"\nBenchmark from: {data['datetime']}")
    print(f"Duration: {data['duration_minutes']} minutes")
    print(f"Strategies tested: {data['num_strategies']}")

    # Run analysis
    compare_strategies(data)
    analyze_elevator_distribution(data)
    export_for_plotting(data)
