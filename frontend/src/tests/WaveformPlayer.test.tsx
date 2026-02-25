import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WaveformPlayer } from '../components/WaveformPlayer'
import type { SpeechChunk } from '../types/database'

// Mock the heavy wavesurfer library objects entirely so it doesnt blow up our JS Dom
const mockAddRegion = vi.fn()
const mockOn = vi.fn()
const mockDestroy = vi.fn()
const mockLoad = vi.fn()

vi.mock('wavesurfer.js', () => {
  return {
    default: {
      create: vi.fn(() => ({
        load: mockLoad,
        on: mockOn,
        destroy: mockDestroy,
        registerPlugin: vi.fn(() => ({
          addRegion: mockAddRegion,
          on: vi.fn(),
          clearRegions: vi.fn(),
        })),
      }))
    }
  }
})

// Mock out the Regions plugin since it attaches differently
vi.mock('wavesurfer.js/dist/plugins/regions.esm.js', () => {
  return {
    default: {
      create: vi.fn(() => ({}))
    }
  }
})

describe('WaveformPlayer', () => {
  const mockChunk: SpeechChunk = {
    id: '123',
    status: 'pending_review',
    dataset_id: 'test',
    speaker_id: 'test',
    wer_score: 0.1,
    audio_url: 'http://example.com/audio.wav',
    original_text: 'hello world',
    duration: 5.5,
    aligned_text_with_timestamps: {
      transcribed_text: 'hello world',
      aligned_words: [
        { word: 'hello', start: 0.0, end: 0.5, confidence: 0.99 },
        { word: 'world', start: 0.6, end: 1.0, confidence: 0.99 }
      ]
    },
    created_at: new Date().toISOString()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Simulate `wavesurfer.on('ready')` firing synchronously for tests
    mockOn.mockImplementation((event: string, callback: () => void) => {
      if (event === 'ready') {
        callback()
      }
    })
  })

  it('mounts the container and draws aligned word regions', () => {
    render(
      <WaveformPlayer 
        chunk={mockChunk} 
        onRegionsChange={vi.fn()} 
      />
    )
    
    // Expect the original text UI block to render natively
    const textNodes = screen.getAllByText('hello world')
    expect(textNodes).toHaveLength(2)
    
    // Expect wavesurfer.load to be called with the object storage URL
    expect(mockLoad).toHaveBeenCalledWith('http://example.com/audio.wav')
    
    // Expect the two word regions to be painted
    expect(mockAddRegion).toHaveBeenCalledTimes(2)
  })
})
