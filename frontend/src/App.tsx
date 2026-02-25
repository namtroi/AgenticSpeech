function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header Area */}
      <header className="bg-white shadow-sm border-b px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">
            Agentic Speech — HITL Review
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-500">
              0 chunks pending
            </span>
          </div>
        </div>
      </header>

      {/* Main Review Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">
            System is initializing. Waiting for audio chunks...
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
