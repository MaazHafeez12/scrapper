"""
Background Job Queue System
Async task processing for long-running operations
"""

import threading
import queue
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import secrets

class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class Job:
    """Background job representation"""
    
    def __init__(self, job_id: str, job_type: str, payload: Dict, 
                 priority: JobPriority = JobPriority.NORMAL):
        self.job_id = job_id
        self.job_type = job_type
        self.payload = payload
        self.priority = priority
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.retry_count = 0
        self.max_retries = 3
        self.progress = 0
        
    def to_dict(self) -> Dict:
        """Convert job to dictionary"""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'payload': self.payload,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'progress': self.progress
        }

class JobWorker(threading.Thread):
    """Worker thread for processing jobs"""
    
    def __init__(self, worker_id: int, job_queue: queue.PriorityQueue, 
                 job_registry: Dict, handlers: Dict):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.job_queue = job_queue
        self.job_registry = job_registry
        self.handlers = handlers
        self.running = True
        self.current_job = None
        
    def run(self):
        """Worker main loop"""
        while self.running:
            try:
                # Get job from queue (with timeout to check running status)
                priority, job = self.job_queue.get(timeout=1)
                self.current_job = job
                
                # Process job
                self._process_job(job)
                
                self.job_queue.task_done()
                self.current_job = None
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
    
    def _process_job(self, job: Job):
        """Process a single job"""
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            # Get handler for job type
            handler = self.handlers.get(job.job_type)
            if not handler:
                raise Exception(f"No handler found for job type: {job.job_type}")
            
            # Execute handler
            result = handler(job.payload, job)
            
            # Update job with result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            job.progress = 100
            
        except Exception as e:
            # Handle job failure
            job.error = str(e)
            job.retry_count += 1
            
            if job.retry_count < job.max_retries:
                job.status = JobStatus.RETRYING
                # Re-queue job with delay
                time.sleep(2 ** job.retry_count)  # Exponential backoff
                self.job_queue.put((job.priority.value, job))
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
    
    def stop(self):
        """Stop worker"""
        self.running = False

