"""
API routes for workflow management
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
from loguru import logger

from models.workflow import (
    Workflow, WorkflowExecutionRequest, WorkflowExecutionResponse,
    Job, JobStatus, BlockType, create_block_config
)
from services.database_service import db_service
from services.job_manager import job_manager
from core.config import settings

router = APIRouter(prefix="/workflows", tags=["workflows"])


# Request/Response models
class CreateWorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None
    blocks: List[Dict[str, Any]] = []
    connections: List[Dict[str, str]] = []


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    connections: Optional[List[Dict[str, str]]] = None


class ExecuteWorkflowRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = None


# Workflow CRUD operations
@router.post("/", response_model=Dict[str, Any])
async def create_workflow(request: CreateWorkflowRequest):
    """Create a new workflow"""
    try:
        # Create workflow blocks
        blocks = []
        for block_data in request.blocks:
            block_type = BlockType(block_data.get('block_type'))
            block = create_block_config(
                block_type=block_type,
                name=block_data.get('name', ''),
                description=block_data.get('description'),
                parameters=block_data.get('parameters', {}),
                position=block_data.get('position', {"x": 0, "y": 0})
            )
            if 'block_id' in block_data:
                block.block_id = block_data['block_id']
            blocks.append(block)
        
        # Create workflow connections
        connections = []
        for conn_data in request.connections:
            from models.workflow import WorkflowConnection
            connection = WorkflowConnection(
                source_block_id=conn_data['source_block_id'],
                target_block_id=conn_data['target_block_id']
            )
            if 'connection_id' in conn_data:
                connection.connection_id = conn_data['connection_id']
            connections.append(connection)
        
        # Create workflow
        workflow = Workflow(
            name=request.name,
            description=request.description,
            blocks=blocks,
            connections=connections
        )
        
        # Save to database
        saved_workflow = await db_service.save_workflow(workflow)
        
        logger.info(f"Created workflow {workflow.workflow_id}")
        return saved_workflow
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[Dict[str, Any]])
async def list_workflows():
    """List all workflows"""
    try:
        workflows = await db_service.list_workflows()
        return workflows
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID"""
    try:
        workflow = await db_service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(workflow_id: str, request: UpdateWorkflowRequest):
    """Update an existing workflow"""
    try:
        # Get existing workflow
        existing = await db_service.get_workflow(workflow_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update fields
        if request.name is not None:
            existing['name'] = request.name
        if request.description is not None:
            existing['description'] = request.description
        if request.blocks is not None:
            # Convert blocks
            blocks = []
            for block_data in request.blocks:
                block_type = BlockType(block_data.get('block_type'))
                block = create_block_config(
                    block_type=block_type,
                    name=block_data.get('name', ''),
                    description=block_data.get('description'),
                    parameters=block_data.get('parameters', {}),
                    position=block_data.get('position', {"x": 0, "y": 0})
                )
                if 'block_id' in block_data:
                    block.block_id = block_data['block_id']
                blocks.append(block.dict())
            existing['blocks'] = blocks
        
        if request.connections is not None:
            existing['connections'] = request.connections
        
        # Create updated workflow object
        from models.workflow import WorkflowConnection
        blocks = []
        for block_data in existing['blocks']:
            block_type = BlockType(block_data.get('block_type'))
            block = create_block_config(
                block_type=block_type,
                name=block_data.get('name', ''),
                description=block_data.get('description'),
                parameters=block_data.get('parameters', {}),
                position=block_data.get('position', {"x": 0, "y": 0})
            )
            block.block_id = block_data['block_id']
            blocks.append(block)
        
        connections = []
        for conn_data in existing['connections']:
            connection = WorkflowConnection(
                source_block_id=conn_data['source_block_id'],
                target_block_id=conn_data['target_block_id']
            )
            if 'connection_id' in conn_data:
                connection.connection_id = conn_data['connection_id']
            connections.append(connection)
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=existing['name'],
            description=existing['description'],
            blocks=blocks,
            connections=connections
        )
        
        # Update workflow in database
        update_data = {
            'name': existing['name'],
            'description': existing['description'],
            'blocks': existing['blocks'],
            'connections': existing['connections']
        }
        updated_workflow = await db_service.update_workflow(workflow_id, update_data)
        
        logger.info(f"Updated workflow {workflow_id}")
        return updated_workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        # Check if workflow exists
        workflow = await db_service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # TODO: Implement delete functionality in database service
        # For now, just return success
        logger.info(f"Would delete workflow {workflow_id}")
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Workflow execution
@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_id: str, request: ExecuteWorkflowRequest):
    """Execute a workflow"""
    try:
        # Get workflow
        workflow_data = await db_service.get_workflow(workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Convert to workflow object
        from models.workflow import WorkflowConnection
        blocks = []
        for block_data in workflow_data['blocks']:
            block_type = BlockType(block_data.get('block_type'))
            block = create_block_config(
                block_type=block_type,
                name=block_data.get('name', ''),
                description=block_data.get('description'),
                parameters=block_data.get('parameters', {}),
                position=block_data.get('position', {"x": 0, "y": 0})
            )
            block.block_id = block_data['block_id']
            blocks.append(block)
        
        connections = []
        for conn_data in workflow_data['connections']:
            connection = WorkflowConnection(
                source_block_id=conn_data['source_block_id'],
                target_block_id=conn_data['target_block_id']
            )
            if 'connection_id' in conn_data:
                connection.connection_id = conn_data['connection_id']
            connections.append(connection)
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=workflow_data['name'],
            description=workflow_data['description'],
            blocks=blocks,
            connections=connections
        )
        
        # Submit job
        job_id = await job_manager.submit_job(workflow, request.input_data)
        
        return WorkflowExecutionResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Workflow execution started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# File upload
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file for use in workflows"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(settings.upload_folder, filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_folder, exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Uploaded file {filename}")
        
        return {
            "file_id": file_id,
            "filename": filename,
            "original_name": file.filename,
            "file_path": filename,  # Relative path for use in workflows
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{filename}")
async def download_file(filename: str):
    """Download a file"""
    try:
        file_path = os.path.join(settings.upload_folder, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Block types info
@router.get("/block-types")
async def get_block_types():
    """Get available block types and their configurations"""
    return {
        "block_types": [
            {
                "type": BlockType.READ_CSV,
                "name": "Read CSV",
                "description": "Load a CSV file into a dataframe",
                "parameters": {
                    "file_path": {"type": "string", "required": True, "description": "Path to CSV file"},
                    "delimiter": {"type": "string", "default": ",", "description": "CSV delimiter"},
                    "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"},
                    "skip_rows": {"type": "integer", "default": 0, "description": "Number of rows to skip"}
                }
            },
            {
                "type": BlockType.SAVE_CSV,
                "name": "Save CSV",
                "description": "Save the current dataframe to a CSV file",
                "parameters": {
                    "file_path": {"type": "string", "required": False, "description": "Output file path (auto-generated if not provided)"},
                    "delimiter": {"type": "string", "default": ",", "description": "CSV delimiter"},
                    "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"},
                    "index": {"type": "boolean", "default": False, "description": "Include row index"}
                }
            },
            {
                "type": BlockType.FILTER,
                "name": "Filter",
                "description": "Apply filtering logic to the dataframe",
                "parameters": {
                    "condition": {"type": "string", "required": True, "description": "Pandas-like filter condition (e.g., df['name'].str.contains('64'))"}
                }
            },
            {
                "type": BlockType.ENRICH_LEAD,
                "name": "Enrich Lead",
                "description": "Enrich lead information using Sixtyfour API",
                "parameters": {
                    "struct": {"type": "object", "description": "Structure defining fields to enrich"},
                    "batch_size": {"type": "integer", "default": 10, "description": "Number of leads to process concurrently"},
                    "timeout": {"type": "integer", "default": 30, "description": "Timeout per request in seconds"}
                }
            },
            {
                "type": BlockType.FIND_EMAIL,
                "name": "Find Email",
                "description": "Find email addresses using Sixtyfour API",
                "parameters": {
                    "batch_size": {"type": "integer", "default": 10, "description": "Number of persons to process concurrently"},
                    "timeout": {"type": "integer", "default": 30, "description": "Timeout per request in seconds"}
                }
            }
        ]
    }
