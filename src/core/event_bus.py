"""
Event Bus Implementation (Observer Pattern)
===========================================

Provides event-driven architecture for monitoring elevator system events.
Allows components to publish and subscribe to events without tight coupling.
"""

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


class EventType(Enum):
    """Types of events in the elevator system"""

    # Elevator events
    ELEVATOR_MOVING = "elevator_moving"
    ELEVATOR_ARRIVED = "elevator_arrived"
    ELEVATOR_DOOR_OPENED = "elevator_door_opened"
    ELEVATOR_DOOR_CLOSED = "elevator_door_closed"
    ELEVATOR_IDLE = "elevator_idle"

    # Passenger events
    PERSON_GENERATED = "person_generated"
    PERSON_WAITING = "person_waiting"
    PERSON_BOARDED = "person_boarded"
    PERSON_ARRIVED = "person_arrived"

    # Request events
    REQUEST_CREATED = "request_created"
    REQUEST_ASSIGNED = "request_assigned"
    REQUEST_COMPLETED = "request_completed"

    # System events
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_STOPPED = "simulation_stopped"
    STATISTICS_UPDATED = "statistics_updated"

    # Performance events
    HIGH_WAIT_TIME = "high_wait_time"
    OVERLOAD = "overload"
    EFFICIENCY_CHANGE = "efficiency_change"


@dataclass
class Event:
    """Represents an event in the system"""

    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S.%f')[:-3]}] {self.event_type.value}: {self.data}"


class EventBus:
    """
    Event bus for publish-subscribe pattern.

    Allows components to publish events and subscribe to events without
    direct coupling. Thread-safe for use in multi-threaded simulations.
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()
        self._event_history: List[Event] = []
        self._max_history_size = 1000

    def subscribe(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function that takes an Event parameter
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

    def unsubscribe(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: The handler function to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                except ValueError:
                    pass  # Handler not found

    def publish(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            data: Event data dictionary
            source: Source identifier (e.g., "elevator_1", "traffic_manager")
        """
        event = Event(event_type=event_type, data=data or {}, source=source)

        # Store in history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)

            # Get subscribers
            handlers = self._subscribers.get(event_type, []).copy()

        # Call handlers outside lock to avoid deadlocks
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler for {event_type}: {e}")

    def get_history(
        self, event_type: Optional[EventType] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type (None = all events)
            limit: Maximum number of events to return (None = all)

        Returns:
            List of events, most recent last
        """
        with self._lock:
            events = self._event_history.copy()

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if limit:
            events = events[-limit:]

        return events

    def clear_history(self) -> None:
        """Clear event history"""
        with self._lock:
            self._event_history.clear()

    def get_event_counts(self) -> Dict[EventType, int]:
        """
        Get count of each event type in history.

        Returns:
            Dictionary mapping event types to counts
        """
        with self._lock:
            events = self._event_history.copy()

        counts: Dict[EventType, int] = {}
        for event in events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1

        return counts

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to all event types.

        Args:
            handler: Callback function that takes an Event parameter
        """
        for event_type in EventType:
            self.subscribe(event_type, handler)

    def unsubscribe_all(self, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from all event types.

        Args:
            handler: The handler function to remove
        """
        for event_type in EventType:
            self.unsubscribe(event_type, handler)


class EventLogger:
    """Simple event logger that prints events"""

    def __init__(self, event_bus: EventBus, verbose: bool = True):
        self.event_bus = event_bus
        self.verbose = verbose
        self.log_file = None

    def start(self, log_file: Optional[str] = None):
        """Start logging events"""
        self.log_file = log_file
        self.event_bus.subscribe_all(self._log_event)

    def stop(self):
        """Stop logging events"""
        self.event_bus.unsubscribe_all(self._log_event)
        if self.log_file:
            # Could flush/close file here
            pass

    def _log_event(self, event: Event):
        """Log an event"""
        if self.verbose:
            print(f"EVENT: {event}")

        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(f"{event}\n")


class EventMetrics:
    """Collect metrics from events"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.metrics: Dict[str, Any] = {
            "total_events": 0,
            "events_by_type": {},
            "average_wait_times": [],
            "elevator_movements": 0,
            "passengers_served": 0,
        }

    def start(self):
        """Start collecting metrics"""
        self.event_bus.subscribe(EventType.PERSON_ARRIVED, self._on_person_arrived)
        self.event_bus.subscribe(EventType.ELEVATOR_MOVING, self._on_elevator_moving)
        self.event_bus.subscribe_all(self._on_any_event)

    def stop(self):
        """Stop collecting metrics"""
        self.event_bus.unsubscribe(EventType.PERSON_ARRIVED, self._on_person_arrived)
        self.event_bus.unsubscribe(EventType.ELEVATOR_MOVING, self._on_elevator_moving)
        self.event_bus.unsubscribe_all(self._on_any_event)

    def _on_any_event(self, event: Event):
        """Track all events"""
        self.metrics["total_events"] += 1
        event_type_str = event.event_type.value
        if event_type_str not in self.metrics["events_by_type"]:
            self.metrics["events_by_type"][event_type_str] = 0
        self.metrics["events_by_type"][event_type_str] += 1

    def _on_person_arrived(self, event: Event):
        """Track person arrivals"""
        self.metrics["passengers_served"] += 1
        if "wait_time" in event.data:
            self.metrics["average_wait_times"].append(event.data["wait_time"])

    def _on_elevator_moving(self, event: Event):
        """Track elevator movements"""
        self.metrics["elevator_movements"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        metrics = self.metrics.copy()
        if metrics["average_wait_times"]:
            metrics["avg_wait_time"] = sum(metrics["average_wait_times"]) / len(
                metrics["average_wait_times"]
            )
        else:
            metrics["avg_wait_time"] = 0.0
        return metrics

    def reset(self):
        """Reset metrics"""
        self.metrics = {
            "total_events": 0,
            "events_by_type": {},
            "average_wait_times": [],
            "elevator_movements": 0,
            "passengers_served": 0,
        }
