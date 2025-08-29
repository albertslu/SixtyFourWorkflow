import { useState, useCallback, useRef } from 'react'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import { PlusIcon, PlayIcon, TrashIcon, CogIcon } from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'
import { BlockConfig, WorkflowConnection, BlockType, Workflow } from '../types/workflow'
import { workflowApi } from '../lib/api'
import BlockComponent from './BlockComponent'
import BlockParametersModal from './BlockParametersModal'
import { v4 as uuidv4 } from 'uuid'

interface WorkflowBuilderProps {
  onJobCreated: (jobId: string) => void
}

const BLOCK_TYPES: { type: BlockType; name: string; description: string; color: string }[] = [
  {
    type: 'read_csv',
    name: 'Read CSV',
    description: 'Load data from a CSV file',
    color: 'bg-blue-500'
  },
  {
    type: 'filter',
    name: 'Filter',
    description: 'Filter rows based on conditions',
    color: 'bg-yellow-500'
  },
  {
    type: 'enrich_lead',
    name: 'Enrich Lead',
    description: 'Enrich lead data using Sixtyfour API',
    color: 'bg-green-500'
  },
  {
    type: 'find_email',
    name: 'Find Email',
    description: 'Find email addresses using Sixtyfour API',
    color: 'bg-purple-500'
  },
  {
    type: 'save_csv',
    name: 'Save CSV',
    description: 'Save data to a CSV file',
    color: 'bg-red-500'
  }
]

