import React, { useEffect, useRef } from "react";
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import type { SpeechChunk, AlignedWord } from '../types/database'

interface WaveformPlayerProps {
  chunk: SpeechChunk
  onRegionsChange: (updatedWords: AlignedWord[]) => void
}

export const WaveformPlayer: React.FC<WaveformPlayerProps> = ({
  chunk,
  onRegionsChange
}) => {
  const waveformRef = useRef<HTMLDivElement>(null)
  const wavesurferRef = useRef<WaveSurfer | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const regionsRef = useRef<any>(null);
  
  // Keep local sync so drag events don't lag React state loops
  const localWordsRef = useRef<AlignedWord[]>([])

  // Hard mount logic
  useEffect(() => {
    if (!waveformRef.current) return

    // 1. Initialize empty wavesurfer
    const ws = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: 'rgb(200, 200, 200)',
      progressColor: 'rgb(100, 100, 100)',
      cursorColor: 'rgb(0, 0, 0)',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 128,
      normalize: true,
      minPxPerSec: 100,
    })
    
    // 2. Register Regions Plugin
    const wsRegions = ws.registerPlugin(RegionsPlugin.create())
    regionsRef.current = wsRegions

    // 3. Load Audio Stream
    ws.load(chunk.audio_url)

    // Wait until audio buffer finishes decoding before painting word boxes
    ws.on('ready', () => {
      wsRegions.clearRegions()
      localWordsRef.current = [...chunk.aligned_text_with_timestamps.aligned_words]

      localWordsRef.current.forEach((word, index) => {
        // Exclude completely broken chunks
        if (word.end <= word.start) return

        wsRegions.addRegion({
          start: word.start,
          end: word.end,
          content: word.word,
          color: 'rgba(59, 130, 246, 0.2)', // Tailwind blue-500 @ 20%
          drag: true,
          resize: true,
          id: index.toString()
        })
      })
    })

    // Listen to Region edge dragging and sync back upstream
    wsRegions.on('region-updated', (region) => {
      const idx = parseInt(region.id)
      if (isNaN(idx)) return

      const updatedLocal = [...localWordsRef.current]
      updatedLocal[idx] = {
        ...updatedLocal[idx],
        start: region.start,
        end: region.end,
      }
      
      localWordsRef.current = updatedLocal
      onRegionsChange(updatedLocal)
    })

    wavesurferRef.current = ws

    return () => {
      ws.destroy()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chunk.audio_url]); // Re-mount the wavesurfer only when chunk underlying audio swaps

  // Listen for spacebar to play/pause at the global window layer
  // (Prevents needing to click the explicit canvas repeatedly)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault() // prevent page scrolling down
        wavesurferRef.current?.playPause()
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className="w-full flex flex-col space-y-4">
      {/* Audio Visualization Box */}
      <div 
        className="w-full bg-white border rounded-lg shadow-sm p-4 h-[200px] flex items-center justify-center overflow-hidden"
      >
        <div ref={waveformRef} className="w-full" />
      </div>
      
      {/* Transcription Reference Panel */}
      <div className="bg-white border rounded-lg shadow-sm p-4 w-full">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
          Original Reference Text
        </h3>
        <p className="text-gray-900 text-lg leading-relaxed bg-gray-50 p-3 rounded border">
          {chunk.original_text}
        </p>
      </div>
      
      <div className="bg-white border rounded-lg shadow-sm p-4 w-full">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
          Whisper Transcribed Text
        </h3>
        <p className="text-gray-900 text-lg leading-relaxed bg-blue-50/50 p-3 rounded border border-blue-100">
          {chunk.aligned_text_with_timestamps.transcribed_text}
        </p>
      </div>
    </div>
  )
}
