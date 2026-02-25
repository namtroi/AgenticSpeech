import torch
import whisperx
from typing import Dict, Any

# Lazy-load models to save VRAM when not in use
_whisper_model = None
_align_model = None
_align_metadata = None


def _load_models(device: str = "cpu", compute_type: str = "float32"):
    global _whisper_model, _align_model, _align_metadata

    if _whisper_model is None:
        # Load base transcription model (can upgrade to large-v2 for prod)
        _whisper_model = whisperx.load_model("base", device, compute_type=compute_type)

    if _align_model is None:
        # Load alignment model specifically for English
        _align_model, _align_metadata = whisperx.load_align_model(
            language_code="en", device=device
        )


def align_whisperx(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transcribes the audio chunk using WhisperX and performs language-specific
    phoneme alignment to extract highly accurate word-level timestamps.
    """
    # Detect GPU if available, else fallback to CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Use float16 on GPU for speed, float32 on CPU
    compute_type = "float16" if device == "cuda" else "float32"

    _load_models(device=device, compute_type=compute_type)

    audio = data["chunk_array"]

    # 1. Transcribe
    # WhisperX expects 16kHz audio. Process VAD already yields 16k in our pipeline.
    result = _whisper_model.transcribe(audio, batch_size=4)

    # Combine full text from segments
    transcribed_text = " ".join([seg["text"].strip() for seg in result["segments"]])

    # 2. Align timestamps
    result_aligned = whisperx.align(
        result["segments"],
        _align_model,
        _align_metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    # 3. Map to Database Schema: `aligned_text_with_timestamps` JSONB struct
    aligned_words = []

    # Sometimes whisperx drops words if alignment fails entirely.
    # It returns 'word_segments' as a flat list.
    if "word_segments" in result_aligned:
        for word in result_aligned["word_segments"]:
            # If whisperx can't confidently align a word, it omits start/end.
            if "start" in word and "end" in word:
                aligned_words.append(
                    {
                        "word": word["word"],
                        "start": round(word["start"], 3),
                        "end": round(word["end"], 3),
                        "confidence": round(word.get("score", 0.0), 3),
                    }
                )

    # Mutate data dict to pass forwards
    data["transcribed_text"] = transcribed_text
    data["aligned_words"] = aligned_words

    return data
