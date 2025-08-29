"""
Data models for workflow blocks and execution
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class BlockType(str, Enum):
    """Enumeration of available workflow block types"""
    READ_CSV = "read_csv"
    SAVE_CSV = "save_csv"
    FILTER = "filter"
    ENRICH_LEAD = "enrich_lead"
    FIND_EMAIL = "find_email"


class JobStatus(str, Enum):
    """Enumeration of job execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BlockConfig(BaseModel):
    """Base configuration for workflow blocks"""
    block_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    block_type: BlockType
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})


class ReadCSVConfig(BlockConfig):
    """Configuration for Read CSV block"""
    block_type: BlockType = BlockType.READ_CSV
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "file_path": "",
        "delimiter": ",",
        "encoding": "utf-8",
        "skip_rows": 0
    })


class SaveCSVConfig(BlockConfig):
    """Configuration for Save CSV block"""
    block_type: BlockType = BlockType.SAVE_CSV
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "file_path": "",
        "delimiter": ",",
        "encoding": "utf-8",
        "index": False
    })


class FilterConfig(BlockConfig):
    """Configuration for Filter block"""
    block_type: BlockType = BlockType.FILTER
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "condition": "",  # e.g., "df['name'].str.contains('64')"
        "description": "Filter condition to apply"
    })


class EnrichLeadConfig(BlockConfig):
    """Configuration for Enrich Lead block"""
    block_type: BlockType = BlockType.ENRICH_LEAD
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "struct": {
            "name": "Full name",
            "email": "Email address",
            "company": "Company name", 
            "title": "Job title",
            "linkedin": "LinkedIn URL",
            "website": "Company website",
            "location": "Location",
            "industry": "Industry",
            "education": "Educational background including university"
        },
        "batch_size": 10,  # Number of leads to process concurrently
        "timeout": 30  # Timeout per request in seconds
    })


class FindEmailConfig(BlockConfig):
    """Configuration for Find Email block"""
    block_type: BlockType = BlockType.FIND_EMAIL
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "batch_size": 10,
        "timeout": 30
    })


class WorkflowConnection(BaseModel):
    """Represents a connection between workflow blocks"""
    source_block_id: str
    target_block_id: str
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class Workflow(BaseModel):
    """Complete workflow definition"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    blocks: List[BlockConfig] = Field(default_factory=list)
    connections: List[WorkflowConnection] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class JobProgress(BaseModel):
    """Progress information for a job"""
    current_step: int = 0
    total_steps: int = 0
    current_block_id: Optional[str] = None
    current_block_name: Optional[str] = None
    processed_rows: int = 0
    total_rows: int = 0
    message: str = ""
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class JobResult(BaseModel):
    """Result data from job execution"""
    block_id: str
    block_type: BlockType
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0  # Execution time in seconds
    rows_processed: int = 0
    rows_output: int = 0


class Job(BaseModel):
    """Job execution model"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = Field(default_factory=JobProgress)
    results: List[JobResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    final_output_path: Optional[str] = None


class WorkflowExecutionRequest(BaseModel):
    """Request model for executing a workflow"""
    workflow: Workflow
    input_data: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution"""
    job_id: str
    status: JobStatus
    message: str = "Workflow execution started"


# Block configuration factory
def create_block_config(block_type: BlockType, **kwargs) -> BlockConfig:
    """Factory function to create appropriate block configuration"""
    config_classes = {
        BlockType.READ_CSV: ReadCSVConfig,
        BlockType.SAVE_CSV: SaveCSVConfig,
        BlockType.FILTER: FilterConfig,
        BlockType.ENRICH_LEAD: EnrichLeadConfig,
        BlockType.FIND_EMAIL: FindEmailConfig,
    }
    
    config_class = config_classes.get(block_type, BlockConfig)
    return config_class(block_type=block_type, **kwargs)
