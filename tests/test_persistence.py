"""
Tests for Data Persistence
==========================

Test simulation recording, saving, loading, and replay functionality.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from src.core.persistence import (
    SimulationSnapshot,
    SimulationRecording,
    SimulationPersistence,
    SimulationRecorder,
    SimulationReplayer,
)


class TestSimulationSnapshot:
    """Test SimulationSnapshot dataclass"""

    def test_create_snapshot(self):
        """Create a basic snapshot"""
        snapshot = SimulationSnapshot(
            simulation_time=45.5,
            num_floors=20,
            num_elevators=4,
            elevators=[{"id": 0, "floor": 5, "state": "idle"}],
            waiting_people=[{"id": 1, "floor": 1, "destination": 10}],
            statistics={"total_completed": 50, "avg_wait_time": 12.5},
            strategy_name="nearest",
        )

        assert snapshot.simulation_time == 45.5
        assert snapshot.num_floors == 20
        assert len(snapshot.elevators) == 1
        assert snapshot.strategy_name == "nearest"

    def test_snapshot_to_dict(self):
        """Convert snapshot to dictionary"""
        snapshot = SimulationSnapshot(
            simulation_time=30.0, num_floors=15, strategy_name="scan"
        )

        data = snapshot.to_dict()

        assert isinstance(data, dict)
        assert data["simulation_time"] == 30.0
        assert data["num_floors"] == 15
        assert isinstance(data["timestamp"], str)  # ISO format

    def test_snapshot_from_dict(self):
        """Create snapshot from dictionary"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "simulation_time": 60.0,
            "num_floors": 25,
            "num_elevators": 6,
            "elevators": [],
            "waiting_people": [],
            "in_transit_people": [],
            "statistics": {"total_completed": 100},
            "config": {"capacity": 8},
            "strategy_name": "round_robin",
        }

        snapshot = SimulationSnapshot.from_dict(data)

        assert snapshot.simulation_time == 60.0
        assert snapshot.num_floors == 25
        assert snapshot.strategy_name == "round_robin"
        assert isinstance(snapshot.timestamp, datetime)

    def test_snapshot_serialization_roundtrip(self):
        """Test serialize and deserialize preserves data"""
        original = SimulationSnapshot(
            simulation_time=90.0,
            num_floors=30,
            num_elevators=8,
            statistics={"completed": 200, "waiting": 5},
            strategy_name="adaptive",
        )

        data = original.to_dict()
        restored = SimulationSnapshot.from_dict(data)

        assert restored.simulation_time == original.simulation_time
        assert restored.num_floors == original.num_floors
        assert restored.statistics == original.statistics


class TestSimulationRecording:
    """Test SimulationRecording functionality"""

    def test_create_recording(self):
        """Create a simulation recording"""
        recording = SimulationRecording(
            session_id="test_123",
            config={"num_floors": 20},
            strategy_name="nearest",
        )

        assert recording.session_id == "test_123"
        assert recording.strategy_name == "nearest"
        assert len(recording.snapshots) == 0
        assert len(recording.events) == 0

    def test_add_snapshot(self):
        """Add snapshots to recording"""
        recording = SimulationRecording(session_id="test_456")

        snapshot1 = SimulationSnapshot(simulation_time=10.0)
        snapshot2 = SimulationSnapshot(simulation_time=20.0)

        recording.add_snapshot(snapshot1)
        recording.add_snapshot(snapshot2)

        assert len(recording.snapshots) == 2
        assert recording.snapshots[0].simulation_time == 10.0
        assert recording.snapshots[1].simulation_time == 20.0

    def test_add_event(self):
        """Add events to recording"""
        recording = SimulationRecording(session_id="test_789")

        event1 = {"type": "request", "floor": 5, "time": 10.5}
        event2 = {"type": "pickup", "elevator": 0, "time": 15.2}

        recording.add_event(event1)
        recording.add_event(event2)

        assert len(recording.events) == 2
        assert recording.events[0]["type"] == "request"
        assert recording.events[1]["elevator"] == 0

    def test_finalize_recording(self):
        """Finalize a recording"""
        recording = SimulationRecording(session_id="test_final")

        assert recording.end_time is None

        final_stats = {"total_completed": 100, "avg_wait_time": 15.5}
        recording.finalize(final_stats)

        assert recording.end_time is not None
        assert recording.final_statistics == final_stats

    def test_recording_to_dict(self):
        """Convert recording to dictionary"""
        recording = SimulationRecording(
            session_id="dict_test", strategy_name="scan", config={"floors": 20}
        )

        recording.add_snapshot(SimulationSnapshot(simulation_time=10.0))
        recording.finalize({"completed": 50})

        data = recording.to_dict()

        assert data["session_id"] == "dict_test"
        assert data["strategy_name"] == "scan"
        assert len(data["snapshots"]) == 1
        assert isinstance(data["start_time"], str)

    def test_recording_from_dict(self):
        """Create recording from dictionary"""
        data = {
            "session_id": "from_dict_test",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "config": {"num_floors": 15},
            "strategy_name": "nearest",
            "snapshots": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "simulation_time": 30.0,
                    "num_floors": 15,
                    "num_elevators": 3,
                    "elevators": [],
                    "waiting_people": [],
                    "in_transit_people": [],
                    "statistics": {},
                    "config": {},
                    "strategy_name": "nearest",
                }
            ],
            "events": [{"type": "test"}],
            "final_statistics": {"completed": 75},
            "metadata": {"version": "1.0"},
        }

        recording = SimulationRecording.from_dict(data)

        assert recording.session_id == "from_dict_test"
        assert recording.strategy_name == "nearest"
        assert len(recording.snapshots) == 1
        assert len(recording.events) == 1


