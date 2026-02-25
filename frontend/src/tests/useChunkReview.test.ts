import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useChunkReview } from '../hooks/useChunkReview'

// Mock the Supabase client entirely to eliminate network dependencies
const mockSelect = vi.fn()
const mockUpdate = vi.fn()
const mockEq = vi.fn()
const mockLimit = vi.fn()
const mockSingle = vi.fn()

vi.mock('../lib/supabase', () => {
  return {
    supabase: {
      from: vi.fn(() => ({
        select: mockSelect,
        update: mockUpdate
      }))
    }
  }
})

// Establish the Mock Chain returns
mockSelect.mockReturnValue({
  eq: mockEq
})

mockUpdate.mockReturnValue({
  eq: mockEq
})

mockEq.mockReturnValue({
  limit: mockLimit,
  // Add support for update().eq() chaining
  select: vi.fn().mockReturnValue({ single: mockSingle })
})

mockLimit.mockReturnValue({
  single: mockSingle
})

describe('useChunkReview', () => {
  const mockChunk = {
    id: '123-abc',
    status: 'pending_review',
    dataset_id: 'test_ds',
    speaker_id: 'speaker_1',
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
  })

  it('fetches a pending chunk on mount', async () => {
    mockSingle.mockResolvedValue({ data: mockChunk, error: null })
    
    const { result } = renderHook(() => useChunkReview())
    
    // Assert initial loading space
    expect(result.current.loading).toBe(true)
    
    // Wait for the async effect to resolve
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0))
    })
    
    expect(result.current.loading).toBe(false)
    expect(result.current.currentChunk).toEqual(mockChunk)
    expect(mockSelect).toHaveBeenCalledWith('*')
    expect(mockEq).toHaveBeenCalledWith('status', 'pending_review')
  })

  it('handles approve mutation and fetches next', async () => {
    mockSingle.mockResolvedValueOnce({ data: mockChunk, error: null }) // Initial fetch
    
    const { result } = renderHook(() => useChunkReview())
    
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0))
    })

    // Setup mock for the update call
    mockEq.mockResolvedValueOnce({ error: null })
    // Setup mock for the subsequent fetch
    mockSingle.mockResolvedValueOnce({ data: null, error: null })

    await act(async () => {
      await result.current.approve()
    })

    expect(mockUpdate).toHaveBeenCalledWith({
      status: 'approved',
      aligned_text_with_timestamps: mockChunk.aligned_text_with_timestamps
    })
    // Assert 2 calls to select (1 initial, 1 after approve)
    expect(mockSelect).toHaveBeenCalledTimes(2)
  })

  it('handles reject mutation and fetches next', async () => {
    mockSingle.mockResolvedValueOnce({ data: mockChunk, error: null })
    
    const { result } = renderHook(() => useChunkReview())
    
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0))
    })

    mockEq.mockResolvedValueOnce({ error: null })
    mockSingle.mockResolvedValueOnce({ data: null, error: null })

    await act(async () => {
      await result.current.reject()
    })

    expect(mockUpdate).toHaveBeenCalledWith({ status: 'rejected' })
    expect(mockSelect).toHaveBeenCalledTimes(2)
  })
})
