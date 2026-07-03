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
            self.n_ctx = model_parameters['n-ctx']
            model_name = f'{model_repo_id}|{model_filename}'
            print(f'Model configurations {model_n_gpu_layers}|{self.n_ctx}')
            print(f"Fetching and initializing {model_name} directly from Hugging Face Hub...")
            self.llm = Llama.from_pretrained(
                repo_id = model_repo_id, 
                filename = model_filename,                    
                n_gpu_layers = model_n_gpu_layers, 
                n_ctx = self.n_ctx,      
                verbose = False
            )
            print("Model downloaded and successfully loaded into memory!")
            end_time = t.time()

            total_time = round(end_time-start_time,5)
            print(f'Spent seconds loading model: {total_time}')

    @app.post("/generate")
    async def generate(
        self, 
        request: Request
    ):
        import re
        try:
            request_dict = await request.json()
            
            query_messages = request_dict.pop("messages", [])
            query_temperature = request_dict.pop("temperature", 0.5)
            query_max_tokens = request_dict.pop("max-tokens", 1024)

            if 0 < len(query_messages):
                inference_start = t.time()

                response = self.llm.create_chat_completion(
                    messages = query_messages,
                    temperature = query_temperature,
                    max_tokens = query_max_tokens
                )
                
                inference_end = t.time()

                usage = response.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                total_latency = inference_end - inference_start

                tokens_per_sec = (completion_tokens / total_latency) if total_latency > 0 else 0
                time_per_output_token = (total_latency / completion_tokens) if completion_tokens > 0 else 0

                content = response["choices"][0]["message"]["content"]
                think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                # doesn work
                if think_match:
                    think_text = think_match.group(1)
                    # Encode text and tokenize using llama_cpp internal tokenizer to get exact footprint
                    think_tokens = len(self.llm.tokenize(think_text.encode('utf-8'), add_bos=False))
                else:
                    think_tokens = 0
                
                reasoning_token_ratio = (think_tokens / completion_tokens) if completion_tokens > 0 else 0

                input_to_output_ratio = (prompt_tokens / completion_tokens) if completion_tokens > 0 else 0
                context_utilization = (total_tokens / self.n_ctx) if self.n_ctx > 0 else 0
                # Edit this to remove reasoning tokens and ratio
                # remove _
                # put the raw_token_counts up
                metrics_payload = {
                    "total_inference_latency_sec": round(total_latency, 4),
                    "tokens_per_second": round(tokens_per_sec, 2),
                    "time_per_output_token_sec": round(time_per_output_token, 4),
                    "input_to_output_ratio": round(input_to_output_ratio, 2),
                    "context_window_utilization_pct": round(context_utilization * 100, 2),
                    "deepseek_reasoning_tokens": think_tokens,
                    "deepseek_reasoning_ratio": round(reasoning_token_ratio, 4),
                    "raw_token_counts": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens
                    }
                }

                return {
                    "status": "success", 
                    "text": content.strip(),
                    "efficiency_metrics": metrics_payload
                }
            return {"status": "error", "message": "Empty query messages array provided."}
        except Exception as e:
            return {"status": "error", "message": str(e)}