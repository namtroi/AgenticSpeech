# Implementation Plan: Agentic Speech Pipeline

## Phase 0: Project Scaffold & Infra Setup

**Goal:** Monorepo skeleton, Docker, Supabase project, env config.

### Steps
1. Init monorepo structure:
   ```
   AgenticSpeech/
   ├── backend/          # Python pipeline
   │   ├── src/
   │   │   ├── nodes/    # LangGraph node functions
   │   │   ├── utils/    # Shared helpers (audio, db)
   │   │   └── graph.py  # LangGraph compiled graph
   │   ├── tests/
   │   ├── Dockerfile
   │   └── requirements.txt
   ├── frontend/         # React HITL UI
   │   ├── src/
   │   │   ├── components/
   │   │   ├── hooks/
   │   │   ├── lib/      # supabase client
   │   │   └── App.tsx
   │   ├── Dockerfile
   │   └── package.json
   ├── docker-compose.yml
   ├── .env.example
   └── docs/
   ```
2. Create Supabase project (free tier). Get `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` + `SUPABASE_ANON_KEY`.
3. Run DB migration: enum, table, indexes, trigger, RLS (from `database_schema.md`).
4. Create `audio_chunks` storage bucket. Set public read policy.
5. Write `.env.example` with all required vars.
6. Setup `docker-compose.yml` — backend service (GPU passthrough) + frontend service.

### Checklist
- [ ] Monorepo dirs created (`backend/`, `frontend/`, `docs/`)
- [ ] `requirements.txt` w/ pinned deps (datasets, silero-vad, whisperx, jiwer, langgraph, supabase)
- [ ] `package.json` w/ deps (react, vite, tailwindcss, wavesurfer.js, @supabase/supabase-js, vitest)
- [ ] Supabase project live, keys in `.env`
- [ ] DB migration executed — table, enum, indexes, trigger, RLS all applied
- [ ] `audio_chunks` bucket created, public read confirmed
- [ ] `docker-compose.yml` builds & runs both services
- [ ] `.env.example` committed (no real keys)

---

## Phase 1: Data Ingestion Node

**Goal:** Stream audio + text from HuggingFace. No disk download.

### Steps
1. `backend/src/nodes/fetch_hf.py` — use `datasets.load_dataset("parler-tts/libritts_r", streaming=True)`.
2. Yield dicts: `{ audio_array, sample_rate, original_text, dataset_id, speaker_id }`.
3. Write tests first (`backend/tests/test_fetch_hf.py`). Mock HF dataset, assert output shape.

### Checklist
- [ ] `test_fetch_hf.py` written & passing (mocked HF)
- [ ] `fetch_hf.py` streams data, yields correct dict shape
- [ ] `speaker_id` extracted from dataset metadata
- [ ] No local file downloads (streaming only)

---

## Phase 2: VAD Processing Node

**Goal:** Split raw audio into 5-15s voiced chunks via Silero VAD.

### Steps
1. `backend/src/nodes/process_vad.py` — load silero-vad model, run on audio tensor.
2. Merge/split VAD segments to enforce 5-15s range.
3. Return list of `{ chunk_array, start_time, end_time, duration, sample_rate }`.
4. TDD: `backend/tests/test_process_vad.py`. Feed dummy sine wave tensor, assert chunk durations in range.

### Checklist
- [ ] `test_process_vad.py` written & passing (dummy tensors)
- [ ] Silero VAD model loads correctly
- [ ] Chunks guaranteed 5-15s (merge short, split long)
- [ ] Silent regions stripped
- [ ] `duration` field computed per chunk

---

## Phase 3: WhisperX Alignment Node

**Goal:** Transcribe chunks, get word-level timestamps (seconds).

### Steps
1. `backend/src/nodes/align_whisperx.py` — load whisperx model, transcribe chunk, run alignment.
2. Output: `{ aligned_words: [{ word, start, end, confidence }], transcribed_text }`.
3. TDD: `backend/tests/test_align_whisperx.py`. Mock whisperx output, assert JSONB structure matches contract.

### Checklist
- [ ] `test_align_whisperx.py` written & passing (mocked whisperx)
- [ ] Transcription runs on chunk array
- [ ] Phoneme alignment returns word-level timestamps (seconds, float)
- [ ] Confidence scores included per word
- [ ] Output matches `aligned_text_with_timestamps` JSONB contract

