#!/usr/bin/env python3
"""
Service Manager for Enhanced Individual Soldier Report System
Manages the lifecycle of all services in the event-driven architecture
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
import time

# Event system imports
try:
    from core.event_bus import EventBus, Event
    from core.events import EventType
except ImportError:
    # Fallback for testing
    class EventBus:
        def subscribe(self, event_type: str, handler): pass
        def publish(self, event): pass
    
    class Event:
        def __init__(self, type, data=None, source=None): 
            self.type = type
            self.data = data
            self.source = source


class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    instance: Any
    status: ServiceStatus
    start_time: Optional[float] = None
    error_message: Optional[str] = None
    dependencies: Optional[List[str]] = None


class ServiceProtocol(Protocol):
    """Protocol that all services should implement"""
    
    async def start_service(self) -> None:
        """Start the service"""
        ...
    
    async def stop_service(self) -> None:
        """Stop the service"""
        ...
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        ...


class ServiceManager:
    """
    Manages the lifecycle of all services in the event-driven architecture.
    Handles service registration, startup, shutdown, and dependency management.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize the service manager
        
        Args:
            event_bus: Central event dispatcher
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self._services: Dict[str, ServiceInfo] = {}
        self._startup_order: List[str] = []
        self._is_shutting_down = False
        
        # Register event handlers
        self._register_event_handlers()
        
        self.logger.info("ServiceManager initialized")
    
    def _register_event_handlers(self) -> None:
        """Register event handlers with the event bus"""
        self.event_bus.subscribe("service_started", self._handle_service_started)
        self.event_bus.subscribe("service_stopped", self._handle_service_stopped)
        self.event_bus.subscribe("service_error", self._handle_service_error)
    
    def register_service(self, name: str, service: ServiceProtocol, 
                        dependencies: Optional[List[str]] = None) -> None:
        """
        Register a service with the manager
        
        Args:
            name: Unique service name
            service: Service instance implementing ServiceProtocol
            dependencies: List of service names this service depends on
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered")
        
        self._services[name] = ServiceInfo(
            name=name,
            instance=service,
            status=ServiceStatus.STOPPED,
            dependencies=dependencies or []
        )
        
        self.logger.info(f"Registered service: {name}")
    
    def unregister_service(self, name: str) -> None:
        """
        Unregister a service
        
        Args:
            name: Service name to unregister
        """
        if name not in self._services:
            self.logger.warning(f"Service '{name}' not found for unregistration")
            return
        
        service_info = self._services[name]
        
        # Stop the service if it's running
        if service_info.status == ServiceStatus.RUNNING:
            asyncio.create_task(self._stop_single_service(name))
        
        del self._services[name]
        self.logger.info(f"Unregistered service: {name}")
    
    async def start_all_services(self) -> None:
        """Start all registered services in dependency order"""
        if self._is_shutting_down:
            self.logger.warning("Cannot start services during shutdown")
            return
        
        self.logger.info("Starting all services...")
        
        # Calculate startup order based on dependencies
        startup_order = self._calculate_startup_order()
        self._startup_order = startup_order
        
        # Start services in order
        for service_name in startup_order:
            if self._is_shutting_down:
                self.logger.info("Startup interrupted by shutdown")
                break
                
            await self._start_single_service(service_name)
        
        self.logger.info("All services startup completed")
        
        # Publish system ready event
        running_services = [name for name, info in self._services.items() 
                          if info.status == ServiceStatus.RUNNING]
        
        self.event_bus.publish(Event(
            type="system_ready",
            data={
                "services_started": running_services,
                "total_services": len(self._services)
            },
            source="ServiceManager"
        ))
    
    async def stop_all_services(self) -> None:
        """Stop all services in reverse startup order"""
        self._is_shutting_down = True
        self.logger.info("Stopping all services...")
        
        # Stop in reverse order
        shutdown_order = list(reversed(self._startup_order)) if self._startup_order else list(self._services.keys())
        
        for service_name in shutdown_order:
            await self._stop_single_service(service_name)
        
        self.logger.info("All services stopped")
        
        # Publish system shutdown event
        self.event_bus.publish(Event(
            type="system_shutdown",
            data={"timestamp": time.time()},
            source="ServiceManager"
        ))
    
    async def restart_service(self, name: str) -> None:
        """
        Restart a specific service
        
        Args:
            name: Service name to restart
        """
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")
        
        self.logger.info(f"Restarting service: {name}")
        
        await self._stop_single_service(name)
        await self._start_single_service(name)
    
    async def _start_single_service(self, name: str) -> None:
        """Start a single service"""
        if name not in self._services:
            self.logger.error(f"Service '{name}' not found")
            return
        
        service_info = self._services[name]
        
        if service_info.status == ServiceStatus.RUNNING:
            self.logger.debug(f"Service '{name}' is already running")
            return
        
        # Check dependencies
        if not self._are_dependencies_ready(name):
            self.logger.error(f"Dependencies not ready for service '{name}'")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = "Dependencies not ready"
            return
        
        try:
            self.logger.info(f"Starting service: {name}")
            service_info.status = ServiceStatus.STARTING
            service_info.start_time = time.time()
            service_info.error_message = None
            
            await service_info.instance.start_service()
            
            service_info.status = ServiceStatus.RUNNING
            self.logger.info(f"Service '{name}' started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service '{name}': {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            
            # Publish error event
            self.event_bus.publish(Event(
                type="service_error",
                data={
                    "service": name,
                    "error": str(e),
                    "operation": "start"
                },
                source="ServiceManager"
            ))
    
    async def _stop_single_service(self, name: str) -> None:
        """Stop a single service"""
        if name not in self._services:
            self.logger.error(f"Service '{name}' not found")
            return
        
        service_info = self._services[name]
        
        if service_info.status in [ServiceStatus.STOPPED, ServiceStatus.STOPPING]:
            self.logger.debug(f"Service '{name}' is already stopped or stopping")
            return
        
        try:
            self.logger.info(f"Stopping service: {name}")
            service_info.status = ServiceStatus.STOPPING
            
            await service_info.instance.stop_service()
            
            service_info.status = ServiceStatus.STOPPED
            service_info.start_time = None
            self.logger.info(f"Service '{name}' stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop service '{name}': {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
    
    def _calculate_startup_order(self) -> List[str]:
        """Calculate the order to start services based on dependencies"""
        order = []
        visited = set()
        temp_visited = set()
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving '{service_name}'")
            
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # Visit dependencies first
            if service_name in self._services:
                dependencies = self._services[service_name].dependencies or []
                for dep in dependencies:
                    if dep not in self._services:
                        raise ValueError(f"Dependency '{dep}' not found for service '{service_name}'")
                    visit(dep)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        # Visit all services
        for service_name in self._services:
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    def _are_dependencies_ready(self, service_name: str) -> bool:
        """Check if all dependencies of a service are running"""
        if service_name not in self._services:
            return False
        
        dependencies = self._services[service_name].dependencies or []
        
        for dep in dependencies:
            if dep not in self._services:
                self.logger.error(f"Dependency '{dep}' not registered")
                return False
            
            if self._services[dep].status != ServiceStatus.RUNNING:
                self.logger.debug(f"Dependency '{dep}' is not running (status: {self._services[dep].status})")
                return False
        
        return True
    
    def _handle_service_started(self, event: Event) -> None:
        """Handle service started events"""
        service_name = event.data.get("service")
        if service_name and service_name in self._services:
            self.logger.debug(f"Received service started event for: {service_name}")
    
    def _handle_service_stopped(self, event: Event) -> None:
        """Handle service stopped events"""
        service_name = event.data.get("service")
        if service_name and service_name in self._services:
            self.logger.debug(f"Received service stopped event for: {service_name}")
    
    def _handle_service_error(self, event: Event) -> None:
        """Handle service error events"""
        service_name = event.data.get("service")
        error = event.data.get("error")
        self.logger.error(f"Service error in '{service_name}': {error}")
    
    # Status and monitoring methods
    def get_service_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific service
        
        Args:
            name: Service name
            
        Returns:
            Service status dictionary or None if not found
        """
        if name not in self._services:
            return None
        
        service_info = self._services[name]
        status = {
            "name": service_info.name,
            "status": service_info.status.value,
            "start_time": service_info.start_time,
            "uptime": time.time() - service_info.start_time if service_info.start_time else None,
            "error_message": service_info.error_message,
            "dependencies": service_info.dependencies
        }
        
        # Get internal service status if available
        try:
            internal_status = service_info.instance.get_service_status()
            status["internal_status"] = internal_status
        except:
            pass
        
        return status
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        return {name: self.get_service_status(name) for name in self._services}
    
    def get_running_services(self) -> List[str]:
        """Get list of currently running services"""
        return [name for name, info in self._services.items() 
                if info.status == ServiceStatus.RUNNING]
    
    def get_failed_services(self) -> List[str]:
        """Get list of failed services"""
        return [name for name, info in self._services.items() 
                if info.status == ServiceStatus.ERROR]
    
    def is_system_ready(self) -> bool:
        """Check if all services are running"""
        return all(info.status == ServiceStatus.RUNNING for info in self._services.values())


