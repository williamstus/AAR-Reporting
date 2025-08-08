"""
Enhanced Analysis Orchestrator with Task Management
Manages multiple analysis engines and task execution
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading
import queue
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future

from core.models import AnalysisEngine, AnalysisResult, Alert, AnalysisDomain, AnalysisTask
from core.event_bus import EventBus


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AnalysisTaskResult:
    """Result of an analysis task execution"""
    task_id: str
    domain: AnalysisDomain
    status: TaskStatus
    result: Optional[AnalysisResult]
    error: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    execution_time: Optional[float]


class AnalysisOrchestrator:
    """
    Enhanced orchestrator for managing analysis engines and task execution
    Provides thread-safe task queuing, execution, and result management
    """
    
    def __init__(self, event_bus: EventBus, max_workers: int = 4):
        self.event_bus = event_bus
        self.engines: Dict[AnalysisDomain, AnalysisEngine] = {}
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, AnalysisTaskResult] = {}
        self.completed_tasks: Dict[str, AnalysisTaskResult] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.worker_thread = None
        self._lock = threading.Lock()
        
        # Task execution callbacks
        self.task_callbacks: Dict[str, Callable] = {}
        
        # Performance metrics
        self.execution_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'avg_execution_time': 0.0
        }

    def register_engine(self, domain: AnalysisDomain, engine: AnalysisEngine):
        """Register an analysis engine for a specific domain"""
        self.engines[domain] = engine
        self.event_bus.publish({
            'type': 'engine_registered',
            'domain': domain.value,
            'engine_type': type(engine).__name__
        })

    def unregister_engine(self, domain: AnalysisDomain):
        """Unregister an analysis engine"""
        if domain in self.engines:
            del self.engines[domain]
            self.event_bus.publish({
                'type': 'engine_unregistered',
                'domain': domain.value
            })

    def get_registered_engines(self) -> List[AnalysisDomain]:
        """Get list of registered analysis domains"""
        return list(self.engines.keys())

    def start(self):
        """Start the orchestrator task processing"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
            self.worker_thread.start()
            self.event_bus.publish({
                'type': 'orchestrator_started',
                'timestamp': datetime.now()
            })

    def stop(self):
        """Stop the orchestrator and cleanup resources"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        # Cancel pending tasks
        with self._lock:
            for task_id, task_result in self.active_tasks.items():
                if task_result.status == TaskStatus.RUNNING:
                    task_result.status = TaskStatus.CANCELLED
                    task_result.end_time = datetime.now()
        
        self.executor.shutdown(wait=True)
        self.event_bus.publish({
            'type': 'orchestrator_stopped',
            'timestamp': datetime.now()
        })

    def submit_task(self, domain: AnalysisDomain, data: pd.DataFrame, 
                   config: Dict[str, Any] = None, priority: TaskPriority = TaskPriority.NORMAL,
                   callback: Callable = None) -> str:
        """
        Submit an analysis task for execution
        
        Args:
            domain: Analysis domain to execute
            data: Data to analyze
            config: Configuration parameters
            priority: Task priority
            callback: Optional callback function for task completion
            
        Returns:
            Task ID for tracking
        """
        if domain not in self.engines:
            raise ValueError(f"No engine registered for domain: {domain}")
        
        # Create task
        task_id = str(uuid.uuid4())
        task = AnalysisTask(
            task_id=task_id,
            domain=domain,
            data=data,
            config=config or {},
            priority=priority.value,
            created_at=datetime.now()
        )
        
        # Create task result tracker
        task_result = AnalysisTaskResult(
            task_id=task_id,
            domain=domain,
            status=TaskStatus.PENDING,
            result=None,
            error=None,
            start_time=datetime.now(),
            end_time=None,
            execution_time=None
        )
        
        with self._lock:
            self.active_tasks[task_id] = task_result
            if callback:
                self.task_callbacks[task_id] = callback
        
        # Add to priority queue (lower number = higher priority)
        self.task_queue.put((priority.value, task))
        
        self.event_bus.publish({
            'type': 'task_submitted',
            'task_id': task_id,
            'domain': domain.value,
            'priority': priority.value
        })
        
        return task_id

    def submit_batch_analysis(self, domains: List[AnalysisDomain], data: pd.DataFrame,
                            config: Dict[str, Any] = None, priority: TaskPriority = TaskPriority.NORMAL) -> List[str]:
        """Submit multiple analysis tasks as a batch"""
        task_ids = []
        
        for domain in domains:
            if domain in self.engines:
                task_id = self.submit_task(domain, data, config, priority)
                task_ids.append(task_id)
        
        self.event_bus.publish({
            'type': 'batch_analysis_submitted',
            'task_ids': task_ids,
            'domains': [d.value for d in domains]
        })
        
        return task_ids

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a specific task"""
        with self._lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].status
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id].status
        return None

    def get_task_result(self, task_id: str) -> Optional[AnalysisTaskResult]:
        """Get the result of a completed task"""
        with self._lock:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            elif task_id in self.active_tasks:
                task_result = self.active_tasks[task_id]
                if task_result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    return task_result
        return None

    def get_all_results(self) -> Dict[AnalysisDomain, AnalysisResult]:
        """Get results from all completed tasks, grouped by domain"""
        results = {}
        
        with self._lock:
            # Check completed tasks
            for task_result in self.completed_tasks.values():
                if task_result.status == TaskStatus.COMPLETED and task_result.result:
                    results[task_result.domain] = task_result.result
            
            # Check active tasks that are completed
            for task_result in self.active_tasks.values():
                if task_result.status == TaskStatus.COMPLETED and task_result.result:
                    results[task_result.domain] = task_result.result
        
        return results

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        with self._lock:
            if task_id in self.active_tasks:
                task_result = self.active_tasks[task_id]
                if task_result.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    task_result.status = TaskStatus.CANCELLED
                    task_result.end_time = datetime.now()
                    if task_result.start_time:
                        task_result.execution_time = (task_result.end_time - task_result.start_time).total_seconds()
                    
                    self.event_bus.publish({
                        'type': 'task_cancelled',
                        'task_id': task_id
                    })
                    return True
        return False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and metrics"""
        with self._lock:
            active_count = len([t for t in self.active_tasks.values() 
                              if t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]])
            completed_count = len(self.completed_tasks)
            
            # Calculate average execution time
            completed_tasks = [t for t in self.completed_tasks.values() 
                             if t.execution_time is not None]
            avg_execution_time = (sum(t.execution_time for t in completed_tasks) / len(completed_tasks) 
                                if completed_tasks else 0)
        
        return {
            'queue_size': self.task_queue.qsize(),
            'active_tasks': active_count,
            'completed_tasks': completed_count,
            'registered_engines': len(self.engines),
            'is_running': self.running,
            'metrics': {
                **self.execution_metrics,
                'avg_execution_time': avg_execution_time
            }
        }

    def clear_completed_tasks(self):
        """Clear completed tasks to free memory"""
        with self._lock:
            self.completed_tasks.clear()
        
        self.event_bus.publish({
            'type': 'completed_tasks_cleared',
            'timestamp': datetime.now()
        })

    def _process_tasks(self):
        """Main task processing loop (runs in separate thread)"""
        while self.running:
            try:
                # Get next task from queue (with timeout to allow checking running status)
                try:
                    priority, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check if task was cancelled
                with self._lock:
                    if task.task_id in self.active_tasks:
                        task_result = self.active_tasks[task.task_id]
                        if task_result.status == TaskStatus.CANCELLED:
                            continue
                
                # Execute task
                self._execute_task(task)
                
            except Exception as e:
                self.event_bus.publish({
                    'type': 'orchestrator_error',
                    'error': str(e),
                    'timestamp': datetime.now()
                })

    def _execute_task(self, task: AnalysisTask):
        """Execute a single analysis task"""
        task_id = task.task_id
        
        try:
            # Update task status
            with self._lock:
                if task_id in self.active_tasks:
                    task_result = self.active_tasks[task_id]
                    task_result.status = TaskStatus.RUNNING
                    task_result.start_time = datetime.now()
                else:
                    return  # Task was cancelled or removed
            
            self.event_bus.publish({
                'type': 'task_started',
                'task_id': task_id,
                'domain': task.domain.value
            })
            
            # Get engine for this domain
            engine = self.engines.get(task.domain)
            if not engine:
                raise ValueError(f"No engine registered for domain: {task.domain}")
            
            # Execute analysis
            start_time = time.time()
            result = engine.analyze(task.data, task.config)
            execution_time = time.time() - start_time
            
            # Update task result
            with self._lock:
                if task_id in self.active_tasks:
                    task_result = self.active_tasks[task_id]
                    task_result.status = TaskStatus.COMPLETED
                    task_result.result = result
                    task_result.end_time = datetime.now()
                    task_result.execution_time = execution_time
                    
                    # Move to completed tasks
                    self.completed_tasks[task_id] = task_result
                    del self.active_tasks[task_id]
                    
                    # Update metrics
                    self.execution_metrics['total_tasks'] += 1
                    self.execution_metrics['successful_tasks'] += 1
                    
                    # Update average execution time
                    total_successful = self.execution_metrics['successful_tasks']
                    current_avg = self.execution_metrics['avg_execution_time']
                    self.execution_metrics['avg_execution_time'] = (
                        (current_avg * (total_successful - 1) + execution_time) / total_successful
                    )
            
            self.event_bus.publish({
                'type': 'task_completed',
                'task_id': task_id,
                'domain': task.domain.value,
                'execution_time': execution_time,
                'alerts_generated': len(result.alerts) if result else 0
            })
            
            # Execute callback if provided
            callback = self.task_callbacks.get(task_id)
            if callback:
                try:
                    callback(task_id, result)
                except Exception as e:
                    self.event_bus.publish({
                        'type': 'callback_error',
                        'task_id': task_id,
                        'error': str(e)
                    })
                finally:
                    del self.task_callbacks[task_id]
            
        except Exception as e:
            # Handle task execution error
            with self._lock:
                if task_id in self.active_tasks:
                    task_result = self.active_tasks[task_id]
                    task_result.status = TaskStatus.FAILED
                    task_result.error = str(e)
                    task_result.end_time = datetime.now()
                    if task_result.start_time:
                        task_result.execution_time = (task_result.end_time - task_result.start_time).total_seconds()
                    
                    # Move to completed tasks
                    self.completed_tasks[task_id] = task_result
                    del self.active_tasks[task_id]
                    
                    # Update metrics
                    self.execution_metrics['total_tasks'] += 1
                    self.execution_metrics['failed_tasks'] += 1
            
            self.event_bus.publish({
                'type': 'task_failed',
                'task_id': task_id,
                'domain': task.domain.value,
                'error': str(e)
            })

    # Legacy compatibility methods
    def analyze_all_domains(self, data: pd.DataFrame, selected_domains: List[AnalysisDomain] = None,
                          config: Dict[str, Any] = None) -> Dict[AnalysisDomain, AnalysisResult]:
        """
        Legacy method for backward compatibility
        Performs synchronous analysis of all domains
        """
        domains_to_analyze = selected_domains or list(self.engines.keys())
        
        # Submit all tasks
        task_ids = self.submit_batch_analysis(domains_to_analyze, data, config, TaskPriority.HIGH)
        
        # Wait for all tasks to complete
        results = {}
        timeout = 300  # 5 minutes timeout
        start_time = time.time()
        
        while len(results) < len(task_ids) and (time.time() - start_time) < timeout:
            for task_id in task_ids:
                if task_id not in results:
                    task_result = self.get_task_result(task_id)
                    if task_result and task_result.status == TaskStatus.COMPLETED:
                        results[task_result.domain] = task_result.result
                    elif task_result and task_result.status == TaskStatus.FAILED:
                        self.event_bus.publish({
                            'type': 'domain_analysis_failed',
                            'domain': task_result.domain.value,
                            'error': task_result.error
                        })
            
            if len(results) < len(task_ids):
                time.sleep(0.1)  # Brief pause before checking again
        
        return results

    def get_domain_analysis(self, domain: AnalysisDomain) -> Optional[AnalysisResult]:
        """Get the most recent analysis result for a specific domain"""
        with self._lock:
            # Check completed tasks first (most recent)
            for task_result in reversed(list(self.completed_tasks.values())):
                if task_result.domain == domain and task_result.status == TaskStatus.COMPLETED:
                    return task_result.result
            
            # Check active tasks
            for task_result in self.active_tasks.values():
                if task_result.domain == domain and task_result.status == TaskStatus.COMPLETED:
                    return task_result.result
        
        return None

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()