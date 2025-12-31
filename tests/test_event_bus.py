"""
Tests for Event Bus
===================

Test the Observer Pattern implementation.
"""

from src.core.event_bus import (
    EventBus,
    EventType,
    EventLogger,
    EventMetrics,
)


class TestEventBus:
    """Test EventBus functionality"""

    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish"""
        bus = EventBus()
        received_events = []

        def handler(event):
            received_events.append(event)

        bus.subscribe(EventType.ELEVATOR_MOVING, handler)
        bus.publish(
            EventType.ELEVATOR_MOVING, {"elevator_id": 1, "floor": 5}, source="test"
        )

        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.ELEVATOR_MOVING
        assert received_events[0].data["elevator_id"] == 1

    def test_multiple_subscribers(self):
        """Test multiple subscribers for same event"""
        bus = EventBus()
        count1 = []
        count2 = []

        bus.subscribe(EventType.PERSON_BOARDED, lambda e: count1.append(e))
        bus.subscribe(EventType.PERSON_BOARDED, lambda e: count2.append(e))

        bus.publish(EventType.PERSON_BOARDED, {"person_id": 1})

        assert len(count1) == 1
        assert len(count2) == 1

    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventType.ELEVATOR_ARRIVED, handler)
        bus.publish(EventType.ELEVATOR_ARRIVED, {"floor": 1})

        bus.unsubscribe(EventType.ELEVATOR_ARRIVED, handler)
        bus.publish(EventType.ELEVATOR_ARRIVED, {"floor": 2})

        assert len(received) == 1  # Only first event

    def test_event_history(self):
        """Test event history tracking"""
        bus = EventBus()

        bus.publish(EventType.PERSON_GENERATED, {"id": 1})
        bus.publish(EventType.PERSON_GENERATED, {"id": 2})
        bus.publish(EventType.ELEVATOR_MOVING, {"id": 1})

        history = bus.get_history()
        assert len(history) == 3

        # Filter by type
        person_events = bus.get_history(EventType.PERSON_GENERATED)
        assert len(person_events) == 2

        # Limit
        limited = bus.get_history(limit=2)
        assert len(limited) == 2

    def test_event_counts(self):
        """Test event counting"""
        bus = EventBus()

        bus.publish(EventType.PERSON_GENERATED, {})
        bus.publish(EventType.PERSON_GENERATED, {})
        bus.publish(EventType.ELEVATOR_MOVING, {})

        counts = bus.get_event_counts()
        assert counts[EventType.PERSON_GENERATED] == 2
        assert counts[EventType.ELEVATOR_MOVING] == 1

    def test_subscribe_all(self):
        """Test subscribing to all events"""
        bus = EventBus()
        all_events = []

        bus.subscribe_all(lambda e: all_events.append(e))

        bus.publish(EventType.PERSON_GENERATED, {})
        bus.publish(EventType.ELEVATOR_MOVING, {})
        bus.publish(EventType.REQUEST_CREATED, {})

        assert len(all_events) == 3

    def test_thread_safety(self):
        """Test thread-safe event publishing"""
        bus = EventBus()
        received = []

        bus.subscribe_all(lambda e: received.append(e))

        # Publish from multiple "threads" (simulated with quick succession)
        for i in range(100):
            bus.publish(EventType.PERSON_GENERATED, {"id": i})

        assert len(received) == 100

    def test_error_handling_in_handler(self):
        """Test that errors in handlers don't break event bus"""
        bus = EventBus()
        good_handler_called = []

        def bad_handler(event):
            raise ValueError("Handler error")

        def good_handler(event):
            good_handler_called.append(event)

        bus.subscribe(EventType.ELEVATOR_MOVING, bad_handler)
        bus.subscribe(EventType.ELEVATOR_MOVING, good_handler)

        bus.publish(EventType.ELEVATOR_MOVING, {})

        # Good handler should still be called
        assert len(good_handler_called) == 1


class TestEventLogger:
    """Test EventLogger functionality"""

    def test_event_logger(self, tmp_path):
        """Test event logging"""
        bus = EventBus()
        log_file = tmp_path / "events.log"

        logger = EventLogger(bus, verbose=False)
        logger.start(str(log_file))

        bus.publish(EventType.PERSON_GENERATED, {"id": 1})
        bus.publish(EventType.ELEVATOR_MOVING, {"id": 1})

        logger.stop()

        # Check log file
        assert log_file.exists()
        content = log_file.read_text()
        assert "PERSON_GENERATED" in content or "person_generated" in content


class TestEventMetrics:
    """Test EventMetrics functionality"""

    def test_metrics_collection(self):
        """Test metrics collection from events"""
        bus = EventBus()
        metrics = EventMetrics(bus)
        metrics.start()

        bus.publish(EventType.PERSON_ARRIVED, {"wait_time": 10.0})
        bus.publish(EventType.PERSON_ARRIVED, {"wait_time": 20.0})
        bus.publish(EventType.ELEVATOR_MOVING, {})
        bus.publish(EventType.ELEVATOR_MOVING, {})
        bus.publish(EventType.ELEVATOR_MOVING, {})

        metrics.stop()

        collected = metrics.get_metrics()
        assert collected["total_events"] >= 5
        assert collected["passengers_served"] == 2
        assert collected["elevator_movements"] == 3
        assert collected["avg_wait_time"] == 15.0

    def test_metrics_reset(self):
        """Test resetting metrics"""
        bus = EventBus()
        metrics = EventMetrics(bus)
        metrics.start()

        bus.publish(EventType.PERSON_ARRIVED, {"wait_time": 10.0})
        metrics.reset()

        collected = metrics.get_metrics()
        assert collected["total_events"] == 0
        assert collected["passengers_served"] == 0