class TestSimulationPersistence:
    """Test SimulationPersistence class"""

    @pytest.fixture
    def persistence(self):
        """Create persistence with temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield SimulationPersistence(storage_dir=tmpdir)

    def test_create_persistence(self):
        """Create persistence instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SimulationPersistence(storage_dir=tmpdir)
            assert persistence.storage_dir.exists()

    def test_save_recording_uncompressed(self, persistence):
        """Save recording without compression"""
        recording = SimulationRecording(session_id="save_test", strategy_name="nearest")
        recording.add_snapshot(SimulationSnapshot(simulation_time=10.0))
        recording.finalize({"completed": 50})

        filepath = persistence.save_recording(recording, compress=False)

        assert Path(filepath).exists()
        assert filepath.endswith(".json")
        assert not filepath.endswith(".gz")

    def test_save_recording_compressed(self, persistence):
        """Save recording with compression"""
        recording = SimulationRecording(
            session_id="compress_test", strategy_name="scan"
        )
        recording.add_snapshot(SimulationSnapshot(simulation_time=20.0))
        recording.finalize({"completed": 75})

        filepath = persistence.save_recording(recording, compress=True)

        assert Path(filepath).exists()
        assert filepath.endswith(".json.gz")

    def test_load_recording_uncompressed(self, persistence):
        """Load uncompressed recording"""
        # Save first
        original = SimulationRecording(session_id="load_test", strategy_name="nearest")
        original.add_snapshot(SimulationSnapshot(simulation_time=15.0))
        original.finalize({"completed": 60})

        persistence.save_recording(original, compress=False)

        # Load
        loaded = persistence.load_recording("load_test")

        assert loaded.session_id == "load_test"
        assert loaded.strategy_name == "nearest"
        assert len(loaded.snapshots) == 1
        assert loaded.snapshots[0].simulation_time == 15.0

    def test_load_recording_compressed(self, persistence):
        """Load compressed recording"""
        # Save first
        original = SimulationRecording(
            session_id="load_gz_test", strategy_name="round_robin"
        )
        original.add_snapshot(SimulationSnapshot(simulation_time=25.0))
        original.finalize({"completed": 80})

        persistence.save_recording(original, compress=True)

        # Load
        loaded = persistence.load_recording("load_gz_test")

        assert loaded.session_id == "load_gz_test"
        assert loaded.strategy_name == "round_robin"
        assert len(loaded.snapshots) == 1

    def test_list_recordings(self, persistence):
        """List all available recordings"""
        # Create multiple recordings
        for i in range(3):
            recording = SimulationRecording(
                session_id=f"list_test_{i}", strategy_name=f"strategy_{i}"
            )
            recording.finalize({})
            persistence.save_recording(recording, compress=(i % 2 == 0))

        recordings = persistence.list_recordings()

        assert len(recordings) == 3
        assert all("session_id" in r for r in recordings)
        assert all("strategy_name" in r for r in recordings)

    def test_delete_recording(self, persistence):
        """Delete a recording"""
        # Create recording
        recording = SimulationRecording(
            session_id="delete_test", strategy_name="nearest"
        )
        recording.finalize({})
        persistence.save_recording(recording, compress=False)

        # Verify exists
        recordings = persistence.list_recordings()
        assert len(recordings) == 1

        # Delete
        result = persistence.delete_recording("delete_test")

        assert result is True
        recordings = persistence.list_recordings()
        assert len(recordings) == 0

    def test_delete_nonexistent_recording(self, persistence):
        """Delete recording that doesn't exist"""
        result = persistence.delete_recording("nonexistent")
        assert result is False

    def test_save_snapshot(self, persistence):
        """Save individual snapshot"""
        snapshot = SimulationSnapshot(simulation_time=40.0, num_floors=20)

        filepath = persistence.save_snapshot(snapshot, session_id="snapshot_test")

        assert Path(filepath).exists()
        assert "snapshot_" in filepath

    def test_export_to_csv(self, persistence):
        """Export recording to CSV"""
        # Create recording with snapshots
        recording = SimulationRecording(session_id="csv_test", strategy_name="nearest")

        for i in range(3):
            snapshot = SimulationSnapshot(
                simulation_time=i * 10.0,
                statistics={
                    "total_generated": i * 20,
                    "total_completed": i * 15,
                    "total_waiting": i * 5,
                    "avg_wait_time": 10.0 + i,
                    "throughput": 30.0 + i,
                },
            )
            recording.add_snapshot(snapshot)

        recording.finalize({})
        persistence.save_recording(recording, compress=False)

        # Export to CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            persistence.export_to_csv("csv_test", csv_path)

            # Verify CSV file
            assert Path(csv_path).exists()

            with open(csv_path, "r") as f:
                content = f.read()
                assert "Timestamp" in content
                assert "Simulation Time" in content
                assert "Total Completed" in content
        finally:
            Path(csv_path).unlink()


