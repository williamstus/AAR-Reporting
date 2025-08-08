<<<<<<< HEAD
# File: tests/unit/test_event_bus.py
"""Unit tests for the event bus system"""

import pytest
import time
import threading
from unittest.mock import Mock, call

from src.core.event_bus import EventBus, EventHandler
from src.core.events import Event, EventType, StatusUpdateEvent


class TestEventBus:
    """Test the EventBus class"""
    
    def test_event_bus_initialization(self):
        """Test event bus initialization"""
        bus = EventBus()
        assert not bus._running
        assert bus._event_queue.empty()
        assert len(bus._subscribers) == 0
    
    def test_subscribe_and_publish(self, event_bus):
        """Test basic subscribe and publish functionality"""
        # Setup
        handler = Mock()
        event_type = EventType.STATUS_UPDATE.value
        test_event = StatusUpdateEvent("Test message")
        
        # Subscribe
        handler_id = event_bus.subscribe(event_type, handler)
        assert handler_id is not None
        
        # Publish and wait for processing
        event_bus.publish_sync(test_event)
        
        # Verify handler was called
        handler.assert_called_once_with(test_event)
    
    def test_multiple_handlers(self, event_bus):
        """Test multiple handlers for same event type"""
        # Setup
        handler1 = Mock()
        handler2 = Mock()
        event_type = EventType.STATUS_UPDATE.value
        test_event = StatusUpdateEvent("Test message")
        
        # Subscribe multiple handlers
        event_bus.subscribe(event_type, handler1, priority=1)
        event_bus.subscribe(event_type, handler2, priority=2)
        
        # Publish
        event_bus.publish_sync(test_event)
        
        # Verify both handlers called
        handler1.assert_called_once_with(test_event)
        handler2.assert_called_once_with(test_event)
    
    def test_handler_priority(self, event_bus):
        """Test handler priority ordering"""
        # Setup
        call_order = []
        
        def handler1(event):
            call_order.append('handler1')
        
        def handler2(event):
            call_order.append('handler2')
        
        event_type = EventType.STATUS_UPDATE.value
        test_event = StatusUpdateEvent("Test message")
        
        # Subscribe with different priorities
        event_bus.subscribe(event_type, handler1, priority=1)
        event_bus.subscribe(event_type, handler2, priority=2)
        
        # Publish
        event_bus.publish_sync(test_event)
        
        # Verify order (higher priority first)
        assert call_order == ['handler2', 'handler1']
    
    def test_unsubscribe(self, event_bus):
        """Test unsubscribing handlers"""
        # Setup
        handler = Mock()
        event_type = EventType.STATUS_UPDATE.value
        test_event = StatusUpdateEvent("Test message")
        
        # Subscribe
        handler_id = event_bus.subscribe(event_type, handler)
        
        # Unsubscribe
        success = event_bus.unsubscribe(event_type, handler_id)
        assert success
        
        # Publish - handler should not be called
        event_bus.publish_sync(test_event)
        handler.assert_not_called()
    
    def test_async_handler(self, event_bus):
        """Test asynchronous handler execution"""
        # Setup
        handler_called = threading.Event()
        
        def async_handler(event):
            handler_called.set()
        
        event_type = EventType.STATUS_UPDATE.value
        test_event = StatusUpdateEvent("Test message")
        
        # Subscribe async handler
        event_bus.subscribe(event_type, async_handler, async_handler=True)
        
        # Publish
        event_bus.publish_sync(test_event)
        
        # Wait for async execution
        assert handler_called.wait(timeout=1.0)
    
    def test_error_handling(self, event_bus):
        """Test error handling in event handlers"""
        # Setup
        def failing_handler(event):
            raise ValueError("Test error")
        
        def working_handler(event):
            working_handler.called = True
        
        working_handler.called = False
        
        event_type = EventType.STATUS_UPDATE.value
        test_event = StatusUpdateEvent("Test message")
        
        # Subscribe both handlers
        event_bus.subscribe(event_type, failing_handler)
        event_bus.subscribe(event_type, working_handler)
        
        # Publish - should not crash
        event_bus.publish_sync(test_event)
        
        # Working handler should still be called
        assert working_handler.called
    
    def test_event_history(self, event_bus):
        """Test event history tracking"""
        # Publish some events
        events = [
            StatusUpdateEvent("Message 1"),
            StatusUpdateEvent("Message 2"),
            StatusUpdateEvent("Message 3")
        ]
        
        for event in events:
            event_bus.publish_sync(event)
        
        # Check history
        history = event_bus.get_recent_events(10)
        assert len(history) == 3
        assert all(e.type == EventType.STATUS_UPDATE.value for e in history)
    
    def test_statistics(self, event_bus):
        """Test event bus statistics"""
        # Setup handler
        handler = Mock()
        event_type = EventType.STATUS_UPDATE.value
        
        event_bus.subscribe(event_type, handler)
        
        # Publish events
        for i in range(5):
            event_bus.publish_sync(StatusUpdateEvent(f"Message {i}"))
        
        # Check stats
        stats = event_bus.get_stats()
        assert stats['running'] == True
        assert stats['events_processed'] == 5
        assert stats['handlers_called'] == 5
        assert event_type in stats['subscribers']
=======
# Event bus unit tests
>>>>>>> dae0a8cb6feadc2779506d88360bd7bf01476064
