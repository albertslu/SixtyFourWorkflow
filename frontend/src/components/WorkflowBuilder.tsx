import { useState, useCallback, useRef, useEffect } from 'react'
import { 
  PlusIcon, 
  PlayIcon, 
  BookmarkIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon 
} from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'
import { BlockConfig, WorkflowConnection, BlockType, Workflow } from '../types/workflow'
import { workflowApi } from '../lib/api'
import BlockComponent from './BlockComponent'
import BlockParametersModal from './BlockParametersModal'
import { v4 as uuidv4 } from 'uuid'

interface WorkflowBuilderProps {
  onJobCreated: (jobId: string) => void
}

const BLOCK_TYPES: { type: BlockType; name: string; description: string; color: string; icon: string }[] = [
  {
    type: 'read_csv',
    name: 'Read CSV',
    description: 'Load data from a CSV file',
    color: 'bg-blue-500',
    icon: '📁'
  },
  {
    type: 'filter',
    name: 'Filter',
    description: 'Filter rows based on conditions',
    color: 'bg-yellow-500',
    icon: '🔍'
  },
  {
    type: 'enrich_lead',
    name: 'Enrich Lead',
    description: 'Enrich lead data using Sixtyfour API',
    color: 'bg-green-500',
    icon: '✨'
  },
  {
    type: 'find_email',
    name: 'Find Email',
    description: 'Find email addresses using Sixtyfour API',
    color: 'bg-purple-500',
    icon: '📧'
  },
  {
    type: 'save_csv',
    name: 'Save CSV',
    description: 'Save data to a CSV file',
    color: 'bg-red-500',
    icon: '💾'
  }
]

