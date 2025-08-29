"""
Database service for Supabase integration
"""
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from loguru import logger
import json
from datetime import datetime

from core.config import settings
from models.workflow import Job, Workflow, JobStatus, JobProgress, JobResult


def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def workflow_to_dict(workflow: Workflow) -> Dict[str, Any]:
    """Convert workflow to dictionary with proper datetime handling"""
    data = {
        'workflow_id': workflow.workflow_id,
        'name': workflow.name,
        'description': workflow.description,
        'blocks': [block.dict() for block in workflow.blocks],
        'connections': [conn.dict() for conn in workflow.connections],
        'created_at': workflow.created_at.isoformat() if workflow.created_at else datetime.utcnow().isoformat(),
        'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else datetime.utcnow().isoformat()
    }
    return data


def job_to_dict(job: Job) -> Dict[str, Any]:
    """Convert job to dictionary with proper datetime handling"""
    data = {
        'job_id': job.job_id,
        'workflow_id': job.workflow_id,
        'status': job.status.value if hasattr(job.status, 'value') else job.status,
        'progress': job.progress.dict() if hasattr(job.progress, 'dict') else job.progress,
        'results': [result.dict() if hasattr(result, 'dict') else result for result in job.results],
        'created_at': job.created_at.isoformat() if job.created_at else datetime.utcnow().isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message,
        'final_output_path': job.final_output_path
    }
    return data


