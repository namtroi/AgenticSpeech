import React from 'react'
import type { SpeechChunk } from '../types/database'
import { Check, X, Clock, Database, User, Activity } from 'lucide-react'

interface ReviewControlsProps {
  chunk: SpeechChunk
  onApprove: () => void
  onReject: () => void
  loading: boolean
}

export const ReviewControls: React.FC<ReviewControlsProps> = ({
  chunk,
  onApprove,
  onReject,
  loading
}) => {
  // Format the WER percent cleanly
  const werPercent = (chunk.wer_score * 100).toFixed(1)
  
  // Decide the WER color indicator. Below 15% is passing initially.
  const werColor = chunk.wer_score > 0.15 ? 'text-red-500' : 'text-green-500'

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 w-full max-w-sm flex flex-col h-full space-y-6">
      
      {/* Header Info */}
      <div className="border-b pb-4">
        <h2 className="text-lg font-semibold text-gray-800 break-all mb-1">
          {chunk.id}
        </h2>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          {chunk.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Metadata Statistics List */}
      <div className="space-y-4 flex-1">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center text-gray-500">
            <Activity className="w-4 h-4 mr-2" />
            WER Score
          </div>
          <span className={`font-mono font-medium ${werColor}`}>
            {werPercent}%
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center text-gray-500">
            <Clock className="w-4 h-4 mr-2" />
            Duration
          </div>
          <span className="font-mono text-gray-700">
            {chunk.duration.toFixed(2)}s
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center text-gray-500">
            <Database className="w-4 h-4 mr-2" />
            Dataset ID
          </div>
          <span className="font-mono text-gray-700 truncate ml-2">
            {chunk.dataset_id}
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center text-gray-500">
            <User className="w-4 h-4 mr-2" />
            Speaker ID
          </div>
          <span className="font-mono text-gray-700 truncate ml-2">
            {chunk.speaker_id}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-4 border-t">
        <button
          onClick={onReject}
          disabled={loading}
          className="flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <X className="w-4 h-4 mr-1.5" />
          Reject
        </button>
        
        <button
          onClick={onApprove}
          disabled={loading}
          className="flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Check className="w-4 h-4 mr-1.5" />
          Approve
        </button>
      </div>
      
      {/* Keyboard Hint */}
      <div className="text-center text-xs text-gray-400 mt-2">
        <p>Press <kbd className="font-mono bg-gray-100 rounded px-1">Enter</kbd> to Appr. <kbd className="font-mono bg-gray-100 rounded px-1">Del</kbd> to Rej.</p>
      </div>

    </div>
  )
}
