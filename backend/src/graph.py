from typing import TypedDict, Any, List, Dict
from langgraph.graph import StateGraph, START, END

# Import actual pipeline execution nodes
from src.nodes.process_vad import process_vad
from src.nodes.align_whisperx import align_whisperx
from src.nodes.evaluate_wer import evaluate_wer
from src.nodes.insert_db import insert_db

# Quality Gate (WER)
# Quality Gate (WER)

# pass is a reserved keyword, but used heavily as a dict key by nodes.
# In older python versions TypedDict allowed 'pass', but usually
# it's best to avoid. We'll stick to 'pass_gate' and update nodes
# if necessary, or just use string literal keys. But for now, fixing:

PipelineState = TypedDict(
    "PipelineState",
    {
        "audio_array": Any,
        "sample_rate": int,
        "original_text": str,
        "dataset_id": str,
        "speaker_id": str,
        "chunk_array": Any,
        "start_time": float,
        "end_time": float,
        "duration": float,
        "transcribed_text": str,
        "aligned_words": List[Dict[str, Any]],
        "wer_score": float,
        "pass": bool,
    },
    total=False,
)


def route_quality_gate(state: PipelineState) -> str:
    """
    Conditional routing function evaluating the WER quality score.
    If pass_gate is False, we skip database insertion and end graph early.
    """
    # If the boolean flag exists and is True, continue upwards.
    if state.get("pass", False) is True:
        return "insert_db"

    # Otherwise terminate immediately to discard the chunk.
    return "end"


def get_compiled_graph():
    """
    Constructs and compiles the `StateGraph` object managing traversal
    from Start -> VAD -> WhisperX -> WER (Conditional Branch) -> Insert DB
    """
    builder = StateGraph(PipelineState)

    # Define Nodes
    builder.add_node("process_vad", process_vad)
    builder.add_node("align_whisperx", align_whisperx)
    builder.add_node("evaluate_wer", evaluate_wer)
    builder.add_node("insert_db", insert_db)

    # Define primary linear traversal vectors
    builder.add_edge(START, "process_vad")
    builder.add_edge("process_vad", "align_whisperx")
    builder.add_edge("align_whisperx", "evaluate_wer")

    # Conditional branching logic terminating off `pass` boolean flag
    builder.add_conditional_edges(
        "evaluate_wer", route_quality_gate, {"insert_db": "insert_db", "end": END}
    )

    # Terminate the graph upon successful Database upload
    builder.add_edge("insert_db", END)

    return builder.compile()
