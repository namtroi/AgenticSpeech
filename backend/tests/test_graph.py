import pytest
from unittest.mock import MagicMock, patch

from src.graph import get_compiled_graph, PipelineState

@pytest.fixture
def mock_pipeline_nodes(monkeypatch):
    """
    Mocks the heavy computation nodes to return state instantly.
    """
    mock_vad = MagicMock(return_value={"pass": True})
    mock_whisperx = MagicMock(return_value={"pass": True})
    mock_wer = MagicMock(return_value={"pass": True, "wer_score": 0.0})
    mock_insert = MagicMock(return_value={"pass": True})
    
    # We patch the actual python modules so Graph imports the mocks
    monkeypatch.setattr("src.graph.process_vad", mock_vad)
    monkeypatch.setattr("src.graph.align_whisperx", mock_whisperx)
    monkeypatch.setattr("src.graph.evaluate_wer", mock_wer)
    monkeypatch.setattr("src.graph.insert_db", mock_insert)
    
    return {
        "vad": mock_vad,
        "whisperx": mock_whisperx,
        "wer": mock_wer,
        "insert": mock_insert
    }

def test_graph_happy_path(mock_pipeline_nodes):
    """
    Tests that a passing chunk (WER = 0.0) traverses the entire graph
    from VAD -> WhisperX -> WER -> Insert DB.
    """
    graph = get_compiled_graph()
    
    initial_state: PipelineState = {
        "audio_array": None,
        "sample_rate": 16000,
        "original_text": "Hello world",
        "dataset_id": "test",
        "speaker_id": "1",
        "pass": True
    }
    
    # Run graph execution
    final_state = graph.invoke(initial_state)
    
    # Assert all nodes were called in sequence
    mock_pipeline_nodes["vad"].assert_called_once()
    mock_pipeline_nodes["whisperx"].assert_called_once()
    mock_pipeline_nodes["wer"].assert_called_once()
    mock_pipeline_nodes["insert"].assert_called_once()
    
    assert final_state["pass"] is True


def test_graph_fail_path(mock_pipeline_nodes):
    """
    Tests that a failing chunk (WER > 0.15) skips the Insert DB node.
    """
    # Force the WER node to fail the quality gate
    mock_pipeline_nodes["wer"].return_value = {"pass": False, "wer_score": 1.0}
    
    graph = get_compiled_graph()
    
    initial_state: PipelineState = {
        "audio_array": None,
        "sample_rate": 16000,
        "original_text": "Hello world",
        "dataset_id": "test",
        "speaker_id": "1",
        "pass": True
    }
    
    final_state = graph.invoke(initial_state)
    
    mock_pipeline_nodes["vad"].assert_called_once()
    mock_pipeline_nodes["whisperx"].assert_called_once()
    mock_pipeline_nodes["wer"].assert_called_once()
    
    # CRITICAL: Insert DB should NOT be called since pass=False
    mock_pipeline_nodes["insert"].assert_not_called()
    assert final_state["pass"] is False
