import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { BlockConfig } from '../types/workflow'

interface BlockParametersModalProps {
  isOpen: boolean
  onClose: () => void
  block: BlockConfig
  onSave: (blockId: string, parameters: Record<string, any>) => void
}

export default function BlockParametersModal({
  isOpen,
  onClose,
  block,
  onSave
}: BlockParametersModalProps) {
  const [parameters, setParameters] = useState<Record<string, any>>({})

  useEffect(() => {
    if (isOpen && block) {
      setParameters({ ...block.parameters })
    }
  }, [isOpen, block])

  const handleSave = () => {
    onSave(block.block_id, parameters)
  }

  const updateParameter = (key: string, value: any) => {
    setParameters(prev => ({ ...prev, [key]: value }))
  }

  const renderParameterInput = (key: string, value: any, type: string = 'text') => {
    switch (type) {
      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={(e) => updateParameter(key, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            rows={3}
          />
        )
      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => updateParameter(key, parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        )
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => updateParameter(key, e.target.checked)}
            className="w-4 h-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          />
        )
      case 'object':
        return (
          <textarea
            value={JSON.stringify(value || {}, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value)
                updateParameter(key, parsed)
              } catch (err) {
                // Invalid JSON, don't update
              }
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
            rows={6}
          />
        )
      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => updateParameter(key, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        )
    }
  }

  const renderBlockSpecificParameters = () => {
    switch (block.block_type) {
      case 'read_csv':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File Path
              </label>
              {renderParameterInput('file_path', parameters.file_path)}
              <p className="text-xs text-gray-500 mt-1">
                Path to the CSV file to read
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Delimiter
              </label>
              {renderParameterInput('delimiter', parameters.delimiter)}
              <p className="text-xs text-gray-500 mt-1">
                Character used to separate values (default: comma)
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Encoding
              </label>
              {renderParameterInput('encoding', parameters.encoding)}
              <p className="text-xs text-gray-500 mt-1">
                File encoding (default: utf-8)
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Skip Rows
              </label>
              {renderParameterInput('skip_rows', parameters.skip_rows, 'number')}
              <p className="text-xs text-gray-500 mt-1">
                Number of rows to skip at the beginning
              </p>
            </div>
          </div>
        )

      case 'filter':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter Condition
              </label>
              {renderParameterInput('condition', parameters.condition, 'textarea')}
              <p className="text-xs text-gray-500 mt-1">
                Pandas-like condition (e.g., df['company'].str.contains('Ariglad'))
              </p>
            </div>
            
            <div className="bg-gray-50 p-3 rounded-md">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Examples:</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <div>• df['company'].str.contains('Ariglad', na=False)</div>
                <div>• df['name'].str.len() &gt; 5</div>
                <div>• df['email'].notna()</div>
              </div>
            </div>
          </div>
        )

      case 'enrich_lead':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Structure (JSON)
              </label>
              {renderParameterInput('struct', parameters.struct, 'object')}
              <p className="text-xs text-gray-500 mt-1">
                Define what fields to enrich and their descriptions
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Batch Size
              </label>
              {renderParameterInput('batch_size', parameters.batch_size, 'number')}
              <p className="text-xs text-gray-500 mt-1">
                Number of leads to process concurrently
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeout (seconds)
              </label>
              {renderParameterInput('timeout', parameters.timeout, 'number')}
              <p className="text-xs text-gray-500 mt-1">
                Timeout per API request
              </p>
            </div>
          </div>
        )

      case 'find_email':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Batch Size
              </label>
              {renderParameterInput('batch_size', parameters.batch_size, 'number')}
              <p className="text-xs text-gray-500 mt-1">
                Number of persons to process concurrently
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeout (seconds)
              </label>
              {renderParameterInput('timeout', parameters.timeout, 'number')}
              <p className="text-xs text-gray-500 mt-1">
                Timeout per API request
              </p>
            </div>
          </div>
        )

      case 'save_csv':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File Path
              </label>
              {renderParameterInput('file_path', parameters.file_path)}
              <p className="text-xs text-gray-500 mt-1">
                Output file path (leave empty for auto-generated name)
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Delimiter
              </label>
              {renderParameterInput('delimiter', parameters.delimiter)}
              <p className="text-xs text-gray-500 mt-1">
                Character used to separate values
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Encoding
              </label>
              {renderParameterInput('encoding', parameters.encoding)}
              <p className="text-xs text-gray-500 mt-1">
                File encoding
              </p>
            </div>
            
            <div className="flex items-center">
              <label className="block text-sm font-medium text-gray-700 mr-3">
                Include Index
              </label>
              {renderParameterInput('index', parameters.index, 'boolean')}
              <p className="text-xs text-gray-500 ml-3">
                Include row index in output
              </p>
            </div>
          </div>
        )

      default:
        return (
          <div className="text-center text-gray-500">
            No parameters available for this block type
          </div>
        )
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Configure {block.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {renderBlockSpecificParameters()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="btn-primary"
          >
            Save Parameters
          </button>
        </div>
      </div>
    </div>
  )
}