class TestSimulationRecorder:
    """Test SimulationRecorder class"""

    @pytest.fixture
    def recorder(self):
        """Create recorder with temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield SimulationRecorder(storage_dir=tmpdir)

    def test_create_recorder(self):
        """Create a recorder instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = SimulationRecorder(storage_dir=tmpdir)
            assert recorder.recording is None

    def test_start_recording(self, recorder):
        """Start a new recording"""
        config = {"num_floors": 20, "num_elevators": 4}
        metadata = {"version": "1.0", "test": True}

        recorder.start(config=config, strategy_name="nearest", metadata=metadata)

        assert recorder.recording is not None
        assert recorder.recording.config == config
        assert recorder.recording.strategy_name == "nearest"
        assert recorder.recording.metadata == metadata

    def test_record_snapshot(self, recorder):
        """Record snapshots"""
        recorder.start(config={}, strategy_name="test")

        snapshot1 = SimulationSnapshot(simulation_time=10.0)
        snapshot2 = SimulationSnapshot(simulation_time=20.0)

        recorder.record_snapshot(snapshot1)
        recorder.record_snapshot(snapshot2)

        assert len(recorder.recording.snapshots) == 2

    def test_record_event(self, recorder):
        """Record events"""
        recorder.start(config={}, strategy_name="test")

        event1 = {"type": "request", "floor": 5}
        event2 = {"type": "pickup", "elevator": 0}

        recorder.record_event(event1)
        recorder.record_event(event2)

        assert len(recorder.recording.events) == 2

    def test_stop_recording(self, recorder):
        """Stop recording and finalize"""
        recorder.start(config={}, strategy_name="test")

        final_stats = {"total_completed": 100, "avg_wait_time": 15.0}
        recorder.stop(final_stats)

        assert recorder.recording.end_time is not None
        assert recorder.recording.final_statistics == final_stats

    def test_save_recording(self, recorder):
        """Save the recording"""
        recorder.start(config={}, strategy_name="test")
        recorder.record_snapshot(SimulationSnapshot(simulation_time=30.0))
        recorder.stop({"completed": 50})

        filepath = recorder.save(compress=True)

        assert filepath is not None
        assert Path(filepath).exists()

    def test_get_session_id(self, recorder):
        """Get current session ID"""
        assert recorder.get_session_id() is None

        recorder.start(config={}, strategy_name="test")

        session_id = recorder.get_session_id()
        assert session_id is not None
        assert isinstance(session_id, str)

    def test_auto_save_interval(self):
        """Test auto-save functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = SimulationRecorder(storage_dir=tmpdir, auto_save_interval=2)

            recorder.start(config={}, strategy_name="test")

            # Add snapshots - should auto-save after 2nd snapshot
            recorder.record_snapshot(SimulationSnapshot(simulation_time=10.0))
            recorder.record_snapshot(SimulationSnapshot(simulation_time=20.0))

            # Check that file was created
            files = list(Path(tmpdir).glob("sim_*.json.gz"))
            assert len(files) == 1


class TestSimulationReplayer:
    """Test SimulationReplayer class"""

    @pytest.fixture
    def replayer(self):
        """Create replayer with temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test recording
            persistence = SimulationPersistence(storage_dir=tmpdir)
            recording = SimulationRecording(
                session_id="replay_test", strategy_name="nearest"
            )

            for i in range(3):
                snapshot = SimulationSnapshot(
                    simulation_time=i * 10.0,
                    statistics={"completed": i * 10, "waiting": 5 - i},
                )
                recording.add_snapshot(snapshot)

            recording.finalize({"total_completed": 30, "avg_wait_time": 12.0})
            persistence.save_recording(recording, compress=True)

            yield SimulationReplayer(storage_dir=tmpdir)

    def test_create_replayer(self):
        """Create a replayer instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            replayer = SimulationReplayer(storage_dir=tmpdir)
            assert replayer.persistence is not None

    def test_replay_simulation(self, replayer, capsys):
        """Replay a simulation"""
        replayer.replay("replay_test")

        captured = capsys.readouterr()
        assert "REPLAYING SIMULATION" in captured.out
        assert "replay_test" in captured.out
        assert "nearest" in captured.out
        assert "FINAL STATISTICS" in captured.out

    def test_replay_with_callback(self, replayer):
        """Replay with callback function"""
        snapshots_seen = []

        def callback(snapshot):
            snapshots_seen.append(snapshot)

        replayer.replay("replay_test", callback=callback)

        assert len(snapshots_seen) == 3
        assert all(isinstance(s, SimulationSnapshot) for s in snapshots_seen)

    def test_compare_sessions(self, capsys):
        """Compare multiple sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SimulationPersistence(storage_dir=tmpdir)

            # Create multiple recordings
            for i, strategy in enumerate(["nearest", "scan"]):
                recording = SimulationRecording(
                    session_id=f"compare_{i}", strategy_name=strategy
                )
                recording.finalize(
                    {
                        "total_completed": 100 - i * 10,
                        "avg_wait_time": 10.0 + i * 2,
                        "throughput": 50.0 - i * 5,
                    }
                )
                persistence.save_recording(recording, compress=False)

            # Compare
            replayer = SimulationReplayer(storage_dir=tmpdir)
            replayer.compare_sessions(["compare_0", "compare_1"])

            captured = capsys.readouterr()
            assert "COMPARING SIMULATIONS" in captured.out
            assert "nearest" in captured.out
            assert "scan" in captured.out


