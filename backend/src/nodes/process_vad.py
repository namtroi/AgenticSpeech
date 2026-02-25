import torch
import numpy as np
from typing import Dict, List, Any

# Lazy-load model to save RAM until called
_vad_model = None
_get_speech_timestamps = None


def _load_silero():
    global _vad_model, _get_speech_timestamps
    if _vad_model is None:
        # Load silero-vad
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        _vad_model = model
        _get_speech_timestamps = utils[0]


def process_vad(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Takes the raw audio array, applies Silero VAD to find speech regions,
    and returns chunks constrained between 5-15 seconds.
    """
    _load_silero()

    audio_full = data["audio_array"]
    sr = data["sample_rate"]

    # Silero works best at 16k.
    # We will compute timestamps based on the provided sample rate,
    # but strictly speaking PyTorch tensors are expected.
    tensor_audio = torch.from_numpy(audio_full)

    if len(tensor_audio.shape) > 1:
        tensor_audio = tensor_audio.squeeze()

    # Get timestamps in samples (default output of silero)
    # Note: For production fidelity, audio should be resampled to 16kHz if not already.
    # For MVP we pass `sampling_rate=sr`.
    speech_timestamps = _get_speech_timestamps(
        tensor_audio, _vad_model, sampling_rate=sr
    )

    # Strategy: Merge short segments, split long segments
    # to enforce chunks of duration 5.0s <= d <= 15.0s
    chunks = []

    current_chunk_start = -1
    current_chunk_end = -1

    min_length_samples = int(5.0 * sr)
    max_length_samples = int(15.0 * sr)

    for ts in speech_timestamps:
        start_samples = ts["start"]
        end_samples = ts["end"]

        if current_chunk_start == -1:
            current_chunk_start = start_samples
            current_chunk_end = end_samples
        else:
            # How long would the chunk be if we merged this segment?
            # Notice we merge the silence BETWEEN as well to keep it contiguous for Whisper.
            merged_duration = end_samples - current_chunk_start

            if merged_duration > max_length_samples:
                # Flush the current accrued chunk
                _flush_chunk(
                    chunks,
                    audio_full,
                    sr,
                    current_chunk_start,
                    current_chunk_end,
                    min_length_samples,
                    max_length_samples,
                )

                # Start new chunk with current segment
                current_chunk_start = start_samples
                current_chunk_end = end_samples
            else:
                # Keep merging
                current_chunk_end = end_samples

    # Flush the last one if anything is pending
    if current_chunk_start != -1:
        _flush_chunk(
            chunks,
            audio_full,
            sr,
            current_chunk_start,
            current_chunk_end,
            min_length_samples,
            max_length_samples,
        )

    return chunks


def _flush_chunk(chunks, audio_full, sr, start, end, min_len, max_len):
    """
    Helper to append a physical chunk to the array, gracefully handling splits
    if the incoming block itself is > 15s long (like a 20s continuous speech block).
    Also attempts to pad if < 5s.
    """
    total_len = end - start

    if total_len > max_len:
        # The block itself is huge. We must split it into max_len chunks.
        chunks_count = int(np.ceil(total_len / max_len))
        target_len = int(total_len / chunks_count)  # e.g., 20s -> two 10s chunks

        for i in range(chunks_count):
            sub_start = start + (i * target_len)
            sub_end = min(end, sub_start + target_len)

            # Note: We skip the min_len check here because mathematically
            # splitting a long block guarantees it's fairly distributed.

            arr = audio_full[sub_start:sub_end]
            dur = len(arr) / sr

            chunks.append(
                {
                    "chunk_array": arr,
                    "start_time": sub_start / sr,
                    "end_time": sub_end / sr,
                    "duration": dur,
                    "sample_rate": sr,
                }
            )
    else:
        # Check if padding is required to reach 5s
        if total_len < min_len:
            # Add silence padding to reach exactly 5.0 seconds
            pad_amount = min_len - total_len
            arr = np.concatenate(
                [audio_full[start:end], np.zeros(pad_amount, dtype=np.float32)]
            )
            sub_start = start
            sub_end = start + min_len
        else:
            arr = audio_full[start:end]
            sub_start = start
            sub_end = end

        dur = len(arr) / sr

        chunks.append(
            {
                "chunk_array": arr,
                "start_time": sub_start / sr,
                "end_time": sub_end / sr,
                "duration": dur,
                "sample_rate": sr,
            }
        )
