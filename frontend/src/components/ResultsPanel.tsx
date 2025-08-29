import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  DocumentArrowDownIcon, 
  EyeIcon, 
  ChartBarIcon,
  TableCellsIcon
} from '@heroicons/react/24/outline'
import { jobsApi, workflowApi } from '../lib/api'
import { toast } from 'react-hot-toast'

interface ResultsPanelProps {
  jobId: string | null
}

export default function ResultsPanel({ jobId }: ResultsPanelProps) {
  const [selectedResult, setSelectedResult] = useState<any>(null)
  const [viewMode, setViewMode] = useState<'table' | 'json'>('table')

  // Fetch job results
  const { data: jobResults, isLoading } = useQuery(
    ['job-results', jobId],
    () => jobId ? jobsApi.getJobResults(jobId) : null,
    {
      enabled: !!jobId,
      onError: (error: any) => {
        console.error('Failed to fetch job results:', error)
        toast.error('Failed to fetch job results')
      }
    }
  )

  // Fetch job details
  const { data: jobDetails } = useQuery(
    ['job-details', jobId],
    () => jobId ? jobsApi.getJob(jobId) : null,
    {
      enabled: !!jobId,
      onError: (error: any) => {
        console.error('Failed to fetch job details:', error)
      }
    }
  )

  const handleDownloadResult = async (filename: string) => {
    try {
      const blob = await workflowApi.downloadFile(filename)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('File downloaded successfully')
    } catch (error: any) {
      console.error('Failed to download file:', error)
      toast.error('Failed to download file')
    }
  }

  const renderDataPreview = (data: any) => {
    if (!data) return null

    if (viewMode === 'json') {
      return (
        <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto text-sm font-mono">
          {JSON.stringify(data, null, 2)}
        </pre>
      )
    }

    // Try to render as table if it's an array of objects
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      const columns = Object.keys(data[0])
      const maxRows = 10 // Limit preview to 10 rows

      return (
        <div className="overflow-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.slice(0, maxRows).map((row: any, index: number) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  {columns.map((column) => (
                    <td key={column} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {String(row[column] || '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.length > maxRows && (
            <div className="text-center py-4 text-sm text-gray-500">
              Showing {maxRows} of {data.length} rows
            </div>
          )}
        </div>
      )
    }

    // Fallback to JSON view
    return (
      <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-sm">
        {JSON.stringify(data, null, 2)}
      </pre>
    )
  }

  if (!jobId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <ChartBarIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Job Selected
          </h3>
          <p className="text-gray-500">
            Select a completed job to view its results
          </p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading results...</p>
        </div>
      </div>
    )
  }

  if (!jobResults || jobDetails?.status !== 'completed') {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <ChartBarIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Results Available
          </h3>
          <p className="text-gray-500">
            {jobDetails?.status === 'running' 
              ? 'Job is still running. Results will appear when completed.'
              : 'This job has no results to display.'
            }
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex">
      {/* Results List */}
      <div className="w-1/3 bg-white border-r border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Results</h2>
          <div className="text-sm text-gray-500">
            Job {jobId?.substring(0, 8)} • {jobResults.total_blocks} blocks
          </div>
        </div>

        <div className="overflow-y-auto max-h-[calc(100vh-200px)]">
          {/* Final Output */}
          {jobResults.final_output_path && (
            <div className="p-4 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">Final Output</div>
                  <div className="text-sm text-gray-500 font-mono">
                    {jobResults.final_output_path?.split('/').pop()}
                  </div>
                </div>
                <button
                  onClick={() => jobResults.final_output_path && handleDownloadResult(jobResults.final_output_path.split('/').pop() || '')}
                  className="p-2 text-gray-400 hover:text-gray-600"
                  title="Download file"
                >
                  <DocumentArrowDownIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Block Results */}
          {jobResults.results.map((result: any, index: number) => (
            <div
              key={index}
              onClick={() => setSelectedResult(result)}
              className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                selectedResult === result ? 'bg-primary-50 border-primary-200' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium text-gray-900">
                  {result.block_type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                </div>
                <div className={`w-3 h-3 rounded-full ${
                  result.success ? 'bg-green-400' : 'bg-red-400'
                }`} />
              </div>
              
              <div className="text-sm text-gray-600">
                <div>Block: {result.block_id.substring(0, 8)}</div>
                <div>Duration: {result.execution_time.toFixed(2)}s</div>
                {result.success && (
                  <div>
                    {result.rows_processed} → {result.rows_output} rows
                  </div>
                )}
              </div>

              {result.data && (
                <div className="mt-2 flex items-center text-xs text-primary-600">
                  <EyeIcon className="w-3 h-3 mr-1" />
                  View data
                </div>
              )}
            </div>
          ))}

          {jobResults.results.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              <ChartBarIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Block Results</h3>
              <p>This job completed without detailed block results</p>
            </div>
          )}
        </div>
      </div>

      {/* Result Details */}
      <div className="flex-1 bg-gray-50">
        {selectedResult ? (
          <div className="h-full overflow-y-auto">
            {/* Result Header */}
            <div className="bg-white border-b border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <h3 className="text-xl font-semibold text-gray-900">
                    {selectedResult.block_type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())} Result
                  </h3>
                  <div className={`ml-3 w-3 h-3 rounded-full ${
                    selectedResult.success ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setViewMode('table')}
                    className={`p-2 rounded ${
                      viewMode === 'table' 
                        ? 'bg-primary-100 text-primary-600' 
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
                    title="Table view"
                  >
                    <TableCellsIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('json')}
                    className={`p-2 rounded ${
                      viewMode === 'json' 
                        ? 'bg-primary-100 text-primary-600' 
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
                    title="JSON view"
                  >
                    <ChartBarIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Block ID:</span>
                  <span className="ml-2 text-gray-900 font-mono">
                    {selectedResult.block_id.substring(0, 8)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Execution Time:</span>
                  <span className="ml-2 text-gray-900">
                    {selectedResult.execution_time.toFixed(2)}s
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Rows Processed:</span>
                  <span className="ml-2 text-gray-900">
                    {selectedResult.rows_processed}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Rows Output:</span>
                  <span className="ml-2 text-gray-900">
                    {selectedResult.rows_output}
                  </span>
                </div>
              </div>
            </div>

            {/* Result Content */}
            <div className="p-6">
              {selectedResult.success ? (
                <>
                  {selectedResult.data && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-4">Data Output</h4>
                      {renderDataPreview(selectedResult.data)}
                    </div>
                  )}
                  
                  {!selectedResult.data && (
                    <div className="text-center py-8 text-gray-500">
                      <ChartBarIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>No data output available for this block</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <h4 className="text-lg font-medium text-red-600 mb-2">Execution Error</h4>
                  <div className="bg-red-100 rounded-md p-4">
                    <div className="text-sm text-red-700 font-mono">
                      {selectedResult.error}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <EyeIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a Result
              </h3>
              <p className="text-gray-500">
                Choose a block result from the list to view its details
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
