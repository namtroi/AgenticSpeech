import numpy as np
from unittest.mock import patch, MagicMock

from src.nodes.transcribe_vosk import transcribe_vosk

@patch("src.nodes.transcribe_vosk.Model")
@patch("src.nodes.transcribe_vosk.KaldiRecognizer")
def test_transcribe_vosk(mock_recognizer, mock_model):
    """
    Test the Vosk transcription node specifically focusing on 
    the parsing of KaldiRecognizer output into the required dict format.
    """
    
    # Mock Vosk KaldiRecognizer instance
    mock_rec_instance = MagicMock()
    mock_recognizer.return_value = mock_rec_instance
    
    # Mock the JSON output from FinalResult()
    mock_json_response = '''
    {
      "result": [
        {"conf": 1.0, "end": 0.60, "start": 0.36, "word": "hello"},
        {"conf": 0.99, "end": 1.05, "start": 0.60, "word": "world"}
      ],
      "text": "hello world"
    }
    '''
    mock_rec_instance.FinalResult.return_value = mock_json_response
    
    # 1-second of mock Float32 audio via numpy
    mock_audio = np.zeros(16000, dtype=np.float32)

    data_in = {
        "chunk_array": mock_audio
    }

    # Execute
    data_out = transcribe_vosk(data_in)

    # Verify Calls
    mock_model.assert_called_once_with(lang="en-us")
    mock_recognizer.assert_called_once()
    mock_rec_instance.SetWords.assert_called_once_with(True)
    mock_rec_instance.AcceptWaveform.assert_called_once()
    mock_rec_instance.FinalResult.assert_called_once()

    # Verify Mutated Data
    assert data_out["transcribed_text"] == "hello world"
    
    # Verify word alignment mapping
    assert len(data_out["aligned_words"]) == 2
    
    assert data_out["aligned_words"][0]["word"] == "hello"
    assert data_out["aligned_words"][0]["start"] == 0.36
    assert data_out["aligned_words"][0]["end"] == 0.60
    assert data_out["aligned_words"][0]["confidence"] == 1.0

    assert data_out["aligned_words"][1]["word"] == "world"
    assert data_out["aligned_words"][1]["start"] == 0.60
    assert data_out["aligned_words"][1]["end"] == 1.05
    assert data_out["aligned_words"][1]["confidence"] == 0.99