class DatabaseService:
    """Service for database operations using Supabase"""
    
    def __init__(self):
        if not settings.supabase_url or not settings.supabase_key:
            logger.warning("Supabase credentials not found, using in-memory storage")
            self.client = None
            self._in_memory_jobs = {}
            self._in_memory_workflows = {}
        else:
            self.client: Client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Connected to Supabase database")
    
    async def create_tables(self):
        """Create necessary tables if they don't exist"""
        if not self.client:
            logger.info("Using in-memory storage, skipping table creation")
            return
            
        # Note: In a real implementation, you'd create these tables via Supabase dashboard
        # or migration scripts. This is just for reference.
        logger.info("Tables should be created via Supabase dashboard")
    
    # Workflow operations
    async def save_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Save a workflow to the database"""
        if not self.client:
            workflow_data = workflow_to_dict(workflow)
            self._in_memory_workflows[workflow.workflow_id] = workflow_data
            return workflow_data
        
        try:
            data = workflow_to_dict(workflow)
            # Convert blocks and connections to JSON strings for Supabase
            data['blocks'] = json.dumps(data['blocks'])
            data['connections'] = json.dumps(data['connections'])
            
            result = self.client.table('workflows').insert(data).execute()
            logger.info(f"Saved workflow {workflow.workflow_id}")
            
            if result.data:
                # Convert back from JSON strings for return
                returned_data = result.data[0]
                returned_data['blocks'] = json.loads(returned_data['blocks'])
                returned_data['connections'] = json.loads(returned_data['connections'])
                return returned_data
            else:
                # Return the original data if no result
                data['blocks'] = json.loads(data['blocks'])
                data['connections'] = json.loads(data['connections'])
                return data
        except Exception as e:
            logger.error(f"Failed to save workflow: {str(e)}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID"""
        if not self.client:
            return self._in_memory_workflows.get(workflow_id)
        
        try:
            result = self.client.table('workflows').select('*').eq('workflow_id', workflow_id).execute()
            if result.data:
                workflow_data = result.data[0]
                workflow_data['blocks'] = json.loads(workflow_data['blocks'])
                workflow_data['connections'] = json.loads(workflow_data['connections'])
                return workflow_data
            return None
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {str(e)}")
            return None
    
    async def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing workflow"""
        if not self.client:
            if workflow_id in self._in_memory_workflows:
                # Add updated_at timestamp
                workflow_data['updated_at'] = datetime.utcnow().isoformat()
                self._in_memory_workflows[workflow_id].update(workflow_data)
                return self._in_memory_workflows[workflow_id]
            return None
        
        try:
            # Prepare data for update
            update_data = workflow_data.copy()
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            if 'blocks' in update_data:
                update_data['blocks'] = json.dumps(update_data['blocks'])
            if 'connections' in update_data:
                update_data['connections'] = json.dumps(update_data['connections'])
            
            result = self.client.table('workflows').update(update_data).eq('workflow_id', workflow_id).execute()
            if result.data:
                returned_data = result.data[0]
                returned_data['blocks'] = json.loads(returned_data['blocks'])
                returned_data['connections'] = json.loads(returned_data['connections'])
                logger.info(f"Updated workflow {workflow_id}")
                return returned_data
            return None
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {str(e)}")
            raise

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        if not self.client:
            return list(self._in_memory_workflows.values())
        
        try:
            result = self.client.table('workflows').select('*').execute()
            workflows = []
            for workflow_data in result.data:
                workflow_data['blocks'] = json.loads(workflow_data['blocks'])
                workflow_data['connections'] = json.loads(workflow_data['connections'])
                workflows.append(workflow_data)
            return workflows
        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            return []
    
    # Job operations
    async def save_job(self, job: Job) -> Dict[str, Any]:
        """Save a job to the database"""
        if not self.client:
            job_data = job_to_dict(job)
            self._in_memory_jobs[job.job_id] = job_data
            return job_data
        
        try:
            data = job_to_dict(job)
            # Convert progress and results to JSON strings for Supabase
            data['progress'] = json.dumps(data['progress'])
            data['results'] = json.dumps(data['results'])
            
            # Check if job exists
            existing = self.client.table('jobs').select('job_id').eq('job_id', job.job_id).execute()
            
            if existing.data:
                # Update existing job
                result = self.client.table('jobs').update(data).eq('job_id', job.job_id).execute()
            else:
                # Insert new job
                result = self.client.table('jobs').insert(data).execute()
            
            logger.info(f"Saved job {job.job_id}")
            
            if result.data:
                # Convert back from JSON strings for return
                returned_data = result.data[0]
                returned_data['progress'] = json.loads(returned_data['progress'])
                returned_data['results'] = json.loads(returned_data['results'])
                return returned_data
            else:
                # Return the original data if no result
                data['progress'] = json.loads(data['progress'])
                data['results'] = json.loads(data['results'])
                return data
        except Exception as e:
            logger.error(f"Failed to save job: {str(e)}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        if not self.client:
            return self._in_memory_jobs.get(job_id)
        
        try:
            result = self.client.table('jobs').select('*').eq('job_id', job_id).execute()
            if result.data:
                job_data = result.data[0]
                job_data['progress'] = json.loads(job_data['progress'])
                job_data['results'] = json.loads(job_data['results'])
                return job_data
            return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    async def update_job_status(self, job_id: str, status: JobStatus, error_message: Optional[str] = None):
        """Update job status"""
        if not self.client:
            if job_id in self._in_memory_jobs:
                self._in_memory_jobs[job_id]['status'] = status
                if error_message:
                    self._in_memory_jobs[job_id]['error_message'] = error_message
                if status == JobStatus.RUNNING:
                    self._in_memory_jobs[job_id]['started_at'] = datetime.utcnow().isoformat()
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    self._in_memory_jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
            return
        
        try:
            update_data = {'status': status.value if hasattr(status, 'value') else status}
            if error_message:
                update_data['error_message'] = error_message
            if status == JobStatus.RUNNING:
                update_data['started_at'] = datetime.utcnow().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_data['completed_at'] = datetime.utcnow().isoformat()
            
            self.client.table('jobs').update(update_data).eq('job_id', job_id).execute()
            logger.info(f"Updated job {job_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
    
    async def update_job_progress(self, job_id: str, progress: JobProgress):
        """Update job progress"""
        if not self.client:
            if job_id in self._in_memory_jobs:
                self._in_memory_jobs[job_id]['progress'] = progress.dict()
            return
        
        try:
            progress_data = progress.dict() if hasattr(progress, 'dict') else progress
            update_data = {'progress': json.dumps(progress_data)}
            self.client.table('jobs').update(update_data).eq('job_id', job_id).execute()
            logger.debug(f"Updated job {job_id} progress: {progress_data.get('percentage', 0)}%")
        except Exception as e:
            logger.error(f"Failed to update job progress: {str(e)}")
    
    async def add_job_result(self, job_id: str, result: JobResult):
        """Add a result to a job"""
        if not self.client:
            if job_id in self._in_memory_jobs:
                if 'results' not in self._in_memory_jobs[job_id]:
                    self._in_memory_jobs[job_id]['results'] = []
                self._in_memory_jobs[job_id]['results'].append(result.dict())
            return
        
        try:
            # Get current results
            job_data = await self.get_job(job_id)
            if job_data:
                results = job_data.get('results', [])
                result_data = result.dict() if hasattr(result, 'dict') else result
                results.append(result_data)
                
                update_data = {'results': json.dumps(results)}
                self.client.table('jobs').update(update_data).eq('job_id', job_id).execute()
                logger.info(f"Added result to job {job_id}")
        except Exception as e:
            logger.error(f"Failed to add job result: {str(e)}")
    
    async def list_jobs(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jobs, optionally filtered by workflow_id"""
        if not self.client:
            jobs = list(self._in_memory_jobs.values())
            if workflow_id:
                jobs = [job for job in jobs if job.get('workflow_id') == workflow_id]
            return jobs
        
        try:
            query = self.client.table('jobs').select('*')
            if workflow_id:
                query = query.eq('workflow_id', workflow_id)
            
            result = query.execute()
            jobs = []
            for job_data in result.data:
                job_data['progress'] = json.loads(job_data['progress'])
                job_data['results'] = json.loads(job_data['results'])
                jobs.append(job_data)
            return jobs
        except Exception as e:
            logger.error(f"Failed to list jobs: {str(e)}")
            return []


# Global database service instance
db_service = DatabaseService()
