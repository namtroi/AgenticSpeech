import { useEffect } from 'react'
import { useChunkReview } from './hooks/useChunkReview'
import { WaveformPlayer } from './components/WaveformPlayer'
import { ReviewControls } from './components/ReviewControls'

function App() {
  const {
    currentChunk,
    loading,
    error,
    approve,
    reject,
    updateTimestamps
  } = useChunkReview()

  // Connect global keyboard listener for quick review routing
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts if user is currently typing in an input
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') {
        return
      }

      if (e.code === 'Enter') {
        e.preventDefault()
        if (currentChunk && !loading) approve()
      } else if (e.code === 'Delete' || e.code === 'Backspace') {
        e.preventDefault()
        if (currentChunk && !loading) reject()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentChunk, loading, approve, reject])

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm border-b px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">
            Agentic Speech — HITL Review
          </h1>
          <div className="flex items-center space-x-4">
            {error && <span className="text-sm font-medium text-red-500">{error}</span>}
            <span className="text-sm font-medium text-gray-500">
              {loading ? 'Processing...' : currentChunk ? '1 chunk active' : '0 chunks pending'}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col md:flex-row gap-6 relative">
        {!currentChunk && !loading && (
          <div className="absolute inset-0 flex items-center justify-center flex-col z-10">
            <p className="text-gray-500 text-lg">No audio chunks pending review.</p>
            <p className="text-gray-400 text-sm mt-2">Check back later once the backend ingress is populated.</p>
          </div>
        )}

        {/* Content Render Tree */}
        <div className={`flex-1 flex flex-col ${!currentChunk ? 'opacity-20 pointer-events-none filter blur-sm transition-all duration-300' : ''}`}>
          {currentChunk && (
            <WaveformPlayer 
              chunk={currentChunk} 
              onRegionsChange={updateTimestamps} 
            />
          )}
        </div>
        
        <div className={`w-full md:w-80 flex-shrink-0 ${!currentChunk ? 'opacity-20 pointer-events-none filter blur-sm transition-all duration-300' : ''}`}>
          {currentChunk && (
            <ReviewControls 
              chunk={currentChunk}
              onApprove={approve}
              onReject={reject}
              loading={loading}
            />
          )}
        </div>
      </main>
    </div>
  )
}

export default App
