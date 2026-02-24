from datasets import load_dataset
import numpy as np
from typing import Iterator, Dict, Any

def fetch_hf_stream() -> Iterator[Dict[str, Any]]:
    """
    Streams the parler-tts/libritts_r dataset from HuggingFace without downloading to disk.
    Yields chunks formatted for the AgenticSpeech pipeline.
    """
    # Load dataset in streaming mode
    dataset = load_dataset("parler-tts/libritts_r", split="train", streaming=True)
    
    for item in dataset:
        # Extract required fields based on the schema mapping tests
        audio_data = item.get("audio", {})
        
        yield {
            "audio_array": np.array(audio_data.get("array", []), dtype=np.float32),
            "sample_rate": audio_data.get("sampling_rate", 24000),
            "original_text": item.get("text_normalized", ""),
            "dataset_id": "parler-tts/libritts_r",
            "speaker_id": str(item.get("speaker_id", ""))
        }