---

## Phase 4: WER Quality Gate Node

**Goal:** Auto-discard bad chunks (WER > 15%).

### Steps
1. `backend/src/nodes/evaluate_wer.py` — use `jiwer.wer()` to compare `transcribed_text` vs `original_text`.
2. Return `{ wer_score, pass: bool }`. Pass = WER <= 0.15.
3. TDD: `backend/tests/test_evaluate_wer.py`. Test exact match (0.0), partial match, total mismatch (1.0), edge case at 0.15.

### Checklist
- [ ] `test_evaluate_wer.py` written & passing
- [ ] WER calculated correctly via jiwer
- [ ] Threshold at 15% (0.15) enforced
- [ ] Failing chunks return `pass: False` (will be skipped by graph)

---

## Phase 5: DB Insert Node + Storage Upload

**Goal:** Upload audio to Supabase Storage, insert metadata row to DB.

### Steps
1. `backend/src/nodes/insert_db.py`:
   - Convert chunk array to `.wav` bytes in memory (use `soundfile` or `scipy.io.wavfile`).
   - Upload to `audio_chunks/{dataset_id}/{uuid}.wav` via `supabase-py` storage.
   - Get public URL.
   - Insert row into `speech_chunks` table w/ all fields.
2. `backend/src/utils/supabase_client.py` — init client from env vars (service_role key).
3. TDD: `backend/tests/test_insert_db.py`. Mock supabase client, assert correct upload path & row payload.

### Checklist
- [ ] `test_insert_db.py` written & passing (mocked supabase)
- [ ] Audio converted to WAV bytes in-memory (no temp files)
- [ ] Upload path follows `{dataset_id}/{uuid}.wav` convention
- [ ] Public URL retrieved after upload
- [ ] DB row includes all columns: id, dataset_id, speaker_id, audio_url, original_text, aligned_text_with_timestamps, wer_score, duration, status
- [ ] `status` defaults to `pending_review`

---

## Phase 6: LangGraph Orchestrator

**Goal:** Wire all nodes into compiled stateful graph w/ error handling.

### Steps
1. `backend/src/graph.py`:
   - Define `PipelineState` TypedDict (carries data between nodes).
   - Add nodes: `fetch_hf_stream` -> `process_vad` -> `align_whisperx` -> `evaluate_wer` -> conditional edge (pass/fail) -> `insert_db`.
   - Add `on_error` edge: log error, skip chunk, continue stream.
2. Add env var support: `BATCH_SIZE`, `MAX_WORKERS`.
3. `backend/src/main.py` — entry point. Load env, compile graph, run.
4. TDD: `backend/tests/test_graph.py`. Test node transitions, test error edge triggers on exception, test WER fail skips insert.

### Checklist
- [ ] `test_graph.py` written & passing
- [ ] `PipelineState` TypedDict defined w/ all intermediate fields
- [ ] Graph compiles without error
- [ ] Happy path: fetch -> vad -> whisperx -> wer pass -> insert
- [ ] WER fail path: evaluate_wer -> skip (no insert)
- [ ] Error path: any node throws -> log + skip -> next chunk
- [ ] `BATCH_SIZE` / `MAX_WORKERS` env vars respected
- [ ] `main.py` runs end-to-end

---

## Phase 7: Frontend — Project Setup & Supabase Client

**Goal:** React + Vite + TailwindCSS scaffold. Supabase JS client wired.

### Steps
1. `npm create vite@latest frontend -- --template react-ts`.
2. Install deps: `tailwindcss`, `@supabase/supabase-js`, `wavesurfer.js`.
3. Configure Tailwind.
4. `frontend/src/lib/supabase.ts` — init client w/ anon key from env.
5. Setup vitest + @testing-library/react.

### Checklist
- [ ] Vite + React + TS builds clean
- [ ] TailwindCSS working (test w/ utility class)
- [ ] Supabase client connects (test w/ simple query)
- [ ] Vitest runs, sample test passes
- [ ] Env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

---

## Phase 8: Frontend — HITL Review UI

**Goal:** Waveform player + word regions + keyboard-first review workflow.

### Steps
1. `frontend/src/hooks/useChunkReview.ts`:
   - Fetch 1 row where `status = 'pending_review'`.
   - Expose `approve()`, `reject()`, `updateTimestamps()` mutations.
   - Auto-load next chunk after approve/reject.
