
def llama_generate_output(
    model: any,
    server_name: str,
    model_name: str,
    n_gpu_layers: any,
    type_k: any,
    type_v: any,
    n_ctx: int,
    request: dict,
) -> any:   
    try:
        import time as t
    except ImportError as e:
        raise ImportError("llama/use failed to import", e)

    try:
        query_messages = request.pop('messages', [])
        query_temperature = request.pop('temperature', 0.5)
        query_max_tokens = request.pop('max_tokens', 1024)
        query_top_p = request.pop('top_p', 0.95)
        query_top_k = request.pop('top_k', 40)
        query_frequency_penalty = request.pop('frequency_penalty', 0.0)
        query_precence_penalty = request.pop('presence_penalty', 0.0)
        
        if 0 < len(query_messages):
            inference_start = t.time()
            first_token_time = None

            stream = model.llm.create_chat_completion(
                messages = query_messages,
                temperature = query_temperature,
                max_tokens = query_max_tokens,
                top_p = query_top_p,
                top_k = query_top_k,
                frequency_penalty = query_frequency_penalty,
                presence_penalty = query_precence_penalty,
                stream = True
            )
            
            generated_chunks = []
            for chunk in stream:
                if first_token_time is None:
                    first_token_time = t.time()
                
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    generated_chunks.append(delta['content'])

            inference_end = t.time()
            content = "".join(generated_chunks)
            
            prompt_text = " ".join([m.get("content", "") for m in query_messages])

            prompt_tokens = len(model.llm.tokenize(prompt_text.encode('utf-8')))
            completion_tokens = len(model.llm.tokenize(content.encode('utf-8')))
            
            total_tokens = prompt_tokens + completion_tokens

            total_latency = inference_end - inference_start

            # Input Processing Time (Prompt Evaluation Time)
            input_processing_time = (first_token_time - inference_start) if first_token_time else total_latency
            
            # Output Generation Time (Token Evaluation / Decode Time)
            output_generation_time = total_latency - input_processing_time

            input_tokens_per_sec = (prompt_tokens / input_processing_time) if input_processing_time > 0 else 0
            output_tokens_per_sec = (completion_tokens / output_generation_time) if output_generation_time > 0 else 0

            ttft = (first_token_time - inference_start) if first_token_time else total_latency
            decode_time = total_latency - ttft  # Time spent solely generating tokens after TTFT

            tokens_per_sec = (completion_tokens / total_latency) if total_latency > 0 else 0
            time_per_output_token = (decode_time / completion_tokens ) if completion_tokens > 0 else 0

            input_to_output_ratio = (prompt_tokens / completion_tokens) if completion_tokens > 0 else 0
            context_utilization = (total_tokens / n_ctx) if n_ctx > 0 else 0

            metrics_payload = {
                'prompt-tokens': prompt_tokens,
                'completion-tokens': completion_tokens,
                'total-tokens': total_tokens,
                'total-latency-sec': total_latency,
                'prompt-processing-time-sec': input_processing_time,
                'generation-time-sec': output_generation_time,
                'input-tokens-per-sec': input_tokens_per_sec,
                'output-tokens-per-sec': output_tokens_per_sec,
                'time-to-first-token-sec': ttft,
                'tokens-per-second': tokens_per_sec,
                'time-per-output-token-sec': time_per_output_token,
                'input-to-output-ratio': input_to_output_ratio,
                'context-window-utilization-pct': context_utilization * 100
            }

            metadata_payload = {
                'inference_server': server_name,
                'used_model': model_name,
                'n_gpu_layers': n_gpu_layers,
                'n_ctx': n_ctx,
                'type_k': type_k,
                'type_v': type_v,
                'temperature': query_temperature,
                'max_tokens': query_max_tokens,
                'top_p': query_top_p,

            }

            return {
                'status': 'success', 
                'response': content.strip(),
                'metadata': metadata_payload,
                'metrics': metrics_payload
            }
        return {
            'status': 'error', 
            'response': 'Empty query messages array provided.',
            'metadata': {},
            'metrics': {}
        }
    except Exception as e:
        return {
            'status': 'error', 
            'response': str(e),
            'metadata': {},
            'metrics': {}
        }