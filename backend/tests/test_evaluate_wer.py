import pytest
from src.nodes.evaluate_wer import evaluate_wer

def test_evaluate_wer_exact_match():
    """WER should be 0.0 and chunk should pass."""
    data = {
        "original_text": "Hello world, this is a test.",
        "transcribed_text": "Hello world, this is a test."
    }
    
    result = evaluate_wer(data)
    
    assert result["wer_score"] == 0.0
    assert result["pass"] is True


def test_evaluate_wer_total_mismatch():
    """WER should be 1.0 or higher and chunk should fail."""
    data = {
        "original_text": "Hello world.",
        "transcribed_text": "Goodbye everyone."
    }
    
    result = evaluate_wer(data)
    
    assert result["wer_score"] >= 1.0
    assert result["pass"] is False


def test_evaluate_wer_case_and_punctuation_insensitivity():
    """
    WER evaluation should ignore casing and punctuation differences,
    yielding 0.0 if the spoken words are phonetically identical.
    """
    data = {
        "original_text": "Hello world... It's me!",
        "transcribed_text": "hello world its me"
    }
    
    result = evaluate_wer(data)
    
    assert result["wer_score"] == 0.0
    assert result["pass"] is True


def test_evaluate_wer_edge_case():
    """
    Test the strict boundary conditions. Threshold is <= 0.15.
    1 error out of 10 words = 0.10 (Passes)
    2 errors out of 10 words = 0.20 (Fails)
    """
    # 10 words total. 1 error.
    data_pass = {
        "original_text": "one two three four five six seven eight nine ten",
        "transcribed_text": "one two three four wrong six seven eight nine ten"
    }
    
    res1 = evaluate_wer(data_pass)
    assert res1["wer_score"] == 0.1
    assert res1["pass"] is True
    
    # 10 words total. 2 errors.
    data_fail = {
        "original_text": "one two three four five six seven eight nine ten",
        "transcribed_text": "one two completely wrong five six seven eight nine ten"
    }
    
    res2 = evaluate_wer(data_fail)
    assert res2["wer_score"] == 0.2
    assert res2["pass"] is False
