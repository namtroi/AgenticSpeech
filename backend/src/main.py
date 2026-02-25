import os
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.graph import get_compiled_graph
from src.nodes.fetch_hf import fetch_hf_stream
from src.nodes.process_vad import process_vad


def main():
    """
    Primary execution entrypoint for the Agentic Speech Backend Pipeline.
    Loads configurations, initiates the HuggingFace generator stream,
    and maps the LangGraph compiled state machine across a ThreadPool.
    """
    # 1. Load Configurations
    load_dotenv()

    # We allow configurations to define parallelization and batch scale
    batch_size = int(os.environ.get("BATCH_SIZE", "10"))
    max_workers = int(os.environ.get("MAX_WORKERS", "4"))

    print(
        f"[AgenticSpeech] Starting pipeline with BATCH_SIZE={batch_size} and MAX_WORKERS={max_workers}"
    )

    # 2. Compile Graph
    graph = get_compiled_graph()

    # 3. Process Stream in Batches
    stream_generator = fetch_hf_stream()

    processed_count = 0
    start_time = time.time()

    batch = []

    # We iterate over the infinite stream, collecting items up to BATCH_SIZE
    for data_dict in stream_generator:
        chunks = process_vad(data_dict)
        for chunk in chunks:
            # Propagate the parent metadata into each separate chunk state
            chunk["original_text"] = data_dict.get("original_text", "")
            chunk["dataset_id"] = data_dict.get("dataset_id", "")
            chunk["speaker_id"] = data_dict.get("speaker_id", "")
            
            batch.append(chunk)

        if len(batch) >= batch_size:
            _process_batch(graph, batch, max_workers)
            processed_count += len(batch)
            print(f"[AgenticSpeech] Processed {processed_count} audio chunks total.")
            batch = []  # Reset batch

    # Flush any remaining items in the final partial batch
    if batch:
        _process_batch(graph, batch, max_workers)
        processed_count += len(batch)

    end_time = time.time()
    print(
        f"[AgenticSpeech] Pipeline finished. Processed {processed_count} chunks in {end_time - start_time:.2f} seconds."
    )


def _process_batch(graph, batch, max_workers):
    """
    Executes a batch of PipelineState dictionaries against the LangGraph
    using a concurrent ThreadPoolExecutor to accelerate IO-bound DB uploads.
    """
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for state in batch:
            # Graph.invoke executes the state machine synchronously inside
            # its designated worker thread.
            futures.append(executor.submit(graph.invoke, state))

        # Await completion and catch potential node-level exceptions
        for future in as_completed(futures):
            try:
                final_state = future.result()
                # Optionally log pass/fail status
                pass_status = final_state.get("pass", False)
                if not pass_status:
                    print(
                        f"  [Gate] Dropped chunk due to high WER: {final_state.get('wer_score')}"
                    )
            except Exception as e:
                print(f"  [Error] Chunk processing failed: {str(e)}")


if __name__ == "__main__":
    main()
