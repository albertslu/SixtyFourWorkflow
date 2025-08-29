"""
Async job manager with progress tracking
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import uuid

from models.workflow import Job, JobStatus, Workflow
from services.database_service import db_service
from services.workflow_executor import workflow_executor


class JobManager:
    """Manages workflow job execution and tracking"""
    
    def __init__(self):
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrent_jobs = 5
        self._worker_tasks: List[asyncio.Task] = []
        self._shutdown = False
    
    async def start(self):
        """Start the job manager workers"""
        logger.info(f"Starting job manager with {self.max_concurrent_jobs} workers")
        
        # Start worker tasks
        for i in range(self.max_concurrent_jobs):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        logger.info("Job manager started successfully")
    
    async def stop(self):
        """Stop the job manager and cancel running jobs"""
        logger.info("Stopping job manager...")
        self._shutdown = True
        
        # Cancel all running jobs
        for job_id, task in self.running_jobs.items():
            logger.info(f"Cancelling job {job_id}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.running_jobs.clear()
        self._worker_tasks.clear()
        logger.info("Job manager stopped")
    
    async def submit_job(self, workflow: Workflow, input_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a workflow for execution
        
        Args:
            workflow: The workflow to execute
            input_data: Optional input data
            
        Returns:
            Job ID for tracking
        """
        # Create job
        job = Job(
            workflow_id=workflow.workflow_id,
            status=JobStatus.PENDING
        )
        
        # Save to database
        await db_service.save_job(job)
        
        # Add to queue
        await self.job_queue.put((job, workflow, input_data))
        
        logger.info(f"Submitted job {job.job_id} for workflow {workflow.workflow_id}")
        return job.job_id
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes jobs from the queue"""
        logger.info(f"Worker {worker_name} started")
        
        while not self._shutdown:
            try:
                # Wait for a job with timeout
                try:
                    job, workflow, input_data = await asyncio.wait_for(
                        self.job_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                logger.info(f"Worker {worker_name} picked up job {job.job_id}")
                
                # Execute the job
                task = asyncio.create_task(
                    self._execute_job(job, workflow, input_data)
                )
                self.running_jobs[job.job_id] = task
                
                try:
                    await task
                except Exception as e:
                    logger.error(f"Job {job.job_id} failed: {str(e)}")
                    await db_service.update_job_status(job.job_id, JobStatus.FAILED, str(e))
                finally:
                    # Clean up
                    if job.job_id in self.running_jobs:
                        del self.running_jobs[job.job_id]
                
                # Mark task as done
                self.job_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _execute_job(self, job: Job, workflow: Workflow, input_data: Optional[Dict[str, Any]]):
        """Execute a single job"""
        try:
            logger.info(f"Starting execution of job {job.job_id}")
            
            # Update job status
            await db_service.update_job_status(job.job_id, JobStatus.RUNNING)
            
            # Execute workflow using the workflow executor
            await workflow_executor._execute_workflow_async(workflow, job, input_data)
            
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} execution failed: {str(e)}")
            await db_service.update_job_status(job.job_id, JobStatus.FAILED, str(e))
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a job"""
        return await db_service.get_job(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        # Check if job is running
        if job_id in self.running_jobs:
            task = self.running_jobs[job_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Update job status
            await db_service.update_job_status(job_id, JobStatus.CANCELLED)
            
            # Clean up
            if job_id in self.running_jobs:
                del self.running_jobs[job_id]
            
            logger.info(f"Cancelled job {job_id}")
            return True
        
        # Check if job is pending in queue (this is more complex to implement)
        # For now, just update status if job exists
        job_data = await db_service.get_job(job_id)
        if job_data and job_data['status'] == JobStatus.PENDING:
            await db_service.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"Cancelled pending job {job_id}")
            return True
        
        return False
    
    async def list_jobs(self, workflow_id: Optional[str] = None, status: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering
        
        Args:
            workflow_id: Optional workflow ID filter
            status: Optional status filter
            
        Returns:
            List of job data
        """
        jobs = await db_service.list_jobs(workflow_id)
        
        if status:
            jobs = [job for job in jobs if job['status'] == status]
        
        return jobs
    
    async def cleanup_old_jobs(self, days: int = 7):
        """
        Clean up old completed/failed jobs
        
        Args:
            days: Number of days to keep jobs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # This would require additional database methods to implement properly
        # For now, just log the intent
        logger.info(f"Would clean up jobs older than {cutoff_date}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get job manager statistics"""
        return {
            "running_jobs": len(self.running_jobs),
            "queue_size": self.job_queue.qsize(),
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "active_workers": len([t for t in self._worker_tasks if not t.done()]),
            "shutdown": self._shutdown
        }


# Global job manager instance
job_manager = JobManager()
