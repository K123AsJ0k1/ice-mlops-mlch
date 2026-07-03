#import os
#import sys
#import ray
#import re
#import time
#import json
#from importlib.metadata import version
import time as t
from ray import serve
from fastapi import FastAPI, Request
#from llama_cpp import Llama

app = FastAPI()

@serve.deployment(
    num_replicas = 1,
    ray_actor_options = {
        "num_cpus": 1, 
        "num_gpus": 1
    } 
)
@serve.ingress(app)
class LLAMA_Deployment:
    def __init__(
        self,
        model_parameters: dict
    ):
        start_time = t.time()
        from llama_cpp import Llama

        if 0 < len(model_parameters):
            model_repo_id = model_parameters['repo-id']
            model_filename = model_parameters['filename']
            model_n_gpu_layers = model_parameters['n-gpu-layers']
            model_n_ctx = model_parameters['n-ctx']
            model_name = f'{model_repo_id}|{model_filename}'

            print(f"Fetching and initializing {model_name} directly from Hugging Face Hub...")
            self.llm = Llama.from_pretrained(
                repo_id = model_repo_id, 
                filename = model_filename,                    
                n_gpu_layers = model_n_gpu_layers, 
                n_ctx = model_n_ctx,      
                verbose = False
            )
            print("Model downloaded and successfully loaded into memory!")

            end_time = t.time()

            total_time = round(end_time-start_time,5)
            print('Spent seconds', total_time)

    @app.post("/generate")
    async def generate(
        self, 
        request: Request
    ):
        #start_time = t.time()

        try:
            request_dict = await request.json()
            
            query_messages = request_dict.pop("messages", [])
            query_temperature = request_dict.pop("temperature", 0.5)
            query_max_tokens = request_dict.pop("temperature", 1024)

            if 0 < len(query_messages):

                response = self.llm.create_chat_completion(
                    messages = query_messages,
                    temperature = query_temperature,
                    max_tokens = query_max_tokens
                )
            return {"status": "success", "text": response["choices"][0]["message"]["content"].strip()}
        except Exception as e:
            return {"status": "error", "message": str(e)}