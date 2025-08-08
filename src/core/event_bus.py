# File: src/core/event_bus.py
"""Central event bus for the Enhanced Soldier Report System"""

import threading
import queue
import logging
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import traceback

from src.core.events import Event, EventType


class EventHandler:
    """Wrapper for event handlers with metadata"""
    
    def __init__(self, handler: Callable[[Event], None], 
                 priority: int = 0, 
                 async_handler: bool = False,
                 handler_id: str = None):
        self.handler = handler
        self.priority = priority
        self.async_handler = async_handler
        self.handler_id = handler_id or f"{handler.__module__}.{handler.__name__}"
        self.call_count = 0
        self.error_count = 0


class EventBus:
    """Central event bus for decoupled communication between components"""
    
    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._event_queue = queue.Queue(maxsize=queue_size)
        self._processing_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._logger = logging.getLogger(__name__)
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._stats = {
            'events_processed': 0,
            'events_failed': 0,
            'handlers_called': 0
        }
    
    def subscribe(self, 
                  event_type: str, 
                  handler: Callable[[Event], None],
                  priority: int = 0,
                  async_handler: bool = False,
                  handler_id: str = None) -> str:
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
            priority: Handler priority (higher = called first)
            async_handler: Whether to run handler asynchronously
            handler_id: Unique identifier for the handler
            
        Returns:
            Handler ID for unsubscribing
        """
        event_handler = EventHandler(handler, priority, async_handler, handler_id)
        
        # Insert handler in priority order (highest first)
        handlers = self._subscribers[event_type]
        inserted = False
        for i, existing_handler in enumerate(handlers):
            if event_handler.priority > existing_handler.priority:
                handlers.insert(i, event_handler)
                inserted = True
                break
        
        if not inserted:
            handlers.append(event_handler)
        
        self._logger.debug(f"Subscribed {event_handler.handler_id} to {event_type}")
        return event_handler.handler_id
    
    def unsubscribe(self, event_type: str, handler_id: str) -> bool:
        """
        Unsubscribe a handler from an event type
        
        Args:
            event_type: Event type to unsubscribe from
            handler_id: ID of handler to remove
            
        Returns:
            True if handler was found and removed
        """
        handlers = self._subscribers[event_type]
        for i, handler in enumerate(handlers):
            if handler.handler_id == handler_id:
                handlers.pop(i)
                self._logger.debug(f"Unsubscribed {handler_id} from {event_type}")
                return True
        return False
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event: Event to publish
        """
        if not self._running:
            self._logger.warning("Event bus not running, dropping event")
            return
        
        try:
            self._event_queue.put(event, timeout=1.0)
            self._logger.debug(f"Published event {event.type} from {event.source}")
        except queue.Full:
            self._logger.error(f"Event queue full, dropping event {event.type}")
            self._stats['events_failed'] += 1
    
    def publish_sync(self, event: Event) -> None:
        """
        Publish an event synchronously (blocks until all handlers complete)
        
        Args:
            event: Event to publish
        """
        self._process_event(event)
    
    def start(self) -> None:
        """Start the event processing thread"""
        if self._running:
            self._logger.warning("Event bus already running")
            return
        
        self._running = True
        self._processing_thread = threading.Thread(
            target=self._process_events,
            name="EventBusProcessor",
            daemon=True
        )
        self._processing_thread.start()
        self._logger.info("Event bus started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the event processing thread
        
        Args:
            timeout: Maximum time to wait for shutdown
        """
        if not self._running:
            return
        
        self._running = False
        
        # Signal shutdown
        try:
            self._event_queue.put(None, timeout=1.0)
        except queue.Full:
            pass
        
        # Wait for processing thread
        if self._processing_thread:
            self._processing_thread.join(timeout=timeout)
            if self._processing_thread.is_alive():
                self._logger.warning("Event processing thread did not shut down cleanly")
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        self._logger.info("Event bus stopped")
    
    def _process_events(self) -> None:
        """Main event processing loop"""
        self._logger.info("Event processing started")
        
        while self._running:
            try:
                # Get next event (blocking)
                event = self._event_queue.get(timeout=1.0)
                
                # Shutdown signal
                if event is None:
                    break
                
                self._process_event(event)
                
            except queue.Empty:
                continue
            except Exception as e:
                self._logger.error(f"Error in event processing loop: {e}")
                self._stats['events_failed'] += 1
        
        self._logger.info("Event processing stopped")
    
    def _process_event(self, event: Event) -> None:
        """
        Process a single event by calling all subscribers
        
        Args:
            event: Event to process
        """
        try:
            # Add to history
            self._add_to_history(event)
            
            # Get handlers for this event type
            handlers = self._subscribers.get(event.type, [])
            
            if not handlers:
                self._logger.debug(f"No handlers for event {event.type}")
                return
            
            self._logger.debug(f"Processing event {event.type} with {len(handlers)} handlers")
            
            # Call handlers
            for handler in handlers:
                try:
                    if handler.async_handler:
                        # Submit to thread pool
                        self._executor.submit(self._call_handler, handler, event)
                    else:
                        # Call synchronously
                        self._call_handler(handler, event)
                        
                except Exception as e:
                    self._logger.error(f"Error calling handler {handler.handler_id}: {e}")
                    handler.error_count += 1
                    self._stats['events_failed'] += 1
            
            self._stats['events_processed'] += 1
            
        except Exception as e:
            self._logger.error(f"Error processing event {event.type}: {e}")
            self._stats['events_failed'] += 1
    
    def _call_handler(self, handler: EventHandler, event: Event) -> None:
        """
        Call a single event handler
        
        Args:
            handler: Handler to call
            event: Event to pass to handler
        """
        try:
            handler.handler(event)
            handler.call_count += 1
            self._stats['handlers_called'] += 1
            
        except Exception as e:
            self._logger.error(
                f"Handler {handler.handler_id} failed for event {event.type}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            handler.error_count += 1
            raise
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history, maintaining size limit"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        subscriber_stats = {}
        for event_type, handlers in self._subscribers.items():
            subscriber_stats[event_type] = {
                'handler_count': len(handlers),
                'handlers': [
                    {
                        'id': h.handler_id,
                        'priority': h.priority,
                        'async': h.async_handler,
                        'calls': h.call_count,
                        'errors': h.error_count
                    }
                    for h in handlers
                ]
            }
        
        return {
            'running': self._running,
            'queue_size': self._event_queue.qsize(),
            'events_processed': self._stats['events_processed'],
            'events_failed': self._stats['events_failed'],
            'handlers_called': self._stats['handlers_called'],
            'subscribers': subscriber_stats,
            'history_size': len(self._event_history)
        }
    
    def get_recent_events(self, count: int = 50) -> List[Event]:
        """Get recent events from history"""
        return self._event_history[-count:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()