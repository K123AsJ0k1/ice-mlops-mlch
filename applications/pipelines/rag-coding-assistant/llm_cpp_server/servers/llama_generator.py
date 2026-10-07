import time as t
from ray import serve
from fastapi import FastAPI, Request

app = FastAPI()

@serve.deployment(
    num_replicas = 1,
    ray_actor_options = {
        "num_cpus": 1, 
        "num_gpus": 1
    } 
)
@serve.ingress(app)
class LLAMA_CPP_GENERATOR:
    def __init__(
        self,
        model_parameters: dict
    ):
        from llama_cpp import Llama

        if 0 < len(model_parameters):
            start_time = t.time()
            model_repo_id = model_parameters['repo-id']
            model_filename = model_parameters['filename']
            self.n_gpu_layers = model_parameters['n-gpu-layers']
            self.serve_id = model_parameters['serve-id']
            self.n_ctx = model_parameters['n-ctx']
            self.type_k = model_parameters['type-k']
            self.type_v = model_parameters['type-v']
            self.flash_attention = model_parameters['flash-attention']
            self.model_name = f'{model_repo_id}|{model_filename}'
            print(f'Model configurations {self.n_gpu_layers}|{self.n_ctx}|{self.type_k}|{self.type_v}')
            print(f'Fetching and initializing {self.model_name} directly from Hugging Face Hub...')
            self.llm = Llama.from_pretrained(
                repo_id = model_repo_id, 
                filename = model_filename,                    
                n_gpu_layers = self.n_gpu_layers, 
                n_ctx = self.n_ctx,
                type_k = self.type_k,
                type_v = self.type_v,   
                flash_attn = self.flash_attention, 
                verbose = False
            )
            print('Model downloaded and successfully loaded into memory!')
            end_time = t.time()

            total_time = round(end_time-start_time,5)
            print(f'Spent seconds loading model: {total_time}')

    @app.post("/inference")
    async def inference(
        self, 
        request: Request
    ):
        try:
            request_dict = await request.json()
            
            query_messages = request_dict.pop('messages', [])
            query_temperature = request_dict.pop('temperature', 0.5)
            query_max_tokens = request_dict.pop('max_tokens', 1024)
            query_top_p = request_dict.pop('top_p', 0.95)
            query_top_k = request_dict.pop('top_k', 40)
            query_frequency_penalty = request_dict.pop('frequency_penalty', 0.0)
            query_precence_penalty = request_dict.pop('presence_penalty', 0.0)
            
            if 0 < len(query_messages):
                inference_start = t.time()
                first_token_time = None

                stream = self.llm.create_chat_completion(
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

                prompt_tokens = len(self.llm.tokenize(prompt_text.encode('utf-8')))
                completion_tokens = len(self.llm.tokenize(content.encode('utf-8')))
                
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
                context_utilization = (total_tokens / self.n_ctx) if self.n_ctx > 0 else 0

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
                    'inference_server': self.serve_id,
                    'used_model': self.model_name,
                    'n_gpu_layers': self.n_gpu_layers,
                    'n_ctx': self.n_ctx,
                    'type_k': self.type_k,
                    'type_v': self.type_v,
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