export default function WorkflowBuilder({ onJobCreated }: WorkflowBuilderProps) {
  const [blocks, setBlocks] = useState<BlockConfig[]>([])
  const [connections, setConnections] = useState<WorkflowConnection[]>([])
  const [selectedBlock, setSelectedBlock] = useState<BlockConfig | null>(null)
  const [isParametersModalOpen, setIsParametersModalOpen] = useState(false)
  const [workflowName, setWorkflowName] = useState('My Workflow')
  const [isExecuting, setIsExecuting] = useState(false)
  const workflowCanvasRef = useRef<HTMLDivElement>(null)

  const addBlock = useCallback((blockType: BlockType) => {
    const newBlock: BlockConfig = {
      block_id: uuidv4(),
      block_type: blockType,
      name: BLOCK_TYPES.find(bt => bt.type === blockType)?.name || blockType,
      parameters: getDefaultParameters(blockType),
      position: { x: Math.random() * 400, y: Math.random() * 200 }
    }
    setBlocks(prev => [...prev, newBlock])
    toast.success(`Added ${newBlock.name} block`)
  }, [])

  const removeBlock = useCallback((blockId: string) => {
    setBlocks(prev => prev.filter(block => block.block_id !== blockId))
    setConnections(prev => prev.filter(conn => 
      conn.source_block_id !== blockId && conn.target_block_id !== blockId
    ))
    toast.success('Block removed')
  }, [])

  const updateBlock = useCallback((blockId: string, updates: Partial<BlockConfig>) => {
    setBlocks(prev => prev.map(block => 
      block.block_id === blockId ? { ...block, ...updates } : block
    ))
  }, [])

  const connectBlocks = useCallback((sourceId: string, targetId: string) => {
    // Check if connection already exists
    const existingConnection = connections.find(conn => 
      conn.source_block_id === sourceId && conn.target_block_id === targetId
    )
    
    if (existingConnection) {
      toast.error('Connection already exists')
      return
    }

    // Check for circular dependencies (basic check)
    if (sourceId === targetId) {
      toast.error('Cannot connect block to itself')
      return
    }

    const newConnection: WorkflowConnection = {
      connection_id: uuidv4(),
      source_block_id: sourceId,
      target_block_id: targetId
    }

    setConnections(prev => [...prev, newConnection])
    toast.success('Blocks connected')
  }, [connections])

  const removeConnection = useCallback((connectionId: string) => {
    setConnections(prev => prev.filter(conn => conn.connection_id !== connectionId))
    toast.success('Connection removed')
  }, [])

  const executeWorkflow = useCallback(async () => {
    if (blocks.length === 0) {
      toast.error('Add at least one block to execute workflow')
      return
    }

    setIsExecuting(true)
    try {
      // Create workflow
      const workflow: Omit<Workflow, 'workflow_id' | 'created_at' | 'updated_at'> = {
        name: workflowName,
        description: `Workflow with ${blocks.length} blocks`,
        blocks,
        connections
      }

      const createdWorkflow = await workflowApi.createWorkflow(workflow)
      toast.success('Workflow created successfully')

      // Execute workflow
      const execution = await workflowApi.executeWorkflow(createdWorkflow.workflow_id)
      toast.success('Workflow execution started')
      
      onJobCreated(execution.job_id)
    } catch (error: any) {
      console.error('Workflow execution failed:', error)
      toast.error(error.response?.data?.detail || 'Failed to execute workflow')
    } finally {
      setIsExecuting(false)
    }
  }, [blocks, connections, workflowName, onJobCreated])

  const openParametersModal = useCallback((block: BlockConfig) => {
    setSelectedBlock(block)
    setIsParametersModalOpen(true)
  }, [])

  const handleParametersUpdate = useCallback((blockId: string, parameters: Record<string, any>) => {
    updateBlock(blockId, { parameters })
    setIsParametersModalOpen(false)
    setSelectedBlock(null)
    toast.success('Block parameters updated')
  }, [updateBlock])

  return (
    <div className="h-full flex">
      {/* Block Palette */}
      <div className="w-80 bg-white border-r border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Block Palette</h2>
        
        <div className="space-y-3">
          {BLOCK_TYPES.map((blockType) => (
            <button
              key={blockType.type}
              onClick={() => addBlock(blockType.type)}
              className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center">
                <div className={`w-4 h-4 rounded ${blockType.color} mr-3`} />
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-primary-600">
                    {blockType.name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {blockType.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Workflow Controls */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Workflow Name
            </label>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <button
            onClick={executeWorkflow}
            disabled={isExecuting || blocks.length === 0}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <PlayIcon className="w-4 h-4 mr-2" />
            {isExecuting ? 'Executing...' : 'Execute Workflow'}
          </button>

          <div className="mt-4 text-sm text-gray-500">
            <div>Blocks: {blocks.length}</div>
            <div>Connections: {connections.length}</div>
          </div>
        </div>
      </div>

      {/* Workflow Canvas */}
      <div className="flex-1 relative overflow-hidden">
        <div 
          ref={workflowCanvasRef}
          className="w-full h-full bg-gray-50 relative"
          style={{ minHeight: '600px' }}
        >
          {/* Grid Background */}
          <div 
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage: `
                linear-gradient(to right, #e5e7eb 1px, transparent 1px),
                linear-gradient(to bottom, #e5e7eb 1px, transparent 1px)
              `,
              backgroundSize: '20px 20px'
            }}
          />

          {/* Blocks */}
          {blocks.map((block) => (
            <div
              key={block.block_id}
              className="absolute"
              style={{
                left: block.position.x,
                top: block.position.y,
                transform: 'translate(-50%, -50%)'
              }}
            >
              <BlockComponent
                block={block}
                onRemove={() => removeBlock(block.block_id)}
                onConfigure={() => openParametersModal(block)}
                onConnect={(targetId) => connectBlocks(block.block_id, targetId)}
                connections={connections.filter(conn => 
                  conn.source_block_id === block.block_id || conn.target_block_id === block.block_id
                )}
              />
            </div>
          ))}

          {/* Connection Lines */}
          <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
            {connections.map((connection) => {
              const sourceBlock = blocks.find(b => b.block_id === connection.source_block_id)
              const targetBlock = blocks.find(b => b.block_id === connection.target_block_id)
              
              if (!sourceBlock || !targetBlock) return null

              return (
                <line
                  key={connection.connection_id}
                  x1={sourceBlock.position.x}
                  y1={sourceBlock.position.y}
                  x2={targetBlock.position.x}
                  y2={targetBlock.position.y}
                  stroke="#6366f1"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
              )
            })}
            
            {/* Arrow marker definition */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon
                  points="0 0, 10 3.5, 0 7"
                  fill="#6366f1"
                />
              </marker>
            </defs>
          </svg>

          {/* Empty State */}
          {blocks.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <PlusIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Start Building Your Workflow
                </h3>
                <p className="text-gray-500 mb-4">
                  Add blocks from the palette to create your data processing workflow
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Block Parameters Modal */}
      {selectedBlock && (
        <BlockParametersModal
          isOpen={isParametersModalOpen}
          onClose={() => {
            setIsParametersModalOpen(false)
            setSelectedBlock(null)
          }}
          block={selectedBlock}
          onSave={handleParametersUpdate}
        />
      )}
    </div>
  )
}

function getDefaultParameters(blockType: BlockType): Record<string, any> {
  switch (blockType) {
    case 'read_csv':
      return {
        file_path: 'sample_data.csv',
        delimiter: ',',
        encoding: 'utf-8',
        skip_rows: 0
      }
    case 'save_csv':
      return {
        file_path: '',
        delimiter: ',',
        encoding: 'utf-8',
        index: false
      }
    case 'filter':
      return {
        condition: "df['company'].str.contains('Ariglad', na=False)"
      }
    case 'enrich_lead':
      return {
        struct: {
          name: 'Full name',
          email: 'Email address',
          company: 'Company name',
          title: 'Job title',
          linkedin: 'LinkedIn URL',
          education: 'Educational background including university'
        },
        batch_size: 10,
        timeout: 30
      }
    case 'find_email':
      return {
        batch_size: 10,
        timeout: 30
      }
    default:
      return {}
  }
}
