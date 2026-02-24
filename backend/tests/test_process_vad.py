import pytest
import numpy as np

from src.nodes.process_vad import process_vad

import os
import torchaudio

def load_real_speech():
    # Load the en_vad.wav file we downloaded 
    test_dir = os.path.dirname(os.path.abspath(__file__))
    wav_path = os.path.join(test_dir, "en_vad.wav")
    
    waveform, sr = torchaudio.load(wav_path)
    
    # Resample to 16k if needed (en_vad is likely 16k already)
    if sr != 16000:
        transform = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        waveform = transform(waveform)
        sr = 16000
    
    # Convert to 1D numpy array
    audio = waveform.squeeze().numpy()
    return audio, sr

def test_process_vad_durations():
    """
    Given an actual block of speech audio, we loop it to create a ~20s file.
    The VAD should chunk it into pieces between 5s and 15s.
    """
    base_audio, sr = load_real_speech()
    
    # Repeat the audio 4 times to ensure it's long enough to force a split
    audio = np.concatenate([base_audio] * 4)
    duration_s = len(audio) / sr
    assert duration_s > 15.0, "Test audio must be > 15s to test the force-split"
    
    input_data = {
        "audio_array": audio,
        "sample_rate": sr,
        "original_text": "Fake text.",
        "dataset_id": "test_ds",
        "speaker_id": "999"
    }

    chunks = process_vad(input_data)
    
    assert isinstance(chunks, list)
    assert len(chunks) >= 2, f"Audio was {duration_s}s, should be split to respect max 15s duration"
    
    for chunk in chunks:
        assert 5.0 <= chunk["duration"] <= 15.0, f"Chunk duration {chunk['duration']} out of bounds"
        expected_len = int(chunk["duration"] * sr)
        assert abs(len(chunk["chunk_array"]) - expected_len) <= 1

def test_process_vad_strips_silence():
    """
    Given an audio block with silence at the beginning and end,
    it should correctly crop out the non-speech regions and isolate the middle speech.
    """
    base_audio, sr = load_real_speech()
    
    # En_vad.wav is ~1-2 seconds of speech. 
    # Let's pad it with 2s of absolute silence on both sides.
    silence = np.zeros(int(2.0 * sr), dtype=np.float32)
    audio = np.concatenate([silence, base_audio, silence])
    
    input_data = {
        "audio_array": audio,
        "sample_rate": sr,
        "original_text": "Silence test",
        "dataset_id": "test_ds",
        "speaker_id": "999"
    }

    chunks = process_vad(input_data)
    
    # Since the base audio is very short, padding might force it to exactly 5.0s 
    # because of our enforcing `min_length_samples = 5.0 * sr`.
    # Let's just verify we don't return the full 2s + 2s + X s.
    
    assert len(chunks) > 0
    chunk = chunks[0]
    
    # It should have stripped the initial 2s of silence.
    # Start time should be >= 1.5s
    assert chunk["start_time"] >= 1.5, f"Expected silence to be stripped, but start time is {chunk['start_time']}"
    
    # We padded 2s of silence to en_vad.wav. en_vad is around 2 seconds.
    # The output chunk should represent the speech + silence padding to make it 5s long min.
    assert chunk["duration"] >= 5.0, f"Chunk duration {chunk['duration']} should be padded to 5s"

