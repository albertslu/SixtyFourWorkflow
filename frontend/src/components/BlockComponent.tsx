import { useState } from 'react'
import { TrashIcon, CogIcon, LinkIcon } from '@heroicons/react/24/outline'
import { BlockConfig, WorkflowConnection, BlockType } from '../types/workflow'

interface BlockComponentProps {
  block: BlockConfig
  onRemove: () => void
  onConfigure: () => void
  onConnect: (targetId: string) => void
  onMouseDown?: (event: React.MouseEvent) => void
  connections: WorkflowConnection[]
  isDragging?: boolean
}

const BLOCK_COLORS: Record<BlockType, string> = {
  read_csv: 'bg-blue-500',
  filter: 'bg-yellow-500',
  enrich_lead: 'bg-green-500',
  find_email: 'bg-purple-500',
  save_csv: 'bg-red-500'
}

const BLOCK_ICONS: Record<BlockType, string> = {
  read_csv: '📁',
  filter: '🔍',
  enrich_lead: '✨',
  find_email: '📧',
  save_csv: '💾'
}

export default function BlockComponent({
  block,
  onRemove,
  onConfigure,
  onConnect,
  onMouseDown,
  connections,
  isDragging = false
}: BlockComponentProps) {
  const [isHovered, setIsHovered] = useState(false)



  const getParameterSummary = () => {
    switch (block.block_type) {
      case 'read_csv':
        return block.parameters.file_path || 'No file selected'
      case 'filter':
        return block.parameters.condition ? 
          `${block.parameters.condition.substring(0, 30)}...` : 
          'No condition set'
      case 'enrich_lead':
        const structKeys = Object.keys(block.parameters.struct || {})
        return `${structKeys.length} fields`
      case 'find_email':
        return `Batch size: ${block.parameters.batch_size || 10}`
      case 'save_csv':
        return block.parameters.file_path || 'Auto-generated filename'
      default:
        return ''
    }
  }

  return (
    <div
      className={`
        relative bg-white rounded-lg shadow-md border-2 transition-all duration-200 cursor-move select-none
        ${isDragging ? 'border-blue-500 shadow-xl scale-105 z-50' : 'border-gray-200'}
        ${isHovered ? 'border-blue-300 shadow-lg' : ''}
        hover:shadow-lg
      `}
      style={{ 
        width: '200px', 
        minHeight: '120px',
        userSelect: 'none'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseDown={onMouseDown}
    >
      {/* Block Header */}
      <div className={`${BLOCK_COLORS[block.block_type]} text-white p-3 rounded-t-lg`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-lg mr-2">{BLOCK_ICONS[block.block_type]}</span>
            <span className="font-medium text-sm">{block.name}</span>
          </div>
          
          {/* Connection indicator */}
          {connections.length > 0 && (
            <div className="flex items-center">
              <LinkIcon className="w-4 h-4" />
              <span className="text-xs ml-1">{connections.length}</span>
            </div>
          )}
        </div>
      </div>

      {/* Block Content */}
      <div className="p-3">
        <div className="text-xs text-gray-600 mb-2">
          {getParameterSummary()}
        </div>
        
        {/* Block ID for debugging */}
        <div className="text-xs text-gray-400 font-mono">
          {block.block_id.substring(0, 8)}...
        </div>
      </div>

      {/* Action Buttons (shown on hover) */}
      {isHovered && (
        <div className="absolute -top-2 -right-2 flex space-x-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onConfigure()
            }}
            className="bg-blue-500 hover:bg-blue-600 text-white p-1 rounded-full shadow-lg transition-colors"
            title="Configure block"
          >
            <CogIcon className="w-4 h-4" />
          </button>
          
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRemove()
            }}
            className="bg-red-500 hover:bg-red-600 text-white p-1 rounded-full shadow-lg transition-colors"
            title="Remove block"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Connection Points */}
      <div className="absolute -left-2 top-1/2 transform -translate-y-1/2">
        <div className="w-4 h-4 bg-gray-300 rounded-full border-2 border-white shadow-sm" />
      </div>
      
      <div className="absolute -right-2 top-1/2 transform -translate-y-1/2">
        <div className="w-4 h-4 bg-gray-300 rounded-full border-2 border-white shadow-sm" />
      </div>

      {/* Status Indicators */}
      <div className="absolute bottom-2 right-2">
        {block.parameters && Object.keys(block.parameters).length > 0 && (
          <div className="w-2 h-2 bg-green-400 rounded-full" title="Configured" />
        )}
      </div>
    </div>
  )
}
