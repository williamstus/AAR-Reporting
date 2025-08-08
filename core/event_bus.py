"""
Fixed Event Bus for AAR System
Handles both dict and object events properly
"""

import threading
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class Event:
    """Event object for the event bus"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str = None


class EventBus:
    """
    Central event bus for system-wide communication
    Supports both dict-style and object-style events
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._event_history: List[Event] = []
        self._max_history = 1000  # Keep last 1000 events
        
        # Middleware functions
        self._middleware: List[Callable] = []
        
        # Event filtering
        self._filters: Dict[str, Callable] = {}
        
        # Statistics
        self._stats = {
            'total_events': 0,
            'events_by_type': {},
            'subscribers_count': 0
        }

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to events of a specific type"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            self._subscribers[event_type].append(callback)
            self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from events of a specific type"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    if not self._subscribers[event_type]:
                        del self._subscribers[event_type]
                    self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())
                except ValueError:
                    pass  # Callback wasn't in the list

    def publish(self, event_data):
        """
        Publish an event
        Accepts both dict-style and Event object-style events
        """
        try:
            # Handle different event formats
            if isinstance(event_data, dict):
                # Dict-style event
                event_type = event_data.get('type', 'unknown')
                event = Event(
                    event_type=event_type,
                    data=event_data,
                    timestamp=datetime.now(),
                    source=event_data.get('source', 'unknown')
                )
            elif hasattr(event_data, 'event_type'):
                # Object-style event
                event = event_data
                event_type = event.event_type
            else:
                # Convert to string and create simple event
                event_type = str(type(event_data).__name__)
                event = Event(
                    event_type=event_type,
                    data={'content': str(event_data)},
                    timestamp=datetime.now(),
                    source='unknown'
                )
            
            # Update statistics
            with self._lock:
                self._stats['total_events'] += 1
                if event_type not in self._stats['events_by_type']:
                    self._stats['events_by_type'][event_type] = 0
                self._stats['events_by_type'][event_type] += 1
                
                # Add to history
                self._event_history.append(event)
                if len(self._event_history) > self._max_history:
                    self._event_history.pop(0)
            
            # Apply middleware
            for middleware_func in self._middleware:
                try:
                    event = middleware_func(event)
                    if event is None:
                        return  # Middleware blocked the event
                except Exception as e:
                    print(f"Middleware error: {e}")
                    continue
            
            # Apply filters
            if event_type in self._filters:
                try:
                    if not self._filters[event_type](event):
                        return  # Event was filtered out
                except Exception as e:
                    print(f"Filter error for {event_type}: {e}")
            
            # Publish to subscribers
            with self._lock:
                subscribers = self._subscribers.get(event_type, []).copy()
            
            for callback in subscribers:
                try:
                    # Call with event data (backward compatibility)
                    callback(event.data)
                except Exception as e:
                    print(f"Subscriber error for {event_type}: {e}")
                    
        except Exception as e:
            print(f"Critical error in event bus: {e}")
            # Don't let event bus errors crash the application

    def add_middleware(self, middleware_func: Callable):
        """Add middleware function that processes all events"""
        self._middleware.append(middleware_func)

    def add_filter(self, event_type: str, filter_func: Callable):
        """Add filter for specific event type"""
        self._filters[event_type] = filter_func

    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """Get recent event history, optionally filtered by type"""
        with self._lock:
            if event_type:
                filtered_events = [e for e in self._event_history if e.event_type == event_type]
                return filtered_events[-limit:]
            else:
                return self._event_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            return {
                'total_events': self._stats['total_events'],
                'events_by_type': self._stats['events_by_type'].copy(),
                'subscribers_count': self._stats['subscribers_count'],
                'active_event_types': list(self._subscribers.keys()),
                'history_size': len(self._event_history)
            }

    def clear_history(self):
        """Clear event history"""
        with self._lock:
            self._event_history.clear()

    def export_history(self, file_path: str, event_type: str = None):
        """Export event history to file"""
        try:
            events_to_export = self.get_event_history(event_type)
            
            export_data = []
            for event in events_to_export:
                export_data.append({
                    'event_type': event.event_type,
                    'timestamp': event.timestamp.isoformat(),
                    'source': event.source,
                    'data': event.data
                })
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Failed to export event history: {e}")

    # Utility methods for common event patterns
    def publish_info(self, message: str, source: str = None, **kwargs):
        """Publish an info event"""
        self.publish({
            'type': 'info',
            'message': message,
            'source': source or 'system',
            **kwargs
        })

    def publish_warning(self, message: str, source: str = None, **kwargs):
        """Publish a warning event"""
        self.publish({
            'type': 'warning',
            'message': message,
            'source': source or 'system',
            **kwargs
        })

    def publish_error(self, message: str, source: str = None, **kwargs):
        """Publish an error event"""
        self.publish({
            'type': 'error',
            'message': message,
            'source': source or 'system',
            **kwargs
        })

    def publish_analysis_event(self, event_type: str, domain: str, **kwargs):
        """Publish an analysis-related event"""
        self.publish({
            'type': event_type,
            'domain': domain,
            'timestamp': datetime.now(),
            **kwargs
        })


# Default middleware functions
def logging_middleware(event: Event) -> Event:
    """Middleware that logs all events"""
    try:
        timestamp = event.timestamp.strftime('%H:%M:%S')
        print(f"[EVENT {timestamp}] {event.event_type}: {event.source}")
    except Exception:
        pass  # Don't let logging errors break the event bus
    
    return event


def correlation_middleware(event: Event) -> Event:
    """Middleware that adds correlation IDs to events"""
    try:
        if 'correlation_id' not in event.data:
            import uuid
            event.data['correlation_id'] = str(uuid.uuid4())[:8]
    except Exception:
        pass
    
    return event


def timestamp_middleware(event: Event) -> Event:
    """Middleware that ensures events have timestamps"""
    try:
        if not hasattr(event, 'timestamp') or event.timestamp is None:
            event.timestamp = datetime.now()
    except Exception:
        pass
    
    return event


# Utility function to create a configured event bus
def create_default_event_bus(enable_logging: bool = False) -> EventBus:
    """Create an event bus with default configuration"""
    bus = EventBus()
    
    # Add default middleware
    bus.add_middleware(timestamp_middleware)
    bus.add_middleware(correlation_middleware)
    
    if enable_logging:
        bus.add_middleware(logging_middleware)
    
    return bus