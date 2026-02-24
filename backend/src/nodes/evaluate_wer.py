import re
import jiwer
from typing import Dict, Any

def _normalize_text(text: str) -> str:
    """
    Normalizes text for accurate WER computation.
    - Lowercases everything.
    - Removes punctuation completely.
    - Replaces multiple spaces with single spaces.
    """
    # Lowercase
    text = text.lower()
    
    # Remove punctuation (everything not word characters or spaces)
    # also remove apostrophes
    text = re.sub(r'[^\w\s]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def evaluate_wer(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates the transcribed text against the original text using 
    Word Error Rate (WER) via the jiwer algorithm.
    """
    original = _normalize_text(data.get("original_text", ""))
    transcribed = _normalize_text(data.get("transcribed_text", ""))
    
    # If both strings are empty after normalization, WER is 0 
    # (though realistically shouldn't happen unless bad VAD slice)
    if not original and not transcribed:
        wer_score = 0.0
    elif not original:
        # We transcribed words that weren't in the ground truth text at all
        wer_score = 1.0
    else:
        wer_score = jiwer.wer(original, transcribed)
    
    wer_score = round(wer_score, 3)
    
    # Enforce quality gate. Threshold is <= 15% (0.15)
    passed_gate = wer_score <= 0.15
    
    data["wer_score"] = wer_score
    data["pass"] = passed_gate
    
    return data