export default function WorkflowBuilder({ onJobCreated }: WorkflowBuilderProps) {
  const [blocks, setBlocks] = useState<BlockConfig[]>([])
  const [connections, setConnections] = useState<WorkflowConnection[]>([])
  const [selectedBlock, setSelectedBlock] = useState<BlockConfig | null>(null)
  const [isParametersModalOpen, setIsParametersModalOpen] = useState(false)
  const [workflowName, setWorkflowName] = useState('My Workflow')
  const [isExecuting, setIsExecuting] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [savedWorkflowId, setSavedWorkflowId] = useState<string | null>(null)
  const [isPaletteOpen, setIsPaletteOpen] = useState(true)
  const [draggedBlock, setDraggedBlock] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const workflowCanvasRef = useRef<HTMLDivElement>(null)

  const addBlock = useCallback((blockType: BlockType, position?: { x: number; y: number }) => {
    // Calculate position based on existing blocks to avoid overlap
    const existingPositions = blocks.map(b => b.position)
    let x = position?.x || 200
    let y = position?.y || 200
    
    if (!position) {
      // Find a free position
      while (existingPositions.some(pos => 
        Math.abs(pos.x - x) < 220 && Math.abs(pos.y - y) < 140
      )) {
        x += 250
        if (x > 800) {
          x = 200
          y += 160
        }
      }
    }

    const newBlock: BlockConfig = {
      block_id: uuidv4(),
      block_type: blockType,
      name: BLOCK_TYPES.find(bt => bt.type === blockType)?.name || blockType,
      parameters: getDefaultParameters(blockType),
      position: { x, y }
    }
    setBlocks(prev => [...prev, newBlock])
    toast.success(`Added ${newBlock.name} block`)
  }, [blocks])

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

  // Enhanced drag handlers for smoother experience
  const handleMouseDown = useCallback((blockId: string, event: React.MouseEvent) => {
    event.preventDefault()
    const block = blocks.find(b => b.block_id === blockId)
    if (!block) return

    const rect = workflowCanvasRef.current?.getBoundingClientRect()
    if (!rect) return

    setDraggedBlock(blockId)
    setIsDragging(true)
    setDragOffset({
      x: event.clientX - rect.left - block.position.x,
      y: event.clientY - rect.top - block.position.y
    })

    // Add global mouse event listeners for smoother dragging
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (!rect) return
      
      const newX = e.clientX - rect.left - dragOffset.x
      const newY = e.clientY - rect.top - dragOffset.y

      // Constrain to canvas bounds with padding
      const constrainedX = Math.max(100, Math.min(rect.width - 100, newX))
      const constrainedY = Math.max(60, Math.min(rect.height - 60, newY))

      updateBlock(blockId, { 
        position: { x: constrainedX, y: constrainedY } 
      })
    }

    const handleGlobalMouseUp = () => {
      setDraggedBlock(null)
      setIsDragging(false)
      document.removeEventListener('mousemove', handleGlobalMouseMove)
      document.removeEventListener('mouseup', handleGlobalMouseUp)
    }

    document.addEventListener('mousemove', handleGlobalMouseMove)
    document.addEventListener('mouseup', handleGlobalMouseUp)
  }, [blocks, dragOffset.x, dragOffset.y, updateBlock])

  const saveWorkflow = useCallback(async () => {
    if (blocks.length === 0) {
      toast.error('Add at least one block to save workflow')
      return
    }

    setIsSaving(true)
    try {
      const workflow: Omit<Workflow, 'workflow_id' | 'created_at' | 'updated_at'> = {
        name: workflowName,
        description: `Workflow with ${blocks.length} blocks`,
        blocks,
        connections
      }

      let savedWorkflow: Workflow
      if (savedWorkflowId) {
        // Update existing workflow
        savedWorkflow = await workflowApi.updateWorkflow(savedWorkflowId, workflow)
        toast.success('Workflow updated successfully')
      } else {
        // Create new workflow
        savedWorkflow = await workflowApi.createWorkflow(workflow)
        setSavedWorkflowId(savedWorkflow.workflow_id)
        toast.success('Workflow saved successfully')
      }
    } catch (error: any) {
      console.error('Failed to save workflow:', error)
      toast.error(error.response?.data?.detail || 'Failed to save workflow')
    } finally {
      setIsSaving(false)
    }
  }, [blocks, connections, workflowName, savedWorkflowId])

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

  // Handle drag from palette to canvas
  const handlePaletteDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    const blockType = event.dataTransfer.getData('text/plain') as BlockType
    const rect = workflowCanvasRef.current?.getBoundingClientRect()
    if (!rect) return

    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    addBlock(blockType, { x, y })
  }, [addBlock])

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
  }, [])

  return (
    <div className="h-screen w-screen bg-gray-50 flex overflow-hidden">
      {/* Collapsible Block Palette */}
      <div className={`
        ${isPaletteOpen ? 'w-80' : 'w-12'} 
        bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex flex-col
      `}>
        {/* Palette Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          {isPaletteOpen ? (
            <>
              <h2 className="text-lg font-semibold text-gray-900">Block Palette</h2>
              <button
                onClick={() => setIsPaletteOpen(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <ChevronLeftIcon className="w-5 h-5 text-gray-500" />
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsPaletteOpen(true)}
              className="p-1 hover:bg-gray-100 rounded mx-auto"
            >
              <ChevronRightIcon className="w-5 h-5 text-gray-500" />
            </button>
          )}
        </div>

        {/* Palette Content */}
        {isPaletteOpen && (
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-3 mb-6">
              {BLOCK_TYPES.map((blockType) => (
                <div
                  key={blockType.type}
                  draggable
                  onDragStart={(e) => e.dataTransfer.setData('text/plain', blockType.type)}
                  onClick={() => addBlock(blockType.type)}
                  className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all group cursor-move bg-white"
                >
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">{blockType.icon}</div>
                    <div>
                      <div className="font-medium text-gray-900 group-hover:text-blue-600">
                        {blockType.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {blockType.description}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Workflow Controls */}
            <div className="border-t border-gray-200 pt-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow Name
                </label>
                <input
                  type="text"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="space-y-3">
                <button
                  onClick={saveWorkflow}
                  disabled={isSaving || blocks.length === 0}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
                >
                  <BookmarkIcon className="w-4 h-4 mr-2" />
                  {isSaving ? 'Saving...' : savedWorkflowId ? 'Update Workflow' : 'Save Workflow'}
                </button>

                <button
                  onClick={executeWorkflow}
                  disabled={isExecuting || blocks.length === 0}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
                >
                  <PlayIcon className="w-4 h-4 mr-2" />
                  {isExecuting ? 'Executing...' : 'Execute Workflow'}
                </button>
              </div>

              <div className="mt-4 text-sm text-gray-500 space-y-1">
                <div>Blocks: {blocks.length}</div>
                <div>Connections: {connections.length}</div>
                {savedWorkflowId && (
                  <div className="text-green-600">✓ Saved</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 relative">
        {/* Canvas */}
        <div 
          ref={workflowCanvasRef}
          className="w-full h-full bg-gray-50 relative overflow-hidden"
          onDrop={handlePaletteDrop}
          onDragOver={handleDragOver}
          style={{ 
            backgroundImage: `
              linear-gradient(to right, #e5e7eb 1px, transparent 1px),
              linear-gradient(to bottom, #e5e7eb 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px',
            backgroundPosition: '0 0'
          }}
        >
          {/* Blocks */}
          {blocks.map((block) => (
            <div
              key={block.block_id}
              className="absolute"
              style={{
                left: block.position.x,
                top: block.position.y,
                transform: 'translate(-50%, -50%)',
                zIndex: draggedBlock === block.block_id ? 1000 : 1
              }}
            >
              <BlockComponent
                block={block}
                onRemove={() => removeBlock(block.block_id)}
                onConfigure={() => openParametersModal(block)}
                onConnect={(targetId: string) => connectBlocks(block.block_id, targetId)}
                onMouseDown={(event: React.MouseEvent) => handleMouseDown(block.block_id, event)}
                connections={connections.filter(conn => 
                  conn.source_block_id === block.block_id || conn.target_block_id === block.block_id
                )}
                isDragging={draggedBlock === block.block_id}
              />
            </div>
          ))}

          {/* Connection Lines */}
          <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 2 }}>
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
                  stroke="#3b82f6"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                  className="drop-shadow-sm"
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
                  fill="#3b82f6"
                />
              </marker>
            </defs>
          </svg>

          {/* Empty State */}
          {blocks.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <div className="text-6xl mb-4">🎯</div>
                <h3 className="text-xl font-medium text-gray-900 mb-2">
                  Start Building Your Workflow
                </h3>
                <p className="text-gray-500 mb-4 max-w-md">
                  Drag blocks from the palette or click on them to add to your workflow. 
                  Connect blocks to create your data processing pipeline.
                </p>
                {!isPaletteOpen && (
                  <button
                    onClick={() => setIsPaletteOpen(true)}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Bars3Icon className="w-4 h-4 mr-2" />
                    Open Block Palette
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Floating Palette Toggle (when closed) */}
          {!isPaletteOpen && blocks.length > 0 && (
            <button
              onClick={() => setIsPaletteOpen(true)}
              className="absolute top-4 left-4 p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              <Bars3Icon className="w-5 h-5 text-gray-600" />
            </button>
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