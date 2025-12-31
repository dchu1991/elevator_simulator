"""
Data Persistence - Save and Replay Simulations
==============================================

Save simulation state and replay simulations for analysis.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import gzip


@dataclass
class SimulationSnapshot:
    """Complete snapshot of simulation state at a point in time"""

    timestamp: datetime = field(default_factory=datetime.now)
    simulation_time: float = 0.0

    # Building state
    num_floors: int = 0
    num_elevators: int = 0

    # Elevator states
    elevators: List[Dict[str, Any]] = field(default_factory=list)

    # People states
    waiting_people: List[Dict[str, Any]] = field(default_factory=list)
    in_transit_people: List[Dict[str, Any]] = field(default_factory=list)

    # Statistics
    statistics: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    strategy_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationSnapshot":
        """Create from dictionary"""
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class SimulationRecording:
    """Complete recording of a simulation session"""

    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    strategy_name: str = ""

    # Snapshots taken during simulation
    snapshots: List[SimulationSnapshot] = field(default_factory=list)

    # Events that occurred
    events: List[Dict[str, Any]] = field(default_factory=list)

    # Final statistics
    final_statistics: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_snapshot(self, snapshot: SimulationSnapshot):
        """Add a snapshot to the recording"""
        self.snapshots.append(snapshot)

    def add_event(self, event: Dict[str, Any]):
        """Add an event to the recording"""
        self.events.append(event)

    def finalize(self, final_stats: Dict[str, Any]):
        """Finalize recording with final statistics"""
        self.end_time = datetime.now()
        self.final_statistics = final_stats

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "config": self.config,
            "strategy_name": self.strategy_name,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "events": self.events,
            "final_statistics": self.final_statistics,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationRecording":
        """Create from dictionary"""
        return cls(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=(
                datetime.fromisoformat(data["end_time"])
                if data.get("end_time")
                else None
            ),
            config=data.get("config", {}),
            strategy_name=data.get("strategy_name", ""),
            snapshots=[
                SimulationSnapshot.from_dict(s) for s in data.get("snapshots", [])
            ],
            events=data.get("events", []),
            final_statistics=data.get("final_statistics", {}),
            metadata=data.get("metadata", {}),
        )


class SimulationPersistence:
    """Handles saving and loading simulation data"""

    def __init__(self, storage_dir: str = "simulation_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_recording(
        self, recording: SimulationRecording, compress: bool = True
    ) -> str:
        """
        Save a simulation recording.

        Args:
            recording: SimulationRecording to save
            compress: Whether to use gzip compression

        Returns:
            Path to saved file
        """
        filename = f"sim_{recording.session_id}.json"
        if compress:
            filename += ".gz"

        filepath = self.storage_dir / filename

        data = recording.to_dict()

        if compress:
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        return str(filepath)

    def load_recording(self, session_id: str) -> SimulationRecording:
        """
        Load a simulation recording.

        Args:
            session_id: Session ID of the recording

        Returns:
            SimulationRecording
        """
        # Try compressed first
        filepath = self.storage_dir / f"sim_{session_id}.json.gz"
        if filepath.exists():
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                data = json.load(f)
        else:
            # Try uncompressed
            filepath = self.storage_dir / f"sim_{session_id}.json"
            with open(filepath, "r") as f:
                data = json.load(f)

        return SimulationRecording.from_dict(data)

    def list_recordings(self) -> List[Dict[str, Any]]:
        """
        List all available recordings.

        Returns:
            List of recording metadata
        """
        recordings = []

        for filepath in self.storage_dir.glob("sim_*.json*"):
            try:
                # Quick load just the metadata
                if filepath.suffix == ".gz":
                    with gzip.open(filepath, "rt", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    with open(filepath, "r") as f:
                        data = json.load(f)

                recordings.append(
                    {
                        "session_id": data["session_id"],
                        "start_time": data["start_time"],
                        "end_time": data.get("end_time"),
                        "strategy_name": data.get("strategy_name", "unknown"),
                        "num_snapshots": len(data.get("snapshots", [])),
                        "num_events": len(data.get("events", [])),
                        "filepath": str(filepath),
                    }
                )
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

        return sorted(recordings, key=lambda x: x["start_time"], reverse=True)

    def delete_recording(self, session_id: str) -> bool:
        """
        Delete a recording.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        for pattern in [f"sim_{session_id}.json", f"sim_{session_id}.json.gz"]:
            filepath = self.storage_dir / pattern
            if filepath.exists():
                filepath.unlink()
                return True
        return False

    def save_snapshot(self, snapshot: SimulationSnapshot, session_id: str) -> str:
        """
        Save a single snapshot (for incremental saving).

        Args:
            snapshot: Snapshot to save
            session_id: Session ID

        Returns:
            Path to saved file
        """
        snapshot_dir = self.storage_dir / f"snapshots_{session_id}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = snapshot.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"snapshot_{timestamp}.json"
        filepath = snapshot_dir / filename

        with open(filepath, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

        return str(filepath)

    def export_to_csv(self, session_id: str, output_file: str):
        """
        Export recording statistics to CSV.

        Args:
            session_id: Session ID to export
            output_file: Output CSV filename
        """
        import csv

        recording = self.load_recording(session_id)

        with open(output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(
                [
                    "Timestamp",
                    "Simulation Time",
                    "Total Generated",
                    "Total Completed",
                    "Waiting",
                    "Avg Wait Time",
                    "Throughput",
                ]
            )

            # Data from snapshots
            for snapshot in recording.snapshots:
                stats = snapshot.statistics
                writer.writerow(
                    [
                        snapshot.timestamp.isoformat(),
                        snapshot.simulation_time,
                        stats.get("total_generated", 0),
                        stats.get("total_completed", 0),
                        stats.get("total_waiting", 0),
                        stats.get("avg_wait_time", 0.0),
                        stats.get("throughput", 0.0),
                    ]
                )


class SimulationRecorder:
    """
    Records simulation as it runs.

    Usage:
        recorder = SimulationRecorder()
        recorder.start(config, strategy_name)

        # During simulation
        recorder.record_snapshot(snapshot)
        recorder.record_event(event)

        recorder.stop(final_stats)
        filepath = recorder.save()
    """

    def __init__(
        self,
        storage_dir: str = "simulation_data",
        auto_save_interval: Optional[int] = None,
    ):
        self.persistence = SimulationPersistence(storage_dir)
        self.recording: Optional[SimulationRecording] = None
        self.auto_save_interval = auto_save_interval
        self.snapshot_count = 0

    def start(
        self,
        config: Dict[str, Any],
        strategy_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Start a new recording"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording = SimulationRecording(
            session_id=session_id,
            config=config,
            strategy_name=strategy_name,
            metadata=metadata or {},
        )
        self.snapshot_count = 0

    def record_snapshot(self, snapshot: SimulationSnapshot):
        """Record a snapshot"""
        if self.recording:
            self.recording.add_snapshot(snapshot)
            self.snapshot_count += 1

            # Auto-save if interval specified
            if (
                self.auto_save_interval
                and self.snapshot_count % self.auto_save_interval == 0
            ):
                self.save(compress=True)

    def record_event(self, event: Dict[str, Any]):
        """Record an event"""
        if self.recording:
            self.recording.add_event(event)

    def stop(self, final_stats: Dict[str, Any]):
        """Stop recording"""
        if self.recording:
            self.recording.finalize(final_stats)

    def save(self, compress: bool = True) -> Optional[str]:
        """Save the recording"""
        if self.recording:
            return self.persistence.save_recording(self.recording, compress=compress)
        return None

    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self.recording.session_id if self.recording else None


class SimulationReplayer:
    """Replay a saved simulation"""

    def __init__(self, storage_dir: str = "simulation_data"):
        self.persistence = SimulationPersistence(storage_dir)

    def replay(self, session_id: str, callback: Optional[callable] = None):
        """
        Replay a simulation.

        Args:
            session_id: Session to replay
            callback: Optional callback function called for each snapshot
        """
        recording = self.persistence.load_recording(session_id)

        print(f"\n{'='*80}")
        print(f"REPLAYING SIMULATION: {session_id}")
        print(f"{'='*80}")
        print(f"Strategy: {recording.strategy_name}")
        print(f"Duration: {recording.start_time} -> {recording.end_time}")
        print(f"Snapshots: {len(recording.snapshots)}")
        print(f"Events: {len(recording.events)}")
        print(f"{'='*80}\n")

        for i, snapshot in enumerate(recording.snapshots):
            print(f"\n--- Snapshot {i+1}/{len(recording.snapshots)} ---")
            print(f"Time: {snapshot.simulation_time:.1f}s")
            print(f"Statistics: {snapshot.statistics}")

            if callback:
                callback(snapshot)

        print(f"\n{'='*80}")
        print("FINAL STATISTICS:")
        print(f"{'='*80}")
        for key, value in recording.final_statistics.items():
            print(f"  {key}: {value}")
        print(f"{'='*80}\n")

    def compare_sessions(self, session_ids: List[str]):
        """Compare multiple simulation sessions"""
        print(f"\n{'='*80}")
        print("COMPARING SIMULATIONS")
        print(f"{'='*80}\n")

        recordings = [self.persistence.load_recording(sid) for sid in session_ids]

        # Print comparison table
        print(
            f"{'Session ID':<20} {'Strategy':<20} {'Completed':<12} {'Avg Wait':<12} {'Throughput':<12}"
        )
        print("-" * 80)

        for recording in recordings:
            stats = recording.final_statistics
            print(
                f"{recording.session_id:<20} "
                f"{recording.strategy_name:<20} "
                f"{stats.get('total_completed', 0):>11d} "
                f"{stats.get('avg_wait_time', 0.0):>10.2f}s "
                f"{stats.get('throughput', 0.0):>10.1f}/hr"
            )

        print(f"{'='*80}\n")
