"""
Workflow execution engine with dataframe management
"""
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import os
from pathlib import Path
import time
from loguru import logger

from models.workflow import (
    Workflow, Job, JobStatus, JobProgress, JobResult, BlockType, BlockConfig
)
from services.database_service import db_service
from services.sixtyfour_service import sixtyfour_service
from core.config import settings


class WorkflowExecutionError(Exception):
    """Custom exception for workflow execution errors"""
    pass


class DataFrameManager:
    """Manages dataframes during workflow execution"""
    
    def __init__(self):
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def store_dataframe(self, key: str, df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None):
        """Store a dataframe with optional metadata"""
        self.dataframes[key] = df.copy()
        self.metadata[key] = metadata or {}
        logger.info(f"Stored dataframe '{key}' with {len(df)} rows, {len(df.columns)} columns")
    
    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """Get a dataframe by key"""
        return self.dataframes.get(key)
    
    def get_metadata(self, key: str) -> Dict[str, Any]:
        """Get metadata for a dataframe"""
        return self.metadata.get(key, {})
    
    def clear(self):
        """Clear all stored dataframes"""
        self.dataframes.clear()
        self.metadata.clear()


class WorkflowExecutor:
    """Main workflow execution engine"""
    
    def __init__(self):
        self.df_manager = DataFrameManager()
        self.current_job: Optional[Job] = None
    
    async def execute_workflow(self, workflow: Workflow, input_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a complete workflow
        
        Args:
            workflow: The workflow to execute
            input_data: Optional input data for the workflow
            
        Returns:
            Job ID for tracking execution
        """
        # Create a new job
        job = Job(
            workflow_id=workflow.workflow_id,
            status=JobStatus.PENDING,
            progress=JobProgress(
                total_steps=len(workflow.blocks),
                message="Workflow queued for execution"
            )
        )
        
        # Save job to database
        await db_service.save_job(job)
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow_async(workflow, job, input_data))
        
        return job.job_id
    
    async def _execute_workflow_async(self, workflow: Workflow, job: Job, input_data: Optional[Dict[str, Any]]):
        """Execute workflow asynchronously"""
        self.current_job = job
        self.df_manager.clear()
        
        try:
            # Update job status to running
            await db_service.update_job_status(job.job_id, JobStatus.RUNNING)
            
            # Build execution order from workflow connections
            execution_order = self._build_execution_order(workflow)
            
            # Execute blocks in order
            current_df_key = "main"
            
            for step, block_id in enumerate(execution_order):
                block = next((b for b in workflow.blocks if b.block_id == block_id), None)
                if not block:
                    raise WorkflowExecutionError(f"Block {block_id} not found in workflow")
                
                # Update progress
                progress = JobProgress(
                    current_step=step + 1,
                    total_steps=len(execution_order),
                    current_block_id=block.block_id,
                    current_block_name=block.name,
                    message=f"Executing {block.name}",
                    percentage=((step + 1) / len(execution_order)) * 100
                )
                await db_service.update_job_progress(job.job_id, progress)
                
                # Execute the block
                result = await self._execute_block(block, current_df_key)
                
                # Save result
                await db_service.add_job_result(job.job_id, result)
                
                if not result.success:
                    raise WorkflowExecutionError(f"Block {block.name} failed: {result.error}")
                
                # Update current dataframe key if block produces output
                if result.data and 'output_df_key' in result.data:
                    current_df_key = result.data['output_df_key']
            
            # Mark job as completed
            final_df = self.df_manager.get_dataframe(current_df_key)
            final_output_path = None
            
            if final_df is not None:
                # Save final output
                final_output_path = f"{settings.upload_folder}/output_{job.job_id}.csv"
                os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
                final_df.to_csv(final_output_path, index=False)
                logger.info(f"Saved final output to {final_output_path}")
            
            # Update job completion
            await db_service.update_job_status(job.job_id, JobStatus.COMPLETED)
            
            # Update final progress
            final_progress = JobProgress(
                current_step=len(execution_order),
                total_steps=len(execution_order),
                message="Workflow completed successfully",
                percentage=100.0
            )
            await db_service.update_job_progress(job.job_id, final_progress)
            
            logger.info(f"Workflow {workflow.workflow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            await db_service.update_job_status(job.job_id, JobStatus.FAILED, str(e))
            
            # Update progress with error
            error_progress = JobProgress(
                current_step=job.progress.current_step,
                total_steps=job.progress.total_steps,
                message=f"Workflow failed: {str(e)}",
                percentage=job.progress.percentage
            )
            await db_service.update_job_progress(job.job_id, error_progress)
    
    def _build_execution_order(self, workflow: Workflow) -> List[str]:
        """
        Build execution order from workflow connections
        For now, we'll use a simple topological sort
        """
        # Create adjacency list
        graph = {block.block_id: [] for block in workflow.blocks}
        in_degree = {block.block_id: 0 for block in workflow.blocks}
        
        for connection in workflow.connections:
            graph[connection.source_block_id].append(connection.target_block_id)
            in_degree[connection.target_block_id] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [block_id for block_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(execution_order) != len(workflow.blocks):
            raise WorkflowExecutionError("Workflow contains cycles or disconnected components")
        
        return execution_order
    
    async def _execute_block(self, block: BlockConfig, input_df_key: str) -> JobResult:
        """Execute a single workflow block"""
        start_time = time.time()
        
        try:
            if block.block_type == BlockType.READ_CSV:
                return await self._execute_read_csv(block, input_df_key)
            elif block.block_type == BlockType.SAVE_CSV:
                return await self._execute_save_csv(block, input_df_key)
            elif block.block_type == BlockType.FILTER:
                return await self._execute_filter(block, input_df_key)
            elif block.block_type == BlockType.ENRICH_LEAD:
                return await self._execute_enrich_lead(block, input_df_key)
            elif block.block_type == BlockType.FIND_EMAIL:
                return await self._execute_find_email(block, input_df_key)
            else:
                raise WorkflowExecutionError(f"Unknown block type: {block.block_type}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Block {block.name} failed: {str(e)}")
            return JobResult(
                block_id=block.block_id,
                block_type=block.block_type,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_read_csv(self, block: BlockConfig, input_df_key: str) -> JobResult:
        """Execute Read CSV block"""
        start_time = time.time()
        
        file_path = block.parameters.get('file_path', '')
        delimiter = block.parameters.get('delimiter', ',')
        encoding = block.parameters.get('encoding', 'utf-8')
        skip_rows = block.parameters.get('skip_rows', 0)
        
        if not file_path:
            raise WorkflowExecutionError("File path is required for Read CSV block")
        
        # Handle relative paths
        if not os.path.isabs(file_path):
            # Remove leading ./ if present
            if file_path.startswith('./'):
                file_path = file_path[2:]
            file_path = os.path.join(settings.upload_folder, file_path)
        
        if not os.path.exists(file_path):
            raise WorkflowExecutionError(f"File not found: {file_path}")
        
        # Read CSV
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            skiprows=skip_rows
        )
        
        # Store dataframe
        output_key = f"{block.block_id}_output"
        self.df_manager.store_dataframe(output_key, df, {
            'source_file': file_path,
            'block_id': block.block_id
        })
        
        execution_time = time.time() - start_time
        
        return JobResult(
            block_id=block.block_id,
            block_type=block.block_type,
            success=True,
            data={
                'output_df_key': output_key,
                'rows_loaded': len(df),
                'columns': list(df.columns),
                'file_path': file_path
            },
            execution_time=execution_time,
            rows_processed=0,
            rows_output=len(df)
        )
    
    async def _execute_save_csv(self, block: BlockConfig, input_df_key: str) -> JobResult:
        """Execute Save CSV block"""
        start_time = time.time()
        
        df = self.df_manager.get_dataframe(input_df_key)
        if df is None:
            raise WorkflowExecutionError(f"No dataframe found with key: {input_df_key}")
        
        file_path = block.parameters.get('file_path', '')
        delimiter = block.parameters.get('delimiter', ',')
        encoding = block.parameters.get('encoding', 'utf-8')
        include_index = block.parameters.get('index', False)
        
        if not file_path:
            # Generate default filename
            file_path = f"output_{block.block_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Handle relative paths
        if not os.path.isabs(file_path):
            # Remove leading ./ if present
            if file_path.startswith('./'):
                file_path = file_path[2:]
            file_path = os.path.join(settings.upload_folder, file_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save CSV
        df.to_csv(
            file_path,
            sep=delimiter,
            encoding=encoding,
            index=include_index
        )
        
        execution_time = time.time() - start_time
        
        return JobResult(
            block_id=block.block_id,
            block_type=block.block_type,
            success=True,
            data={
                'output_df_key': input_df_key,  # Pass through the same dataframe
                'file_path': file_path,
                'rows_saved': len(df)
            },
            execution_time=execution_time,
            rows_processed=len(df),
            rows_output=len(df)
        )
    
    async def _execute_filter(self, block: BlockConfig, input_df_key: str) -> JobResult:
        """Execute Filter block with pandas-like operations"""
        start_time = time.time()
        
        df = self.df_manager.get_dataframe(input_df_key)
        if df is None:
            raise WorkflowExecutionError(f"No dataframe found with key: {input_df_key}")
        
        condition = block.parameters.get('condition', '')
        if not condition:
            raise WorkflowExecutionError("Filter condition is required")
        
        original_count = len(df)
        
        try:
            # Create a safe environment for eval
            # This is a simplified approach - in production, you'd want more robust parsing
            safe_dict = {
                'df': df,
                'pd': pd,
                'np': np,
                'str': str,
                'len': len,
                'int': int,
                'float': float,
                'bool': bool
            }
            
            # Evaluate the condition
            mask = eval(condition, {"__builtins__": {}}, safe_dict)
            
            if isinstance(mask, pd.Series):
                filtered_df = df[mask]
            else:
                raise WorkflowExecutionError("Filter condition must return a boolean Series")
            
        except Exception as e:
            raise WorkflowExecutionError(f"Invalid filter condition: {str(e)}")
        
        # Store filtered dataframe
        output_key = f"{block.block_id}_output"
        self.df_manager.store_dataframe(output_key, filtered_df, {
            'filter_condition': condition,
            'original_rows': original_count,
            'filtered_rows': len(filtered_df),
            'block_id': block.block_id
        })
        
        execution_time = time.time() - start_time
        
        return JobResult(
            block_id=block.block_id,
            block_type=block.block_type,
            success=True,
            data={
                'output_df_key': output_key,
                'original_rows': original_count,
                'filtered_rows': len(filtered_df),
                'condition': condition
            },
            execution_time=execution_time,
            rows_processed=original_count,
            rows_output=len(filtered_df)
        )
    
    async def _execute_enrich_lead(self, block: BlockConfig, input_df_key: str) -> JobResult:
        """Execute Enrich Lead block using Sixtyfour API"""
        start_time = time.time()
        
        df = self.df_manager.get_dataframe(input_df_key)
        if df is None:
            raise WorkflowExecutionError(f"No dataframe found with key: {input_df_key}")
        
        struct = block.parameters.get('struct', {})
        batch_size = block.parameters.get('batch_size', 10)
        
        # Convert dataframe rows to lead info format
        leads = []
        for _, row in df.iterrows():
            lead_info = {}
            for col in df.columns:
                if pd.notna(row[col]):
                    lead_info[col] = str(row[col])
            leads.append(lead_info)
        
        # Process in batches for better performance
        enriched_results = []
        total_leads = len(leads)
        
        for i in range(0, total_leads, batch_size):
            batch = leads[i:i + batch_size]
            batch_results = await sixtyfour_service.batch_enrich_leads(batch, struct)
            enriched_results.extend(batch_results)
            
            # Update progress if we have a current job
            if self.current_job:
                processed = min(i + batch_size, total_leads)
                progress = JobProgress(
                    current_step=self.current_job.progress.current_step,
                    total_steps=self.current_job.progress.total_steps,
                    current_block_id=block.block_id,
                    current_block_name=block.name,
                    processed_rows=processed,
                    total_rows=total_leads,
                    message=f"Enriching leads: {processed}/{total_leads}",
                    percentage=self.current_job.progress.percentage
                )
                await db_service.update_job_progress(self.current_job.job_id, progress)
        
        # Convert results back to dataframe
        enriched_df = pd.DataFrame(enriched_results)
        
        # Store enriched dataframe
        output_key = f"{block.block_id}_output"
        self.df_manager.store_dataframe(output_key, enriched_df, {
            'enrichment_struct': struct,
            'original_rows': len(df),
            'enriched_rows': len(enriched_df),
            'block_id': block.block_id
        })
        
        execution_time = time.time() - start_time
        successful_enrichments = len([r for r in enriched_results if r.get('_enrichment_status') == 'success'])
        
        return JobResult(
            block_id=block.block_id,
            block_type=block.block_type,
            success=True,
            data={
                'output_df_key': output_key,
                'original_rows': len(df),
                'enriched_rows': len(enriched_df),
                'successful_enrichments': successful_enrichments,
                'struct_fields': list(struct.keys())
            },
            execution_time=execution_time,
            rows_processed=len(df),
            rows_output=len(enriched_df)
        )
    
    async def _execute_find_email(self, block: BlockConfig, input_df_key: str) -> JobResult:
        """Execute Find Email block using Sixtyfour API"""
        start_time = time.time()
        
        df = self.df_manager.get_dataframe(input_df_key)
        if df is None:
            raise WorkflowExecutionError(f"No dataframe found with key: {input_df_key}")
        
        batch_size = block.parameters.get('batch_size', 10)
        
        # Convert dataframe rows to person info format
        persons = []
        for _, row in df.iterrows():
            person_info = {}
            for col in df.columns:
                if pd.notna(row[col]):
                    person_info[col] = str(row[col])
            persons.append(person_info)
        
        # Process in batches
        email_results = []
        total_persons = len(persons)
        
        for i in range(0, total_persons, batch_size):
            batch = persons[i:i + batch_size]
            batch_results = await sixtyfour_service.batch_find_emails(batch)
            email_results.extend(batch_results)
            
            # Update progress
            if self.current_job:
                processed = min(i + batch_size, total_persons)
                progress = JobProgress(
                    current_step=self.current_job.progress.current_step,
                    total_steps=self.current_job.progress.total_steps,
                    current_block_id=block.block_id,
                    current_block_name=block.name,
                    processed_rows=processed,
                    total_rows=total_persons,
                    message=f"Finding emails: {processed}/{total_persons}",
                    percentage=self.current_job.progress.percentage
                )
                await db_service.update_job_progress(self.current_job.job_id, progress)
        
        # Convert results back to dataframe
        results_df = pd.DataFrame(email_results)
        
        # Store results dataframe
        output_key = f"{block.block_id}_output"
        self.df_manager.store_dataframe(output_key, results_df, {
            'original_rows': len(df),
            'results_rows': len(results_df),
            'block_id': block.block_id
        })
        
        execution_time = time.time() - start_time
        successful_finds = len([r for r in email_results if r.get('_email_find_status') == 'success'])
        
        return JobResult(
            block_id=block.block_id,
            block_type=block.block_type,
            success=True,
            data={
                'output_df_key': output_key,
                'original_rows': len(df),
                'results_rows': len(results_df),
                'successful_finds': successful_finds
            },
            execution_time=execution_time,
            rows_processed=len(df),
            rows_output=len(results_df)
        )


# Global workflow executor instance
workflow_executor = WorkflowExecutor()
