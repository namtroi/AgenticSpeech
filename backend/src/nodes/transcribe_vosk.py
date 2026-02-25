import json
from typing import Dict, Any
from vosk import Model, KaldiRecognizer

# Lazy-load model to save resources when not in use
_vosk_model = None

def _load_model():
    global _vosk_model
    if _vosk_model is None:
        # Load the default small English model
        # You can specify the model path here if you have downloaded a specific one
        # vosk downloads this on first execution of Model(model_name="...") if missing
        _vosk_model = Model(lang="en-us")


def transcribe_vosk(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transcribes the audio chunk using Vosk and performs word-level timestamp alignment.
    This replaces the heavy WhisperX usage for low-resource environments.
    """
    _load_model()
    
    # Audio from process_vad is expected to be a numpy array. 
    # We need to convert it to raw bytes for Vosk, 
    # making sure it's 16kHz, 16-bit mono PCM.
    import numpy as np
    audio_np = data["chunk_array"]
    # Ensure standard format (-1.0 to 1.0 -> Int16)
    audio_int16 = (audio_np * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()

    # The sampling rate is 16kHz as configured in process_vad.py
    rec = KaldiRecognizer(_vosk_model, 16000)
    
    # Enable word-level details
    rec.SetWords(True)

    # Process all audio bytes
    rec.AcceptWaveform(audio_bytes)
    
    # Retrieve the final result
    result_json = rec.FinalResult()
    result_dict = json.loads(result_json)

    transcribed_text = result_dict.get("text", "")
    aligned_words = []

    if "result" in result_dict:
        for word_info in result_dict["result"]:
            aligned_words.append({
                "word": word_info.get("word", ""),
                "start": round(word_info.get("start", 0.0), 3),
                "end": round(word_info.get("end", 0.0), 3),
                "confidence": round(word_info.get("conf", 0.0), 3),
            })

    # Mutate data dict to pass forwards
    data["transcribed_text"] = transcribed_text
    data["aligned_words"] = aligned_words

    return data
