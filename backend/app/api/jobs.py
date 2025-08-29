"""
API routes for job management and monitoring
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from models.workflow import JobStatus
from services.job_manager import job_manager
from services.database_service import db_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


# Response models
class JobStatusResponse(BaseModel):
    job_id: str
    workflow_id: str
    status: JobStatus
    progress: Dict[str, Any]
    results: List[Dict[str, Any]]
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    final_output_path: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobStatusResponse]
    total: int


class JobStatsResponse(BaseModel):
    running_jobs: int
    queue_size: int
    max_concurrent_jobs: int
    active_workers: int
    shutdown: bool


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip")
):
    """List jobs with optional filtering and pagination"""
    try:
        # Get jobs from job manager
        jobs = await job_manager.list_jobs(workflow_id, status)
        
        # Apply pagination
        total = len(jobs)
        paginated_jobs = jobs[offset:offset + limit]
        
        # Convert to response format
        job_responses = []
        for job_data in paginated_jobs:
            job_response = JobStatusResponse(
                job_id=job_data['job_id'],
                workflow_id=job_data['workflow_id'],
                status=JobStatus(job_data['status']),
                progress=job_data.get('progress', {}),
                results=job_data.get('results', []),
                created_at=job_data['created_at'],
                started_at=job_data.get('started_at'),
                completed_at=job_data.get('completed_at'),
                error_message=job_data.get('error_message'),
                final_output_path=job_data.get('final_output_path')
            )
            job_responses.append(job_response)
        
        return JobListResponse(jobs=job_responses, total=total)
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status and details of a specific job"""
    try:
        job_data = await job_manager.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job_data['job_id'],
            workflow_id=job_data['workflow_id'],
            status=JobStatus(job_data['status']),
            progress=job_data.get('progress', {}),
            results=job_data.get('results', []),
            created_at=job_data['created_at'],
            started_at=job_data.get('started_at'),
            completed_at=job_data.get('completed_at'),
            error_message=job_data.get('error_message'),
            final_output_path=job_data.get('final_output_path')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running or pending job"""
    try:
        success = await job_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Job not found or cannot be cancelled (already completed/failed)"
            )
        
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/progress")
async def get_job_progress(job_id: str):
    """Get real-time progress information for a job"""
    try:
        job_data = await job_manager.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        progress = job_data.get('progress', {})
        
        return {
            "job_id": job_id,
            "status": job_data['status'],
            "progress": progress,
            "current_step": progress.get('current_step', 0),
            "total_steps": progress.get('total_steps', 0),
            "current_block_id": progress.get('current_block_id'),
            "current_block_name": progress.get('current_block_name'),
            "processed_rows": progress.get('processed_rows', 0),
            "total_rows": progress.get('total_rows', 0),
            "message": progress.get('message', ''),
            "percentage": progress.get('percentage', 0.0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job progress {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/results")
async def get_job_results(job_id: str):
    """Get the results of a completed job"""
    try:
        job_data = await job_manager.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        results = job_data.get('results', [])
        
        return {
            "job_id": job_id,
            "status": job_data['status'],
            "results": results,
            "final_output_path": job_data.get('final_output_path'),
            "total_blocks": len(results),
            "successful_blocks": len([r for r in results if r.get('success', False)]),
            "failed_blocks": len([r for r in results if not r.get('success', True)])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job results {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", response_model=JobStatsResponse)
async def get_job_stats():
    """Get job manager statistics and overview"""
    try:
        stats = job_manager.get_stats()
        
        return JobStatsResponse(
            running_jobs=stats['running_jobs'],
            queue_size=stats['queue_size'],
            max_concurrent_jobs=stats['max_concurrent_jobs'],
            active_workers=stats['active_workers'],
            shutdown=stats['shutdown']
        )
        
    except Exception as e:
        logger.error(f"Failed to get job stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_jobs(days: int = Query(7, ge=1, le=365, description="Number of days to keep jobs")):
    """Clean up old completed/failed jobs"""
    try:
        await job_manager.cleanup_old_jobs(days)
        
        return {"message": f"Cleanup initiated for jobs older than {days} days"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