2. `frontend/src/components/WaveformPlayer.tsx`:
   - Init `wavesurfer.js` w/ Regions plugin.
   - Load audio from `audio_url`.
   - Draw word regions from `aligned_text_with_timestamps` JSONB.
   - Draggable region edges -> update local state.
   - Show word text labels on regions.
3. `frontend/src/components/ReviewControls.tsx`:
   - Display WER score, duration, dataset_id, speaker_id.
   - Show pending count.
4. `frontend/src/App.tsx`:
   - Compose WaveformPlayer + ReviewControls.
   - Wire keyboard listeners (global):
     - `Space` -> play/pause
     - `Enter` -> save edits + approve + load next
     - `Delete` -> reject + load next
5. TDD: `frontend/src/tests/`:
   - `useChunkReview.test.ts` — mock supabase, assert correct payloads on approve/reject.
   - `WaveformPlayer.test.tsx` — mock wavesurfer, assert regions drawn from JSONB data.
   - `App.test.tsx` — simulate keyboard events, assert approve/reject calls fire.

### Checklist
- [ ] `useChunkReview.test.ts` passing (mocked supabase)
- [ ] `WaveformPlayer.test.tsx` passing (mocked wavesurfer)
- [ ] `App.test.tsx` passing (keyboard events)
- [ ] Waveform renders from audio URL
- [ ] Word regions drawn w/ correct start/end positions
- [ ] Region edges draggable, text editable
- [ ] `Space` toggles play/pause
- [ ] `Enter` saves edits -> approve -> loads next
- [ ] `Delete` rejects -> loads next
- [ ] Updated timestamps serialized back to JSONB on save
- [ ] WER score + metadata displayed
- [ ] Empty state shown when no pending chunks

---

## Phase 9: Docker & docker-compose

**Goal:** Containerize both services. One-command startup.

### Steps
1. `backend/Dockerfile`: Python 3.11, CUDA base image, install ffmpeg, pip install requirements.
2. `frontend/Dockerfile`: Node 20 alpine, npm install, vite build, serve static.
3. `docker-compose.yml`: backend (GPU runtime) + frontend (port 3000). Env vars from `.env`.

### Checklist
- [ ] `docker build` succeeds for backend
- [ ] `docker build` succeeds for frontend
- [ ] `docker-compose up` starts both services
- [ ] Backend can reach Supabase from container
- [ ] Frontend serves on localhost:3000
- [ ] GPU passthrough works for backend (nvidia runtime)

---

## Phase 10: Integration Test & End-to-End Validation

**Goal:** Full pipeline smoke test. Stream -> process -> store -> review in UI.

### Steps
1. Run backend pipeline on small subset (10-20 samples from libritts_r).
2. Verify rows appear in Supabase `speech_chunks` table w/ `pending_review` status.
3. Verify audio files in `audio_chunks` bucket, URLs accessible.
4. Open frontend, review chunks via UI. Approve/reject. Verify status updates in DB.
5. Check edge cases: WER > 15% chunks not in DB, error chunks logged & skipped.

### Checklist
- [ ] Pipeline processes 10+ samples without crash
- [ ] DB rows created w/ correct schema (all columns populated)
- [ ] Audio URLs load in browser
- [ ] UI fetches & displays pending chunks
- [ ] Approve/reject updates DB status
- [ ] Timestamp edits persist after save
- [ ] High-WER chunks discarded (not in DB)
- [ ] Pipeline recovers from individual chunk errors
- [ ] All backend pytest tests pass
- [ ] All frontend vitest tests pass

---

## Implementation Order & Dependencies

```
Phase 0 (Scaffold) ─┬─> Phase 1 (Fetch) ──> Phase 2 (VAD) ──> Phase 3 (WhisperX) ──> Phase 4 (WER) ──> Phase 5 (DB Insert) ──> Phase 6 (LangGraph)
                     │
                     └─> Phase 7 (Frontend Setup) ──> Phase 8 (HITL UI)
                     │
                     └─> Phase 9 (Docker) ──────────────────────────────────────────────────────────────> Phase 10 (E2E)
```

- Backend phases 1-6 are sequential (each node depends on prior output).
- Frontend phases 7-8 can run in parallel w/ backend (decoupled via Supabase).
- Phase 9 (Docker) can start after Phase 0 scaffold.
- Phase 10 requires all other phases complete.
