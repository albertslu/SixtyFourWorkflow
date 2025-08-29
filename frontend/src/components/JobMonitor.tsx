import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  PlayIcon, 
  PauseIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { jobsApi } from '../lib/api'
import { Job, JobStatus } from '../types/workflow'
import { toast } from 'react-hot-toast'

interface JobMonitorProps {
  currentJobId: string | null
  onJobSelect: (jobId: string) => void
}

const STATUS_COLORS: Record<JobStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-800'
}

const STATUS_ICONS: Record<JobStatus, React.ReactNode> = {
  pending: <ClockIcon className="w-4 h-4" />,
  running: <ArrowPathIcon className="w-4 h-4 animate-spin" />,
  completed: <CheckCircleIcon className="w-4 h-4" />,
  failed: <XCircleIcon className="w-4 h-4" />,
  cancelled: <PauseIcon className="w-4 h-4" />
}

export default function JobMonitor({ currentJobId, onJobSelect }: JobMonitorProps) {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch all jobs
  const { data: jobsData, refetch: refetchJobs } = useQuery(
    'jobs',
    () => jobsApi.getJobs(),
    {
      refetchInterval: autoRefresh ? 2000 : false, // Refresh every 2 seconds if auto-refresh is on
      onError: (error: any) => {
        console.error('Failed to fetch jobs:', error)
        toast.error('Failed to fetch jobs')
      }
    }
  )

  // Fetch job progress for selected job
  const { data: jobProgress } = useQuery(
    ['job-progress', selectedJob?.job_id],
    () => selectedJob ? jobsApi.getJobProgress(selectedJob.job_id) : null,
    {
      enabled: !!selectedJob && selectedJob.status === 'running',
      refetchInterval: selectedJob?.status === 'running' ? 1000 : false, // Refresh every second for running jobs
      onError: (error: any) => {
        console.error('Failed to fetch job progress:', error)
      }
    }
  )

  // Fetch job results for completed jobs
  const { data: jobResults } = useQuery(
    ['job-results', selectedJob?.job_id],
    () => selectedJob ? jobsApi.getJobResults(selectedJob.job_id) : null,
    {
      enabled: !!selectedJob && ['completed', 'failed'].includes(selectedJob.status),
      onError: (error: any) => {
        console.error('Failed to fetch job results:', error)
      }
    }
  )

  // Auto-select current job if provided
  useEffect(() => {
    if (currentJobId && jobsData?.jobs) {
      const job = jobsData.jobs.find(j => j.job_id === currentJobId)
      if (job) {
        setSelectedJob(job)
      }
    }
  }, [currentJobId, jobsData])

  const handleJobSelect = (job: Job) => {
    setSelectedJob(job)
    onJobSelect(job.job_id)
  }

  const handleCancelJob = async (jobId: string) => {
    try {
      await jobsApi.cancelJob(jobId)
      toast.success('Job cancelled successfully')
      refetchJobs()
    } catch (error: any) {
      console.error('Failed to cancel job:', error)
      toast.error('Failed to cancel job')
    }
  }

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime)
    const end = endTime ? new Date(endTime) : new Date()
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000)
    
    if (duration < 60) return `${duration}s`
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`
  }

  return (
    <div className="h-full flex">
      {/* Jobs List */}
      <div className="w-1/3 bg-white border-r border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Jobs</h2>
            <div className="flex items-center space-x-2">
              <label className="flex items-center text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="mr-2"
                />
                Auto-refresh
              </label>
              <button
                onClick={() => refetchJobs()}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <ArrowPathIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div className="text-sm text-gray-500">
            Total: {jobsData?.total || 0} jobs
          </div>
        </div>

        <div className="overflow-y-auto max-h-[calc(100vh-200px)]">
          {jobsData?.jobs.map((job) => (
            <div
              key={job.job_id}
              onClick={() => handleJobSelect(job)}
              className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                selectedJob?.job_id === job.job_id ? 'bg-primary-50 border-primary-200' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  {STATUS_ICONS[job.status]}
                  <span className="ml-2 font-medium text-gray-900 truncate">
                    Job {job.job_id.substring(0, 8)}
                  </span>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${STATUS_COLORS[job.status]}`}>
                  {job.status}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                <div>Created: {new Date(job.created_at).toLocaleString()}</div>
                {job.started_at && (
                  <div>
                    Duration: {formatDuration(job.started_at, job.completed_at)}
                  </div>
                )}
              </div>

              {job.status === 'running' && job.progress && (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Progress</span>
                    <span>{job.progress.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress.percentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ))}

          {(!jobsData?.jobs || jobsData.jobs.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              <PlayIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Jobs Yet</h3>
              <p>Execute a workflow to see jobs here</p>
            </div>
          )}
        </div>
      </div>

      {/* Job Details */}
      <div className="flex-1 bg-gray-50">
        {selectedJob ? (
          <div className="h-full overflow-y-auto">
            {/* Job Header */}
            <div className="bg-white border-b border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  {STATUS_ICONS[selectedJob.status]}
                  <h3 className="ml-2 text-xl font-semibold text-gray-900">
                    Job {selectedJob.job_id.substring(0, 8)}
                  </h3>
                  <span className={`ml-3 px-3 py-1 text-sm font-medium rounded-full ${STATUS_COLORS[selectedJob.status]}`}>
                    {selectedJob.status}
                  </span>
                </div>
                
                {selectedJob.status === 'running' && (
                  <button
                    onClick={() => handleCancelJob(selectedJob.job_id)}
                    className="btn-secondary text-red-600 hover:text-red-700"
                  >
                    Cancel Job
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Created:</span>
                  <span className="ml-2 text-gray-900">
                    {new Date(selectedJob.created_at).toLocaleString()}
                  </span>
                </div>
                {selectedJob.started_at && (
                  <div>
                    <span className="text-gray-500">Started:</span>
                    <span className="ml-2 text-gray-900">
                      {new Date(selectedJob.started_at).toLocaleString()}
                    </span>
                  </div>
                )}
                {selectedJob.completed_at && (
                  <div>
                    <span className="text-gray-500">Completed:</span>
                    <span className="ml-2 text-gray-900">
                      {new Date(selectedJob.completed_at).toLocaleString()}
                    </span>
                  </div>
                )}
                {selectedJob.started_at && (
                  <div>
                    <span className="text-gray-500">Duration:</span>
                    <span className="ml-2 text-gray-900">
                      {formatDuration(selectedJob.started_at, selectedJob.completed_at)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Job Progress */}
            {selectedJob.status === 'running' && jobProgress && (
              <div className="bg-white border-b border-gray-200 p-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Progress</h4>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                      <span>Overall Progress</span>
                      <span>{jobProgress.percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${jobProgress.percentage}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Current Step:</span>
                      <span className="ml-2 text-gray-900">
                        {jobProgress.current_step} of {jobProgress.total_steps}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Processed Rows:</span>
                      <span className="ml-2 text-gray-900">
                        {jobProgress.processed_rows} of {jobProgress.total_rows}
                      </span>
                    </div>
                  </div>

                  {jobProgress.current_block_name && (
                    <div className="bg-blue-50 p-3 rounded-md">
                      <div className="text-sm font-medium text-blue-900">
                        Currently executing: {jobProgress.current_block_name}
                      </div>
                      <div className="text-sm text-blue-700 mt-1">
                        {jobProgress.message}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Job Results */}
            {['completed', 'failed'].includes(selectedJob.status) && jobResults && (
              <div className="bg-white p-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Results</h4>
                
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {jobResults.successful_blocks}
                    </div>
                    <div className="text-sm text-green-700">Successful Blocks</div>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">
                      {jobResults.failed_blocks}
                    </div>
                    <div className="text-sm text-red-700">Failed Blocks</div>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {jobResults.total_blocks}
                    </div>
                    <div className="text-sm text-blue-700">Total Blocks</div>
                  </div>
                </div>

                {jobResults.final_output_path && (
                  <div className="bg-gray-50 p-4 rounded-lg mb-4">
                    <div className="text-sm font-medium text-gray-700">Final Output:</div>
                    <div className="text-sm text-gray-600 font-mono">
                      {jobResults.final_output_path}
                    </div>
                  </div>
                )}

                {/* Block Results */}
                <div className="space-y-3">
                  {jobResults.results.map((result: any, index: number) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border ${
                        result.success 
                          ? 'bg-green-50 border-green-200' 
                          : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium">
                          {result.block_type} - {result.block_id.substring(0, 8)}
                        </div>
                        <div className="text-sm text-gray-500">
                          {result.execution_time.toFixed(2)}s
                        </div>
                      </div>
                      
                      {result.success ? (
                        <div className="text-sm text-green-700">
                          Processed {result.rows_processed} rows → {result.rows_output} rows
                        </div>
                      ) : (
                        <div className="text-sm text-red-700">
                          Error: {result.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Error Message */}
            {selectedJob.error_message && (
              <div className="bg-white border-b border-gray-200 p-6">
                <h4 className="text-lg font-medium text-red-600 mb-2">Error</h4>
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <div className="text-sm text-red-700 font-mono">
                    {selectedJob.error_message}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <PlayIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a Job
              </h3>
              <p className="text-gray-500">
                Choose a job from the list to view its details and progress
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
