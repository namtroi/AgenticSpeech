from datasets import load_dataset
import numpy as np
from typing import Iterator, Dict, Any
import librosa
def fetch_hf_stream() -> Iterator[Dict[str, Any]]:
    """
    Streams the parler-tts/libritts_r dataset from HuggingFace without downloading to disk.
    Yields chunks formatted for the AgenticSpeech pipeline.
    """
    # Load dataset in streaming mode
    dataset = load_dataset("mythicinfinity/libritts", name="dev", split="dev.clean", streaming=True)

    for item in dataset:
        # Extract required fields based on the schema mapping tests
        audio_data = item.get("audio", {})
        original_sr = audio_data.get("sampling_rate", 24000)
        audio_arr = np.array(audio_data.get("array", []), dtype=np.float32)

        # Silero VAD strictly requires 16000 or 8000 Hz, resample using librosa
        if original_sr != 16000 and len(audio_arr) > 0:
            audio_arr = librosa.resample(audio_arr, orig_sr=original_sr, target_sr=16000)

        yield {
            "audio_array": audio_arr,
            "sample_rate": 16000,
            "original_text": item.get("text_normalized", ""),
            "dataset_id": "parler-tts/libritts_r",
            "speaker_id": str(item.get("speaker_id", "")),
        }
