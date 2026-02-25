import pytest
import numpy as np

# We'll mock the HF dataset load
from src.nodes.fetch_hf import fetch_hf_stream


class MockIterableDataset:
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        return iter(self.items)


@pytest.fixture
def mock_hf_dataset(monkeypatch):
    """Mocks the datasets.load_dataset call to yield a dummy item."""
    dummy_item = {
        "audio": {
            "array": np.array([0.1, 0.2, 0.3], dtype=np.float32),
            "sampling_rate": 24000,
        },
        "text_normalized": "Hello world",
        "speaker_id": "1234",
        "id": "1234_5678",
    }

    def mock_load_dataset(path, split, streaming, **kwargs):
        assert path == "mythicinfinity/libritts"
        assert streaming is True
        return MockIterableDataset([dummy_item])

    monkeypatch.setattr("src.nodes.fetch_hf.load_dataset", mock_load_dataset)


def test_fetch_hf_stream(mock_hf_dataset):
    """Ensures the transformer yields the expected dictionary layout."""
    stream = fetch_hf_stream()
    first_item = next(stream)

    assert "audio_array" in first_item
    assert "sample_rate" in first_item
    assert "original_text" in first_item
    assert "dataset_id" in first_item
    assert "speaker_id" in first_item

    assert isinstance(first_item["audio_array"], np.ndarray)
    assert first_item["sample_rate"] == 16000
    assert first_item["original_text"] == "Hello world"
    assert first_item["dataset_id"] == "mythicinfinity/libritts"
    assert first_item["speaker_id"] == "1234"
