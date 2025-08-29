export type BlockType = 'read_csv' | 'save_csv' | 'filter' | 'enrich_lead' | 'find_email'

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface BlockConfig {
  block_id: string
  block_type: BlockType
  name: string
  description?: string
  parameters: Record<string, any>
  position: { x: number; y: number }
}

export interface WorkflowConnection {
  connection_id: string
  source_block_id: string
  target_block_id: string
}

export interface Workflow {
  workflow_id: string
  name: string
  description?: string
  blocks: BlockConfig[]
  connections: WorkflowConnection[]
  created_at: string
  updated_at: string
}

export interface JobProgress {
  current_step: number
  total_steps: number
  current_block_id?: string
  current_block_name?: string
  processed_rows: number
  total_rows: number
  message: string
  percentage: number
}

export interface JobResult {
  block_id: string
  block_type: BlockType
  success: boolean
  data?: Record<string, any>
  error?: string
  execution_time: number
  rows_processed: number
  rows_output: number
}

export interface Job {
  job_id: string
  workflow_id: string
  status: JobStatus
  progress: JobProgress
  results: JobResult[]
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  final_output_path?: string
}

export interface BlockTypeInfo {
  type: BlockType
  name: string
  description: string
  parameters: Record<string, {
    type: string
    required?: boolean
    default?: any
    description: string
  }>
}

// Drag and Drop Types
export interface DragItem {
  type: 'block' | 'new-block'
  blockType?: BlockType
  blockId?: string
}

export interface Position {
  x: number
  y: number
}
