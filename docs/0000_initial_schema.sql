-- Initial Schema for Agentic Speech
-- Run this in the Supabase SQL Editor

-- Create Enum
CREATE TYPE chunk_status AS ENUM (
  'pending_review',
  'approved',
  'rejected'
);

-- Create Table
CREATE TABLE speech_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_id text NOT NULL,
  speaker_id text NULL,
  audio_url text NOT NULL,
  original_text text NOT NULL,
  aligned_text_with_timestamps jsonb NOT NULL,
  wer_score real NOT NULL,
  duration real NOT NULL,
  status chunk_status DEFAULT 'pending_review',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create Indexes
CREATE INDEX idx_speech_chunks_status ON speech_chunks (status);
CREATE INDEX idx_speech_chunks_speaker_id ON speech_chunks (speaker_id);

-- Create Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_updated_at
  BEFORE UPDATE ON speech_chunks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Configure RLS
ALTER TABLE speech_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read of pending chunks"
  ON speech_chunks FOR SELECT
  USING (true);

CREATE POLICY "Allow public update for review actions"
  ON speech_chunks FOR UPDATE
  USING (true)
  WITH CHECK (status IN ('approved', 'rejected'));

CREATE POLICY "Allow service_role insert"
  ON speech_chunks FOR INSERT
  WITH CHECK (true);
