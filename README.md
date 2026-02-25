# Agentic Speech Dataset Engineering Pipeline

An automated, high-throughput data pipeline to process raw speech datasets into high-fidelity, word-level aligned audio chunks. The system utilizes an agentic workflow for processing (LangGraph) and features a React-based Human-in-the-Loop (HITL) interface for rapid human validation.

## Architecture

The project is structured as a decoupled monorepo, communicating via Supabase PostgreSQL and Storage.

- **Backend (Python)**: Orchestrated by LangGraph. Streams data from Hugging Face (`parler-tts/libritts_r`), splits audio using Silero VAD, transcribes and aligns words using Vosk, filters based on Word Error Rate (WER) using Jiwer, and inserts results to Supabase.
- **Frontend (React)**: A Vite + TailwindCSS application integrating `wavesurfer.js` (with the Regions plugin) and `@supabase/supabase-js`. Provides a keyboard-first review workflow for Human-in-the-Loop data validation.
- **Database & Storage (Supabase)**: Stores audio chunks in S3-compatible storage and metadata in a PostgreSQL database with Row-Level Security (RLS).

## Tech Stack

- **Orchestration**: LangGraph (Python)
- **Audio Processing**: Hugging Face `datasets`, `silero-vad`, `vosk`, `jiwer`
- **Database & Storage**: Supabase (PostgreSQL, Storage) - Free Tier
- **Frontend / HITL UI**: React (Vite), TailwindCSS, `wavesurfer.js` v7+
- **Containerization**: Docker & Docker Compose
- **Testing**: `pytest` (Backend), `vitest` + `@testing-library/react` (Frontend)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Supabase account (Free tier is sufficient)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AgenticSpeech
   ```

2. **Supabase Configuration**:
   - Create a new project on Supabase.
   - Run the SQL migration script (see `docs/database-schema.md`) to set up the `speech_chunks` table, enums, triggers, and RLS policies.
   - Create an `audio_chunks` storage bucket and set it to public read.

3. **Environment Variables**:
   - Copy the `.env.example` file to `.env` (or create one):
     ```env
     SUPABASE_URL=your_supabase_url
     SUPABASE_ANON_KEY=your_supabase_anon_key
     SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
     VITE_SUPABASE_URL=your_supabase_url
     VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
     ```

4. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```
   - The React frontend will be available at `http://localhost:3000` (or the configured port).
   - The Python backend will automatically start processing data from Hugging Face and populating Supabase.

## Workflow

1. **Data Ingestion**: Audio and text are streamed directly from Hugging Face to memory (no local downloading needed).
2. **Processing & Alignment**: Silero VAD splits audio into 5-15s chunks. Vosk generates transcriptions and extracts word-level timestamps.
3. **AI Quality Gate**: Jiwer computes the Word Error Rate (WER) against the ground truth. Chunks with WER > 15% are automatically discarded.
4. **Database Insertion**: Approved chunks are uploaded to Supabase Storage as `.wav` files, and metadata including JSONB timestamps is inserted into the PostgreSQL database.
5. **HITL Validation**: Users log into the React UI to review chunks with a `pending_review` status. They can adjust word timestamps visually and approve/reject using a keyboard-first interface.

## Documentation Reference
For detailed design decisions and implementation plans, see the `docs/` folder:
- [Specs](docs/specs.md)
- [Architecture](docs/architecture.md)
- [Database Schema](docs/database-schema.md)
- [Detail Plan](docs/detail-plan.md)

## Development
See `docs/detail-plan.md` for specific phases and test-driven development (TDD) guidelines for both frontend and backend.
