"""
Benchmark Analysis with Pandas
==============================

Load and analyze elevator strategy benchmarks using pandas.
Provides easy access to all benchmark data as DataFrames.
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


class BenchmarkAnalysis:
    """Analyze elevator strategy benchmarks using pandas"""

    def __init__(self, benchmark_file=None):
        """
        Load benchmark data from file or use latest.

        Args:
            benchmark_file: Path to specific benchmark JSON, or None for latest
        """
        if benchmark_file is None:
            benchmark_file = self._find_latest_benchmark()

        self.file_path = Path(benchmark_file)
        with open(self.file_path, "r") as f:
            self.data = json.load(f)

        # Build DataFrames
        self.summary = self._build_summary_df()
        self.elevators = self._build_elevator_df()

        print(f"✓ Loaded: {self.file_path.name}")
        print(f"  Benchmark date: {self.data['datetime']}")
        print(f"  Strategies tested: {len(self.data['results'])}")

    def _find_latest_benchmark(self):
        """Find the most recent benchmark file"""
        results_dir = Path("benchmark_results")
        if not results_dir.exists():
            raise FileNotFoundError(
                "No benchmark results found. Run benchmark_strategies.py first!"
            )

        if json_files := sorted(
            results_dir.glob("benchmark_*.json"), reverse=True
        ):
            return json_files[0]
        else:
            raise FileNotFoundError("No benchmark JSON files found!")

    def _build_summary_df(self):
        """Build summary DataFrame with all strategy metrics"""
        records = []
        for r in self.data["results"]:
            # Calculate load balance CV
            served_counts = [e["served"] for e in r["elevator_stats"]]
            if sum(served_counts) > 0:
                import statistics

                mean = statistics.mean(served_counts)
                std_dev = (
                    statistics.stdev(served_counts) if len(served_counts) > 1 else 0
                )
                balance_cv = std_dev / mean if mean > 0 else 0
            else:
                balance_cv = 0

            records.append(
                {
                    "strategy": r["strategy"],
                    "completed": r["total_completed"],
                    "avg_wait_time": r["avg_wait_time"],
                    "peak_wait_time": r["peak_wait_time"],
                    "throughput": r["throughput"],
                    "people_waiting": r["people_waiting"],
                    "avg_load_pct": r["avg_load_factor"] * 100,
                    "peak_load_pct": r["peak_load"] * 100,
                    "avg_full_count": r["avg_full_count"],
                    "pct_time_any_full": r["percent_time_any_full"],
                    "balance_cv": balance_cv,
                }
            )

        df = pd.DataFrame(records)
        df = df.set_index("strategy")
        return df

    def _build_elevator_df(self):
        """Build elevator-level DataFrame"""
        records = []
        for r in self.data["results"]:
            records.extend(
                {
                    "strategy": r["strategy"],
                    "elevator_id": elev["id"],
                    "served": elev["served"],
                    "efficiency": elev["efficiency"],
                }
                for elev in r["elevator_stats"]
            )
        return pd.DataFrame(records)

    def show_summary(self):
        """Display summary statistics"""
        print("\n" + "=" * 80)
        print("STRATEGY SUMMARY")
        print("=" * 80)

        # Select key columns for display
        display_cols = [
            "completed",
            "avg_wait_time",
            "throughput",
            "avg_load_pct",
            "pct_time_any_full",
            "balance_cv",
        ]
        print(self.summary[display_cols].round(2))

        return self.summary

    def top_strategies(self, metric="throughput", n=3):
        """
        Get top N strategies by metric.

        Args:
            metric: Column name (throughput, avg_wait_time, balance_cv, etc.)
            n: Number of top strategies to return

        Returns:
            DataFrame with top strategies
        """
        ascending = metric in ["avg_wait_time", "peak_wait_time", "balance_cv"]
        return (
            self.summary.nsmallest(n, metric) if ascending else self.summary.nlargest(n, metric)
        )

    def compare(self, strategies=None):
        """
        Compare specific strategies side-by-side.

        Args:
            strategies: List of strategy names, or None for all

        Returns:
            DataFrame comparing strategies
        """
        return self.summary if strategies is None else self.summary.loc[strategies]

    def elevator_distribution(self, strategy=None):
        """
        Get work distribution across elevators.

        Args:
            strategy: Strategy name, or None for all

        Returns:
            DataFrame or pivot table
        """
        if strategy:
            return self.elevators[self.elevators["strategy"] == strategy]

        # Pivot to show all strategies
        return self.elevators.pivot(
            index="elevator_id", columns="strategy", values="served"
        )

    def plot_comparison(self, metric="throughput", figsize=(12, 6)):
        """
        Plot strategy comparison.

        Args:
            metric: Metric to plot
            figsize: Figure size (width, height)
        """
        fig, ax = plt.subplots(figsize=figsize)
        self.summary[metric].sort_values(ascending=False).plot(kind="bar", ax=ax)
        ax.set_title(f'Strategy Comparison: {metric.replace("_", " ").title()}')
        ax.set_xlabel("Strategy")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.grid(axis="y", alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        return fig

    def plot_distribution(self, figsize=(14, 8)):
        """Plot work distribution across elevators for all strategies"""
        pivot = self.elevator_distribution()

        fig, ax = plt.subplots(figsize=figsize)
        pivot.plot(kind="bar", ax=ax)
        ax.set_title("Work Distribution: Passengers Served by Each Elevator")
        ax.set_xlabel("Elevator ID")
        ax.set_ylabel("Passengers Served")
        ax.legend(title="Strategy", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_metrics_heatmap(self, figsize=(12, 8)):
        """Plot heatmap of normalized metrics across strategies"""
        # Normalize metrics to 0-1 scale for comparison
        metrics = ["throughput", "avg_load_pct", "balance_cv", "pct_time_any_full"]
        df_norm = self.summary[metrics].copy()

        # For metrics where lower is better, invert
        for col in ["balance_cv", "pct_time_any_full"]:
            if col in df_norm.columns:
                df_norm[col] = df_norm[col].max() - df_norm[col]

        # Normalize to 0-1
        df_norm = (df_norm - df_norm.min()) / (df_norm.max() - df_norm.min())

        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(df_norm.values, cmap="RdYlGn", aspect="auto")

        # Set ticks
        ax.set_xticks(range(len(df_norm.columns)))
        ax.set_yticks(range(len(df_norm.index)))
        ax.set_xticklabels(df_norm.columns)
        ax.set_yticklabels(df_norm.index)

        # Rotate x labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(
            "Normalized Performance (Higher = Better)", rotation=270, labelpad=20
        )

        # Add values
        for i in range(len(df_norm.index)):
            for j in range(len(df_norm.columns)):
                text = ax.text(
                    j,
                    i,
                    f"{df_norm.iloc[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=9,
                )

        ax.set_title("Strategy Performance Heatmap (Normalized Metrics)")
        plt.tight_layout()
        return fig

    def export_csv(self, output_dir="benchmark_results"):
        """Export DataFrames to CSV files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        summary_file = output_dir / f"analysis_summary_{timestamp}.csv"
        self.summary.to_csv(summary_file)

        elevators_file = output_dir / f"analysis_elevators_{timestamp}.csv"
        self.elevators.to_csv(elevators_file, index=False)

        print(f"\n✓ Exported summary to: {summary_file}")
        print(f"✓ Exported elevators to: {elevators_file}")

        return summary_file, elevators_file


