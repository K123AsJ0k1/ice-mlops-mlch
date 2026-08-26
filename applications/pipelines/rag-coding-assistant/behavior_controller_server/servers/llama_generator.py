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
class LLAMA_Generator:
    def __init__(
        self,
        model_parameters: dict
    ):
        from llama_cpp import Llama

        if 0 < len(model_parameters):
            start_time = t.time()
            model_repo_id = model_parameters['repo-id']
            model_filename = model_parameters['filename']
            model_n_gpu_layers = model_parameters['n-gpu-layers']
            self.serve_id = model_parameters['serve-id']
            self.n_ctx = model_parameters['n-ctx']
            self.type_k = model_parameters['type-k']
            self.type_v = model_parameters['type-v']
            self.model_name = f'{model_repo_id}|{model_filename}'
            print(f'Model configurations {model_n_gpu_layers}|{self.n_ctx}|{self.type_k}|{self.type_v}')
            print(f'Fetching and initializing {self.model_name} directly from Hugging Face Hub...')
            self.llm = Llama.from_pretrained(
                repo_id = model_repo_id, 
                filename = model_filename,                    
                n_gpu_layers = model_n_gpu_layers, 
                n_ctx = self.n_ctx,      
                type_k = self.type_k,
                type_v = self.type_v, 
                verbose = False
            )
            print('Model downloaded and successfully loaded into memory!')
            end_time = t.time()

            total_time = round(end_time-start_time,5)
            print(f'Spent seconds loading model: {total_time}')

    @app.post("/generate")
    async def generate(
        self, 
        request: Request
    ):
        try:
            request_dict = await request.json()
            
            query_messages = request_dict.pop('messages', [])
            query_temperature = request_dict.pop('temperature', 0.5)
            query_top_p = request_dict.pop('top-p', 0.95)
            query_max_tokens = request_dict.pop('max-tokens', 1024)

            if 0 < len(query_messages):
                inference_start = t.time()

                response = self.llm.create_chat_completion(
                    messages = query_messages,
                    temperature = query_temperature,
                    top_p = query_top_p,
                    max_tokens = query_max_tokens
                )
                
                inference_end = t.time()

                usage = response.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)

                total_latency = inference_end - inference_start

                tokens_per_sec = (completion_tokens / total_latency) if total_latency > 0 else 0
                time_per_output_token = (total_latency / completion_tokens) if completion_tokens > 0 else 0

                content = response['choices'][0]['message']['content']
                
                input_to_output_ratio = (prompt_tokens / completion_tokens) if completion_tokens > 0 else 0
                context_utilization = (total_tokens / self.n_ctx) if self.n_ctx > 0 else 0
                
                metrics_payload = {
                    'inference-server': self.serve_id,
                    'used-model': self.model_name,
                    'n-ctx': self.n_ctx,
                    'type-k': self.type_k,
                    'type-v': self.type_v,
                    'temperature': query_temperature,
                    'top-p': query_top_p,
                    'max-tokens': query_max_tokens,
                    'total-inference-latency-sec': round(total_latency, 4),
                    'tokens-per-second': round(tokens_per_sec, 2),
                    'time-per-output-token-sec': round(time_per_output_token, 4),
                    'input-to-output-ratio': round(input_to_output_ratio, 2),
                    'context-window-utilization-pct': round(context_utilization * 100, 2),
                    'prompt-tokens': prompt_tokens,
                    'completion-tokens': completion_tokens,
                    'total-tokens': total_tokens
                }

                return {
                    'status': 'success', 
                    'text': content.strip(),
                    'efficiency-metrics': metrics_payload
                }
            return {'status': 'error', 'message': 'Empty query messages array provided.'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}