# Factory function for creating service manager with common services
def create_service_manager_with_common_services(event_bus: EventBus, 
                                               settings: Optional[Dict[str, Any]] = None) -> ServiceManager:
    """
    Factory function to create a service manager with commonly used services
    
    Args:
        event_bus: Event bus instance
        settings: Optional configuration settings
        
    Returns:
        Configured ServiceManager instance
    """
    manager = ServiceManager(event_bus)
    
    # Import and register common services
    try:
        from performance_scorer import PerformanceScorer
        from safety_analyzer import SafetyAnalyzer
        
        # Try to import additional services if available
        try:
            from data_loader import DataLoader
            from analysis_engine import AnalysisEngine
            from report_generator import ReportGenerator
            
            # Register services with dependencies
            manager.register_service("DataLoader", DataLoader(event_bus, settings))
            
        except ImportError:
            logging.getLogger(__name__).info("DataLoader service not available")
        
        # Core safety and performance services (always available)
        manager.register_service("SafetyAnalyzer", SafetyAnalyzer(event_bus, settings))
        manager.register_service("PerformanceScorer", PerformanceScorer(event_bus, settings))
        
        # Try to register analysis engine if available
        try:
            manager.register_service("AnalysisEngine", AnalysisEngine(event_bus, settings), 
                                    dependencies=["SafetyAnalyzer", "PerformanceScorer"])
        except (ImportError, NameError):
            logging.getLogger(__name__).info("AnalysisEngine service not available")
        
        # Try to register report generator if available
        try:
            manager.register_service("ReportGenerator", ReportGenerator(event_bus, settings),
                                    dependencies=["AnalysisEngine"])
        except (ImportError, NameError):
            logging.getLogger(__name__).info("ReportGenerator service not available")
            
    except ImportError as e:
        logging.getLogger(__name__).warning(f"Could not import some services: {e}")
    
    return manager


async def main():
    """Example usage of the service manager"""
    logging.basicConfig(level=logging.INFO)
    
    # Create event bus (you would use your actual event bus here)
    event_bus = EventBus()
    
    # Create service manager
    manager = create_service_manager_with_common_services(event_bus)
    
    try:
        # Start all services
        await manager.start_all_services()
        
        # Print service status
        print("\n=== Service Status ===")
        for name, status in manager.get_all_services_status().items():
            print(f"{name}: {status['status']}")
        
        print(f"\nSystem Ready: {manager.is_system_ready()}")
        
        # Simulate some work
        await asyncio.sleep(2)
        
    finally:
        # Stop all services
        await manager.stop_all_services()


if __name__ == "__main__":
    asyncio.run(main())