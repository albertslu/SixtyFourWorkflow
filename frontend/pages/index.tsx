import { useState } from 'react'
import Head from 'next/head'
import WorkflowBuilder from '../src/components/WorkflowBuilder'
import JobMonitor from '../src/components/JobMonitor'
import ResultsPanel from '../src/components/ResultsPanel'
import { PlusIcon, PlayIcon, StopIcon } from '@heroicons/react/24/outline'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'builder' | 'jobs' | 'results'>('builder')
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  return (
    <>
      <Head>
        <title>SixtyFour Workflow Engine</title>
        <meta name="description" content="Build and execute data workflows with drag-and-drop interface" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-14">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-xl font-bold text-gray-900">
                    SixtyFour Workflow Engine
                  </h1>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setActiveTab('builder')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      activeTab === 'builder'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <PlusIcon className="w-4 h-4 inline mr-2" />
                    Builder
                  </button>
                  <button
                    onClick={() => setActiveTab('jobs')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      activeTab === 'jobs'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <PlayIcon className="w-4 h-4 inline mr-2" />
                    Jobs
                  </button>
                  <button
                    onClick={() => setActiveTab('results')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      activeTab === 'results'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <StopIcon className="w-4 h-4 inline mr-2" />
                    Results
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          {activeTab === 'builder' && (
            <WorkflowBuilder onJobCreated={setCurrentJobId} />
          )}
          
          {activeTab === 'jobs' && (
            <div className="h-full p-4">
              <JobMonitor 
                currentJobId={currentJobId}
                onJobSelect={setCurrentJobId}
              />
            </div>
          )}
          
          {activeTab === 'results' && (
            <div className="h-full p-4">
              <ResultsPanel jobId={currentJobId} />
            </div>
          )}
        </main>
      </div>
    </>
  )
}