def quick_analysis():
    """Quick analysis of latest benchmark"""
    analysis = BenchmarkAnalysis()

    print("\n" + "=" * 80)
    print("TOP PERFORMERS")
    print("=" * 80)

    print("\n🏆 Best Throughput:")
    print(analysis.top_strategies("throughput", 3)[["throughput", "avg_wait_time"]])

    print("\n⚡ Best Wait Time:")
    print(analysis.top_strategies("avg_wait_time", 3)[["avg_wait_time", "throughput"]])

    print("\n⚖️  Best Load Balance:")
    print(analysis.top_strategies("balance_cv", 3)[["balance_cv", "throughput"]])

    return analysis


if __name__ == "__main__":
    # Run quick analysis
    analysis = quick_analysis()

    # Show full summary
    analysis.show_summary()

    # Example usage
    print("\n" + "=" * 80)
    print("USAGE EXAMPLES")
    print("=" * 80)
    print(
        """
# Load analysis
from benchmark_analysis import BenchmarkAnalysis
analysis = BenchmarkAnalysis()

# Access data as pandas DataFrames
df = analysis.summary  # Strategy summary
elev_df = analysis.elevators  # Elevator-level data

# Query data
analysis.top_strategies('throughput', 3)
analysis.compare(['round_robin', 'ml', 'scan'])
analysis.elevator_distribution('ml')

# Visualize
analysis.plot_comparison('throughput')
analysis.plot_distribution()
analysis.plot_metrics_heatmap()

# Export
analysis.export_csv()
    """
    )
