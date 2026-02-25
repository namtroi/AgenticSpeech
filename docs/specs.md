## System Architecture: Agentic Speech Dataset Engineering Pipeline

**Project Objective:** Build an automated, high-throughput data pipeline to process raw speech datasets into high-fidelity, word-level aligned audio chunks. The system utilizes an agentic workflow for processing and features a React-based Human-in-the-Loop (HITL) interface for final rapid validation.

### 1. Data Ingestion Layer (Python)

- **Target Dataset:** Use `parler-tts/libritts_r` on the Hugging Face Hub (This is the "restored" version of LibriTTS, representing the absolute gold standard for high-fidelity, studio-quality English speech data).
- **Implementation:** Use the Hugging Face `datasets` library.
- **Requirement:** Set `streaming=True` to fetch audio arrays and reference text iteratively into memory without downloading the entire massive dataset to local disk.

### 2. Processing & Alignment Layer (Python)

- **Voice Activity Detection (VAD):** Use `silero-vad` (PyTorch). It is the fastest and most accurate open-source VAD. Use it to strip absolute silence and split the audio stream into 5 to 15-second chunks.
- **ASR & Word Alignment:** Use `vosk`.
- Pass the VAD chunks through Vosk to generate transcriptions.
- Use its built-in word details to extract exact word-level timestamps (start and end times in seconds as floats).

- **Automated Quality Gate (AI-as-a-Judge):** Use the `jiwer` Python library to calculate the Word Error Rate (WER) by comparing the Vosk output against the original LibriTTS-R text.
- Rule: If WER > 15%, automatically discard the chunk to save human review time.

### 3. Orchestration & Database Layer

- **Workflow Orchestrator:** Use `langgraph` to construct the entire Python pipeline as a stateful, compiled graph.
- Define nodes for the workflow: `fetch_huggingface_stream` -> `process_silero_vad` -> `transcribe_vosk` -> `evaluate_wer` -> `insert_to_db`.

- **Database & Backend:** Use `supabase` (PostgreSQL) via the `supabase-py` client.
- Store metadata in a `speech_chunks` table containing: `id` (UUID), `dataset_id`, `audio_url` (upload audio chunks to Supabase Storage), `original_text`, `aligned_text_with_timestamps` (JSONB format), `wer_score` (Float), and `status` (Enum: 'pending_review', 'approved', 'rejected').

### 4. Human-in-the-Loop (HITL) Validation UI (React)

- **Framework:** Use `React` (via Vite) with `TailwindCSS`, integrated with the `@supabase/supabase-js` client.
- **Core Audio Component:** Use `wavesurfer.js` (version 7+) along with its `Regions` plugin.
- **Workflow & Interactions:**

1. UI fetches exactly one row from the `speech_chunks` table where `status = 'pending_review'`.
2. `wavesurfer.js` renders the waveform and dynamically draws bounding boxes (regions) over the audio using the JSONB timestamp data.
3. **Keyboard-first Controls:**

- **Spacebar:** Play/Pause.
- **Enter:** Triggers an API call to update the Supabase row status to `approved`, then automatically loads the next pending chunk.
- **Delete:** Triggers an API call to update the Supabase row status to `rejected`, then automatically loads the next pending chunk.

4. **Mouse Editing:** If a timestamp is slightly off, the reviewer can drag the region edges to adjust it, or edit the text inside the region, then press Enter to save.
