import uuid
import io
import soundfile as sf
from typing import Dict, Any
from src.utils.supabase_client import get_supabase_client


def insert_db(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the fully processed pipeline payload and inserts it into Supabase.
    - Encodes raw audio to Wav bytes strictly in memory.
    - Uploads the audio buffer to Supabase Storage `audio_chunks` bucket.
    - Inserts the metadata payload into `speech_chunks` table.

    If the upstream pipeline returned `pass=False` (ie. high WER), this node
    skips the insertion and immediately returns the data dictionary.
    """
    if not data.get("pass", False):
        return data

    client = get_supabase_client()

    # 1. Generate unique identifier for this chunk
    chunk_id = str(uuid.uuid4())
    dataset_id = data.get("dataset_id", "unknown_ds")

    # 2. Convert Audio to In-Memory Wav Bytes
    # Instead of writing a file to disk and immediately uploading it, we write
    # to a BytesIO stream using soundfile to prevent disk I/O bottlenecks.
    wav_io = io.BytesIO()
    sf.write(
        file=wav_io,
        data=data["chunk_array"],
        samplerate=data["sample_rate"],
        format="WAV",
        subtype="PCM_16",
    )
    wav_bytes = wav_io.getvalue()

    # 3. Upload to Supabase Storage
    # Pattern: audio_chunks/dataset_id/uuid.wav
    storage_path = f"{dataset_id}/{chunk_id}.wav"
    bucket = client.storage.from_("audio_chunks")

    bucket.upload(
        path=storage_path, file=wav_bytes, file_options={"content-type": "audio/wav"}
    )

    # Get public URL
    public_url = bucket.get_public_url(storage_path)

    # 4. Insert Metadata into Database
    # This dictionary shape explicitly mirrors our `0000_initial_schema.sql`
    # definitions.
    payload = {
        "id": chunk_id,
        "dataset_id": dataset_id,
        "speaker_id": str(data.get("speaker_id", "")),
        "audio_url": public_url,
        "original_text": data.get("original_text", ""),
        "aligned_text_with_timestamps": {
            "transcribed_text": data.get("transcribed_text", ""),
            "aligned_words": data.get("aligned_words", []),
        },
        "wer_score": data.get("wer_score", 0.0),
        "duration": data.get("duration", 0.0),
        "status": "pending_review",  # Explicitly queue for HITL UI
    }

    client.table("speech_chunks").insert(payload).execute()

    return data
