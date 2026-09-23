---
technologies: "llama.cpp"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# Llama.cpp

## Used material

1. <span id="used-material-1"></span> [llama-cpp-python pip package](https://pypi.org/project/llama-cpp-python/)

2. <span id="used-material-2"></span> [llama-cpp-python  API Reference](https://llama-cpp-python.readthedocs.io/en/latest/api-reference/)

3. <span id="used-material-3"></span> [GGUF](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)

## Why use Llama.cpp?

Llama.cpp is the most common inference framework for running LLMs in constrained environments for the following reasons:

- Provides a quantization engine for running high-parameter models using consumer hardware with high performance inference and wide industrial adaption (mature)

- Easy-to-use web server with widely adopted APIs that enable running models configured with the GGUF single-file format and unified hardware offloading (abstracted)

- Widely supports many programming ecosystems, hardware architectures, and tools (interoperable)

These features make llama.cpp the default inference framework for old architectures and constrained hardware. We will use it to run LLMs in local and cloud environments.  

## How to use Llama.cpp?

Assuming you have checked the [Ray chapter](../part-6/01_ray.md), we can use Ray Serve with llama-cpp-python [(1)](#used-material-1) to create the example [inference server Ray script](./ray/llama_cpp_server/main.py). The critical parts of this Ray script consist of the following:

1. Giving the cluster the packages with correct CUDA compatability 

```
# For NVIDIA P100 with CUDA 13.0
--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
llama-cpp-python>=0.3.1

# For RTX4070 and RTX4090 with CUDA 13.1
--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu130
llama-cpp-python>=0.3.1
```

2. Creating a serve instance with a unique name and prefix

```
serve_instance_name = serve_parameters['name']
serve_route_prefix = serve_parameters['prefix']

serve.run(
    LLAMA_Generator.bind(
        model_parameters = generator_model_parmaters
    ), 
    name = serve_instance_name, 
    route_prefix = serve_route_prefix
) 
```

3. Using the provided parameters to initilize the model

```
from llama_cpp import Llama

model_repo_id = model_parameters['repo-id']
model_filename = model_parameters['filename']
model_n_gpu_layers = model_parameters['n-gpu-layers']
self.n_ctx = model_parameters['n-ctx']
self.type_k = model_parameters['type-k']
self.type_v = model_parameters['type-v']

self.llm = Llama.from_pretrained(
    repo_id = model_repo_id, 
    filename = model_filename,                    
    n_gpu_layers = model_n_gpu_layers, 
    n_ctx = self.n_ctx,
    type_k = self.type_k,
    type_v = self.type_v,      
    verbose = False
)
```

4. When the model is running, processing the sent HTTP JSON inputs

```
request_dict = await request.json()

query_messages = request_dict.pop('messages', [])
query_temperature = request_dict.pop('temperature', 0.5)
query_top_p = request_dict.pop('top-p', 0.95)
query_max_tokens = request_dict.pop('max-tokens', 1024)

response = self.llm.create_chat_completion(
    messages = query_messages,
    temperature = query_temperature,
    top_p = query_top_p,
    max_tokens = query_max_tokens
)

content = response['choices'][0]['message']['content']
```

The explanations for the parameters given in steps 3 and 4 are the following |[(2)](#used-material-2),[(3)](#used-material-3)|:

- Initialization:
    - repo_id: Hugging Face Hub repository identifier such as unsloth/Qwen3.5-9B-GGUF
    - filename: Exact file name within the repository to download such as *Q4_K_M.gguf
    - n_gpu_layers: Number of layers offloaded to GPU VRAM
        - 0: Runs completely on CPU
        - N: Offloads the first n layers to GPU with the rest running on CPU
        - -1: Offloads all layers to GPU
    - n_ctx: Maximum context window available to the model, such as 8192. Includes both input prompt tokens and the generated output tokens. Increasing the value increases VRAM use
    - type_k: Data type used to quantize and store key vectors in KV cache, such as 1 for GGML_TYPE_F16
    - type_v: Data type used to quantize and store value vectors in KV cache, such as 1 for GGML_TYPE_F16
    - flash_attn: Set true to use flash attention during context processing and inference. Requires new GPUs. Makes processing faster with reduced VRAM consumption.
    - verbose: Set to true to see detailed C++ low-level logs
- Inference:
    - messages: A list of dictionaries representing the conversation history in sequence. Each has a role and content, such as [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}]
    - temperature: Controls randomness of the model with a value between 0.0 and 2.0
        - 0.0: Deterministic
        - 0.7: Balanced
        - 1.2+: Creative with possible hallucinations
    - top_p: Filters the probability distribution to only consider tokens whose cumulative probability is the set value, such as 0.9, to prevent wild outliers
    - top_k: Limits the model's vocabulary choices to only the K most probable next tokens
        - 40: Default
        - 1: Deterministic
        - 0: Deactivated
    - max_tokens: Maximum number of tokens the model is permitted to generate in a single turn. After reaching it, the generation stops regardless of whether the sentence of thought is unfinished
    - stream: Set to true to generate tokens one by one in real time

This script will continue to run as long as the cluster exists, which is why you can use the example [shutdown Ray script](./ray/serve_shutdown/main.py) to stop all serve instances. We will show how to shutdown specific instances later. 

Together, these let us create an inference server on Ray clusters using local or cloud GPUs. We will use this to test various open-source models and later develop functions for our workflows. 

---