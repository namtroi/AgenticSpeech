import pytest
import numpy as np

from src.nodes.align_whisperx import align_whisperx


class MockWhisperXModel:
    def transcribe(self, audio, batch_size=16):
        # Fake transcription output
        return {
            "segments": [
                {
                    "text": "Hello world.",
                    "start": 0.0,
                    "end": 1.5,
                }
            ],
            "language": "en",
        }


class MockAlignmentModel:
    pass


@pytest.fixture
def mock_whisperx(monkeypatch):
    """Mocks the whisperx model loading and alignment."""

    def mock_load_model(whisper_arch, device, compute_type):
        return MockWhisperXModel()

    def mock_load_align_model(language_code, device):
        return MockAlignmentModel(), {"fake": "dictionary"}

    def mock_align(segments, model, metadata, audio, device, return_char_alignments):
        # Fake alignment output matching WhisperX's format
        return {
            "segments": [
                {
                    "text": "Hello world.",
                    "start": 0.0,
                    "end": 1.5,
                    "words": [
                        {"word": "Hello", "start": 0.1, "end": 0.5, "score": 0.95},
                        {"word": "world.", "start": 0.6, "end": 1.4, "score": 0.88},
                    ],
                }
            ],
            "word_segments": [
                {"word": "Hello", "start": 0.1, "end": 0.5, "score": 0.95},
                {"word": "world.", "start": 0.6, "end": 1.4, "score": 0.88},
            ],
        }

    monkeypatch.setattr("src.nodes.align_whisperx.whisperx.load_model", mock_load_model)
    monkeypatch.setattr(
        "src.nodes.align_whisperx.whisperx.load_align_model", mock_load_align_model
    )
    monkeypatch.setattr("src.nodes.align_whisperx.whisperx.align", mock_align)


def test_align_whisperx(mock_whisperx):
    """
    Tests that align_whisperx formats the whisperx output into the
    exact UI JSONB schema contract (aligned_text_with_timestamps).
    """
    sr = 16000
    # Dummy 2s float32 audio
    audio = np.zeros(2 * sr, dtype=np.float32)

    input_data = {
        "chunk_array": audio,
        "sample_rate": sr,
        "original_text": "Hello world.",
        "start_time": 0.0,
        "end_time": 2.0,
        "duration": 2.0,
        "dataset_id": "test_ds",
        "speaker_id": "999",
    }

    output = align_whisperx(input_data)

    # 1. Pipeline context passed through
    assert output["chunk_array"] is audio
    assert output["original_text"] == "Hello world."

    # 2. Transcription extracted
    assert output["transcribed_text"] == "Hello world."

    # 3. Aligned words mapped to JSONB schema contract
    assert "aligned_words" in output
    words = output["aligned_words"]

    assert len(words) == 2
    assert words[0]["word"] == "Hello"
    assert words[0]["start"] == 0.1
    assert words[0]["end"] == 0.5
    assert words[0]["confidence"] == 0.95

    assert words[1]["word"] == "world."
    assert words[1]["start"] == 0.6
    assert words[1]["end"] == 1.4
    assert words[1]["confidence"] == 0.88
