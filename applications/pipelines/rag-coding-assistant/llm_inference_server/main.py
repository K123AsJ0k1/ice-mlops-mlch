import os
import sys
import ray
import re
import time
import json
from importlib.metadata import version
from ray import serve
from fastapi import FastAPI, Body
from llama_cpp import Llama

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
        if 0 < len(model_parameters):
            

        model_name = f''

        print("Fetching and initializing model directly from Hugging Face Hub...")
        
        # Llama.from_pretrained downloads the model automatically.
        # Any additional standard parameters (like n_gpu_layers, n_ctx) are passed as kwargs.
        '''
        # works on vm1 P100
        self.llm = Llama.from_pretrained(
            repo_id = "unsloth/Qwen3.5-2B-GGUF", # Replace with actual Qwen3.5 GGUF repo path when released
            filename = "*Q4_K_M.gguf",                    # Uses wildcards or exact filenames
            n_gpu_layers = -1,                            # Offload to the Ray-allocated GPU slice
            n_ctx = 4096,                                 # Constrain context window
            verbose = False
        )
        '''
        '''
        # works on vm1 P100
        self.llm = Llama.from_pretrained(
            repo_id = "unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF", 
            filename = "*Q4_K_M.gguf",                    
            n_gpu_layers = -1,  # -1 offloads all 32 layers completely to the P100 VRAM
            n_ctx = 4096,       # 4096 context context fits comfortably in 16GB VRAM
            verbose = False
        )
        '''
        '''
        # works on vm1 P100
        self.llm = Llama.from_pretrained(
            repo_id = "mistralai/Ministral-3-3B-Instruct-2512-GGUF", 
            filename = "*Q4_K_M.gguf",                    
            n_gpu_layers = -1,  # Safely offloads all layers completely to your P100 GPU
            n_ctx = 4096,       # Constrained context window for optimized VRAM mapping
            verbose = False
        )
        '''
        #self.llm = Llama.from_pretrained(
        #    repo_id = "unsloth/gemma-4-E2B-it-GGUF", 
        #    filename = "*Q4_K_M.gguf",  # Pulls the smart QAT Dynamic 4-bit version                  
        #    n_gpu_layers = -1,              # Completely offloads all layers to the P100 GPU
        #    n_ctx = 4096,                   # Base context window
        #    verbose = False
        #)
        print("Model downloaded and successfully loaded into memory!")

    @app.post("/generate")
    async def generate(
        self, 
        prompt: str = Body(..., embed=True),
        system_message: str = Body("You are a helpful assistant.", embed=True)
    ):
        try:
            '''
            qwen
            response = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
            )
            '''
            '''
            deepseek
            response = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature = 0.6, # DeepSeek recommends 0.5 - 0.7 to avoid infinite reasoning loops
                max_tokens = 1024  # Give it extra room to emit its <think> chain
            )
            '''
            '''
            ministral-3
            response = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature = 0.1, # Mistral recommends < 0.1 for strict task instruction following
                max_tokens = 1024
            )
            '''
            #response = self.llm.create_chat_completion(
            #    messages=[
            #        {"role": "system", "content": system_message},
            #        {"role": "user", "content": prompt}
            #    ],
            #    temperature = 1.0, # Official Google DeepMind recommended default for Gemma 4
            #    max_tokens = 1024
            #)
            return {"status": "success", "text": response["choices"][0]["message"]["content"].strip()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def llama_test(
    job_parameters: dict
):
    try:
        serve_parameters = job_parameters['serve']
        serve_host = serve_parameters['host']
        serve_port = serve_parameters['port']

        serve.start(
            http_options = {
                'host': serve_host,
                'port': serve_port
            }
        )

        serve.run(
            LLAMA_Deployment.bind(), 
            name = 'llama_server', 
            route_prefix='/'
        )   
        
        #time.sleep(240)    
        #serve.shutdown()  
        return True
    except Exception as e:
        print(f'llama error {e}')
        return False 

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'fastapi',
        'llama-cpp-python',
        'huggingface-hub',
        'jinja2'
    ]
   
    for pkg_name in check_packages:
        try:
            print(f'{pkg_name} version is {version(pkg_name)}')
        except Exception as e:
            print(f'package not found error {e}')

    print('Getting input')
    job_parameters = json.loads(sys.argv[1])

    print('Running llama test')
    testing_data_output = llama_test(
        job_parameters = job_parameters
    )
    print('Testing success:' + str(testing_data_output))

    print('Ray job Complete')