class TestPersistenceIntegration:
    """Integration tests for persistence"""

    def test_full_recording_workflow(self):
        """Test complete recording workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Start recording
            recorder = SimulationRecorder(storage_dir=tmpdir)
            recorder.start(
                config={"num_floors": 20, "num_elevators": 4},
                strategy_name="nearest",
                metadata={"test": "integration"},
            )

            # Record some data
            for i in range(5):
                snapshot = SimulationSnapshot(
                    simulation_time=i * 15.0,
                    num_floors=20,
                    num_elevators=4,
                    statistics={
                        "total_generated": i * 20,
                        "total_completed": i * 18,
                        "avg_wait_time": 10.0 + i * 0.5,
                    },
                )
                recorder.record_snapshot(snapshot)

                event = {"type": "request", "floor": i + 1, "time": i * 15.0}
                recorder.record_event(event)

            # Finalize
            final_stats = {"total_completed": 90, "avg_wait_time": 12.0}
            recorder.stop(final_stats)

            # Save
            filepath = recorder.save(compress=True)
            assert filepath is not None

            # Load and verify
            persistence = SimulationPersistence(storage_dir=tmpdir)
            session_id = recorder.get_session_id()
            loaded = persistence.load_recording(session_id)

            assert loaded.strategy_name == "nearest"
            assert len(loaded.snapshots) == 5
            assert len(loaded.events) == 5
            assert loaded.final_statistics["total_completed"] == 90

    def test_multiple_recordings_management(self):
        """Test managing multiple recordings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SimulationPersistence(storage_dir=tmpdir)

            # Create multiple recordings
            sessions = []
            for i in range(5):
                recording = SimulationRecording(
                    session_id=f"session_{i}", strategy_name=f"strategy_{i}"
                )
                recording.finalize({"completed": i * 10})
                persistence.save_recording(recording, compress=(i % 2 == 0))
                sessions.append(f"session_{i}")

            # List all
            recordings = persistence.list_recordings()
            assert len(recordings) == 5

            # Delete some
            persistence.delete_recording("session_0")
            persistence.delete_recording("session_2")

            recordings = persistence.list_recordings()
            assert len(recordings) == 3

            # Verify remaining ones can be loaded
            for session_id in ["session_1", "session_3", "session_4"]:
                loaded = persistence.load_recording(session_id)
                assert loaded.session_id == session_id
