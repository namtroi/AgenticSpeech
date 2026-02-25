import { useState, useCallback, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import type { SpeechChunk, AlignedWord } from '../types/database'

export function useChunkReview() {
  const [currentChunk, setCurrentChunk] = useState<SpeechChunk | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchNextPending = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const { data, error: sbError } = await supabase
        .from('speech_chunks')
        .select('*')
        .eq('status', 'pending_review')
        .limit(1)
        .single() // We intentionally expect single rows

      if (sbError) {
        // PostgREST returns PGRST116 when no rows match `.single()`
        if (sbError.code === 'PGRST116') {
          setCurrentChunk(null) // Queue empty!
          return
        }
        throw new Error(sbError.message)
      }

      setCurrentChunk(data as SpeechChunk)
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg || "Failed to fetch pending chunk.");
      setCurrentChunk(null);
    } finally {
      setLoading(false)
    }
  }, [])

  // Mount effect to fetch immediately
  useEffect(() => {
    fetchNextPending()
  }, [fetchNextPending])

  const approve = async () => {
    if (!currentChunk) return
    setLoading(true)
    
    try {
      // Intentionally omit updating JSONB boundaries here; boundaries
      // save happens prior to approve.
      const { error: sbError } = await supabase
        .from('speech_chunks')
        .update({ status: 'approved' })
        .eq('id', currentChunk.id)

      if (sbError) throw new Error(sbError.message)
      
      // Load next immediately
      await fetchNextPending()
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      setLoading(false);
    }
  }

  const reject = async () => {
    if (!currentChunk) return
    setLoading(true)
    
    try {
      const { error: sbError } = await supabase
        .from('speech_chunks')
        .update({ status: 'rejected' })
        .eq('id', currentChunk.id)

      if (sbError) throw new Error(sbError.message)
      
      await fetchNextPending()
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      setLoading(false);
    }
  }

  const updateTimestamps = async (newWords: AlignedWord[]) => {
    if (!currentChunk) return
    
    // We update our local cache immediately for fast perceived TTFB
    const updatedJSONB = {
      ...currentChunk.aligned_text_with_timestamps,
      aligned_words: newWords
    }
    
    setCurrentChunk({
      ...currentChunk,
      aligned_text_with_timestamps: updatedJSONB
    })

    try {
      const { error: sbError } = await supabase
        .from('speech_chunks')
        .update({ aligned_text_with_timestamps: updatedJSONB })
        .eq('id', currentChunk.id)
        
      if (sbError) throw new Error(sbError.message)
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
    }
  }

  return {
    currentChunk,
    loading,
    error,
    approve,
    reject,
    updateTimestamps
  }
}