class BackgroundJobQueue:
    """Background job queue manager"""
    
    def __init__(self, num_workers: int = 3):
        self.job_queue = queue.PriorityQueue()
        self.job_registry = {}  # {job_id: Job}
        self.handlers = {}  # {job_type: handler_function}
        self.workers = []
        self.num_workers = num_workers
        self._start_workers()
        
    def _start_workers(self):
        """Start worker threads"""
        for i in range(self.num_workers):
            worker = JobWorker(i, self.job_queue, self.job_registry, self.handlers)
            worker.start()
            self.workers.append(worker)
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register job handler"""
        self.handlers[job_type] = handler
    
    def enqueue(self, job_type: str, payload: Dict, 
                priority: JobPriority = JobPriority.NORMAL) -> str:
        """Add job to queue"""
        job_id = secrets.token_urlsafe(16)
        
        job = Job(job_id, job_type, payload, priority)
        self.job_registry[job_id] = job
        
        # Add to priority queue (lower number = higher priority)
        self.job_queue.put((5 - priority.value, job))
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        job = self.job_registry.get(job_id)
        return job.to_dict() if job else None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel pending job"""
        job = self.job_registry.get(job_id)
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            return True
        return False
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        stats = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'total': len(self.job_registry)
        }
        
        for job in self.job_registry.values():
            if job.status == JobStatus.PENDING:
                stats['pending'] += 1
            elif job.status == JobStatus.RUNNING:
                stats['running'] += 1
            elif job.status == JobStatus.COMPLETED:
                stats['completed'] += 1
            elif job.status == JobStatus.FAILED:
                stats['failed'] += 1
        
        stats['queue_size'] = self.job_queue.qsize()
        stats['workers'] = self.num_workers
        stats['active_workers'] = sum(1 for w in self.workers if w.current_job)
        
        return stats
    
    def get_jobs(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get list of jobs"""
        jobs = list(self.job_registry.values())
        
        # Filter by status
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limit results
        jobs = jobs[:limit]
        
        return [job.to_dict() for job in jobs]
    
    def retry_job(self, job_id: str) -> bool:
        """Retry failed job"""
        job = self.job_registry.get(job_id)
        if job and job.status == JobStatus.FAILED:
            job.status = JobStatus.PENDING
            job.retry_count = 0
            job.error = None
            self.job_queue.put((5 - job.priority.value, job))
            return True
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove old completed/failed jobs"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = [
            job_id for job_id, job in self.job_registry.items()
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
            and job.completed_at and job.completed_at < cutoff
        ]
        
        for job_id in jobs_to_remove:
            del self.job_registry[job_id]
        
        return len(jobs_to_remove)
    
    def shutdown(self):
        """Shutdown all workers"""
        for worker in self.workers:
            worker.stop()
        
        for worker in self.workers:
            worker.join(timeout=5)

class JobService:
    """High-level job service with common job types"""
    
    def __init__(self, job_queue: BackgroundJobQueue):
        self.queue = job_queue
        self._register_handlers()
    
    def _register_handlers(self):
        """Register built-in job handlers"""
        self.queue.register_handler('send_email', self._handle_send_email)
        self.queue.register_handler('export_data', self._handle_export_data)
        self.queue.register_handler('webhook_delivery', self._handle_webhook_delivery)
        self.queue.register_handler('bulk_update', self._handle_bulk_update)
        self.queue.register_handler('generate_report', self._handle_generate_report)
        self.queue.register_handler('data_sync', self._handle_data_sync)
        self.queue.register_handler('cleanup', self._handle_cleanup)
    
    def _handle_send_email(self, payload: Dict, job: Job) -> Dict:
        """Handle email sending"""
        # Simulate email sending
        time.sleep(2)  # Simulate delay
        
        return {
            'sent': True,
            'recipient': payload.get('to'),
            'subject': payload.get('subject')
        }
    
    def _handle_export_data(self, payload: Dict, job: Job) -> Dict:
        """Handle data export"""
        # Simulate export
        total_records = payload.get('record_count', 1000)
        
        for i in range(10):
            time.sleep(0.5)
            job.progress = (i + 1) * 10
        
        return {
            'exported': True,
            'records': total_records,
            'format': payload.get('format', 'csv')
        }
    
    def _handle_webhook_delivery(self, payload: Dict, job: Job) -> Dict:
        """Handle webhook delivery"""
        # Simulate webhook call
        time.sleep(1)
        
        return {
            'delivered': True,
            'url': payload.get('url'),
            'status_code': 200
        }
    
    def _handle_bulk_update(self, payload: Dict, job: Job) -> Dict:
        """Handle bulk update"""
        # Simulate bulk operation
        total_items = payload.get('item_count', 100)
        
        for i in range(10):
            time.sleep(0.3)
            job.progress = (i + 1) * 10
        
        return {
            'updated': total_items,
            'entity': payload.get('entity')
        }
    
    def _handle_generate_report(self, payload: Dict, job: Job) -> Dict:
        """Handle report generation"""
        # Simulate report generation
        time.sleep(3)
        
        return {
            'generated': True,
            'report_type': payload.get('report_type'),
            'format': payload.get('format', 'pdf')
        }
    
    def _handle_data_sync(self, payload: Dict, job: Job) -> Dict:
        """Handle data synchronization"""
        # Simulate data sync
        time.sleep(2)
        
        return {
            'synced': True,
            'source': payload.get('source'),
            'records': payload.get('record_count', 0)
        }
    
    def _handle_cleanup(self, payload: Dict, job: Job) -> Dict:
        """Handle cleanup tasks"""
        # Simulate cleanup
        time.sleep(1)
        
        return {
            'cleaned': True,
            'type': payload.get('cleanup_type')
        }
    
    # Convenience methods for common job types
    
    def schedule_email(self, to: str, subject: str, body: str, 
                      priority: JobPriority = JobPriority.NORMAL) -> str:
        """Schedule email sending"""
        payload = {'to': to, 'subject': subject, 'body': body}
        return self.queue.enqueue('send_email', payload, priority)
    
    def schedule_export(self, entity: str, filters: Dict, format: str = 'csv',
                       priority: JobPriority = JobPriority.NORMAL) -> str:
        """Schedule data export"""
        payload = {
            'entity': entity,
            'filters': filters,
            'format': format,
            'record_count': 1000
        }
        return self.queue.enqueue('export_data', payload, priority)
    
    def schedule_webhook(self, url: str, payload: Dict, 
                        priority: JobPriority = JobPriority.HIGH) -> str:
        """Schedule webhook delivery"""
        webhook_payload = {'url': url, 'payload': payload}
        return self.queue.enqueue('webhook_delivery', webhook_payload, priority)
    
    def schedule_bulk_update(self, entity: str, updates: Dict, items: List,
                           priority: JobPriority = JobPriority.NORMAL) -> str:
        """Schedule bulk update"""
        payload = {
            'entity': entity,
            'updates': updates,
            'items': items,
            'item_count': len(items)
        }
        return self.queue.enqueue('bulk_update', payload, priority)
    
    def schedule_report(self, report_type: str, filters: Dict, format: str = 'pdf',
                       priority: JobPriority = JobPriority.NORMAL) -> str:
        """Schedule report generation"""
        payload = {
            'report_type': report_type,
            'filters': filters,
            'format': format
        }
        return self.queue.enqueue('generate_report', payload, priority)
    
    def schedule_sync(self, source: str, target: str, options: Dict = None,
                     priority: JobPriority = JobPriority.NORMAL) -> str:
        """Schedule data synchronization"""
        payload = {
            'source': source,
            'target': target,
            'options': options or {},
            'record_count': 0
        }
        return self.queue.enqueue('data_sync', payload, priority)
