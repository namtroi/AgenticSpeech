# Database & Storage Schema Contract

## 1. PostgreSQL Schema (Supabase)

### Table: `speech_chunks`

Source of truth for pipeline state and metadata. Drives HITL UI via Supabase JS client.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `uuid_generate_v4()` | Unique chunk identifier. |
| `dataset_id` | `text` | NOT NULL | Source dataset (e.g., `parler-tts/libritts_r`). |
| `audio_url` | `text` | NOT NULL | Public URL to `.wav` file in Supabase Storage. |
| `original_text` | `text` | NOT NULL | Ground truth text from source dataset. |
| `aligned_text_with_timestamps`| `jsonb` | NOT NULL | WhisperX alignment output (see format below). |
| `wer_score` | `real` (Float)| NOT NULL | Word Error Rate computed by `jiwer` (0.0 to 1.0). |
| `status` | `chunk_status` | DEFAULT `'pending_review'` | Enum state. |
| `created_at` | `timestamptz` | DEFAULT `now()` | Record creation time (Python ingest). |
| `updated_at` | `timestamptz` | DEFAULT `now()` | Last modification time (UI review). |

### Enum: `chunk_status`
```sql
CREATE TYPE chunk_status AS ENUM (
  'pending_review', -- Awaiting human validation in HITL UI
  'approved',       -- Human validated and saved
  'rejected'        -- Human marked as unusable/bad alignment
);
```

---

## 2. JSONB Structure: `aligned_text_with_timestamps`

**Contract:** Array of word objects. Used by Next.js/Wavesurfer.js to map bounding boxes (Regions) overlaying the audio waveform.

```json
[
  {
    "word": "The",       // Extracted word text
    "start": 0.150,      // Start time in seconds (float)
    "end": 0.320,        // End time in seconds (float)
    "confidence": 0.99   // WhisperX confidence score (0.0 - 1.0)
  },
  {
    "word": "quick",
    "start": 0.330,
    "end": 0.650,
    "confidence": 0.82
  }
]
```
*Note: UI will allow dragging region edges to modify `start`/`end` values, or text input to fix `word`, then reserialize to this JSON array on save.*

---

## 3. Object Storage Contract (Supabase Storage)

**Bucket Name:** `audio_chunks`
**Access:** Public Read (required for Wavesurfer.js to fetch via URL), Authenticated Write (Python backend).

**File Naming Convention:**
`{dataset_id}/{uuid}.wav`

**Example Path:**
`parler-tts-libritts_r/123e4567-e89b-12d3-a456-426614174000.wav`

**Workflow:**
1. Python generates 5-15s audio slice in memory.
2. Python uploads to `audio_chunks` bucket.
3. Python gets public URL.
4. Python inserts row into `speech_chunks` table with the generated `audio_url`.
