import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.nodes.insert_db import insert_db


@pytest.fixture
def mock_supabase(monkeypatch):
    """
    Mocks the Supabase client so no actual network calls are made.
    """
    mock_client = MagicMock()

    # Mock for .storage.from_().upload()
    mock_storage = MagicMock()
    mock_client.storage.from_.return_value = mock_storage
    mock_storage.get_public_url.return_value = (
        "https://mock.supabase.co/storage/v1/object/public/audio_chunks/test_ds/fake_uuid.wav"
    )

    # Mock for .table().insert().execute()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Patch the get_supabase_client function in insert_db.py
    monkeypatch.setattr("src.nodes.insert_db.get_supabase_client", lambda: mock_client)

    return mock_client


@patch("src.nodes.insert_db.uuid")
def test_insert_db_success(mock_uuid, mock_supabase):
    """
    Tests that a passing chunk is correctly uploaded to storage
    and a metadata row is inserted into the database.
    """
    # Force uuid4 to return a fixed string
    mock_uuid.uuid4.return_value = "fake_uuid"

    # Ensure audio array is valid float32
    audio = np.zeros(16000 * 2, dtype=np.float32)

    data = {
        "pass": True,
        "chunk_array": audio,
        "sample_rate": 16000,
        "original_text": "Hello world.",
        "transcribed_text": "Hello world.",
        "dataset_id": "test_ds",
        "speaker_id": "999",
        "aligned_words": [
            {"word": "Hello", "start": 0.1, "end": 0.5, "confidence": 0.99},
            {"word": "world.", "start": 0.6, "end": 1.0, "confidence": 0.98},
        ],
        "wer_score": 0.0,
        "duration": 2.0,
    }

    result = insert_db(data)

    # Assert input was returned unmodified
    assert result is data

    # 1. Verify Storage Upload
    storage_mock = mock_supabase.storage.from_()
    storage_mock.upload.assert_called_once()

    # The first arg to upload is the destination path mapping
    upload_args, upload_kwargs = storage_mock.upload.call_args
    assert upload_kwargs["path"] == "test_ds/fake_uuid.wav"
    # Ensure the uploaded byte buffer was marked as audio/wav
    assert upload_kwargs.get("file_options", {}).get("content-type") == "audio/wav"

    # 2. Verify DB Insert
    table_mock = mock_supabase.table()
    table_mock.insert.assert_called_once()

    insert_payload = table_mock.insert.call_args[0][0]

    # Check that payload matches 0000_initial_schema.sql columns
    assert insert_payload["id"] == "fake_uuid"
    assert insert_payload["dataset_id"] == "test_ds"
    assert insert_payload["speaker_id"] == "999"
    assert (
        insert_payload["audio_url"]
        == "https://mock.supabase.co/storage/v1/object/public/audio_chunks/test_ds/fake_uuid.wav"
    )
    assert insert_payload["original_text"] == "Hello world."
    assert insert_payload["aligned_text_with_timestamps"] == {
        "transcribed_text": data["transcribed_text"],
        "aligned_words": data["aligned_words"],
    }
    assert insert_payload["wer_score"] == 0.0
    assert insert_payload["duration"] == 2.0
    assert insert_payload["status"] == "pending_review"


def test_insert_db_skip_failure(mock_supabase):
    """
    Tests that a failing chunk (pass=False) is entirely skipped
    (no storage upload, no DB insert).
    """
    data = {
        "pass": False,
        "chunk_array": np.zeros(10),
        "dataset_id": "test_ds",
        # ... other fields
    }

    result = insert_db(data)

    # Assert unmodified return
    assert result is data

    # Ensure no API calls were made
    mock_supabase.storage.from_.assert_not_called()
    mock_supabase.table.assert_not_called()
