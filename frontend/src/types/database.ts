// Represents an individual aligned word with confidence and timestamps
export interface AlignedWord {
  word: string;
  start: number;
  end: number;
  confidence: number;
}

// Represents the schema of the `aligned_text_with_timestamps` column
export interface AlignedTextWithTimestamps {
  transcribed_text: string;
  aligned_words: AlignedWord[];
}

// Represents the overarching DB Model matching Supabase Row
export interface SpeechChunk {
  id: string; // UUID
  dataset_id: string;
  speaker_id: string;
  audio_url: string;
  original_text: string;
  aligned_text_with_timestamps: AlignedTextWithTimestamps;
  wer_score: number;
  duration: number;
  status: 'pending_review' | 'approved' | 'rejected';
  created_at: string;
}
