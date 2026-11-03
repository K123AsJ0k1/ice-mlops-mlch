import ray
import time as t
 
@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
class LLAMA_Generator:
    def __init__(
        self,
        server_name: str,
        model_parameters: dict
    ):
        from icebreaker.llama.setup import llama_setup_model
        
        self.model = llama_setup_model(
            model_parameters = model_parameters
        )

        self.server_name = server_name
        self.n_gpu_layers = model_parameters['n-gpu-layers']
        self.serve_id = model_parameters['serve-id']
        self.n_ctx = model_parameters['n-ctx']
        self.type_k = model_parameters['type-k']
        self.type_v = model_parameters['type-v']
        self.flash_attention = model_parameters['flash-attention']
        model_repo_id = model_parameters['repo-id']
        model_filename = model_parameters['filename']
        self.model_name = f'{model_repo_id}|{model_filename}'
        
    def generate_output(
        self,
        request: dict
    ) -> any:
        from icebreaker.llama.use import llama_generate_output

        result = llama_generate_output(
            model = self.model,
            server_name = self.server_name,
            model_name = self.model_name,
            n_gpu_layers = self.n_gpu_layers,
            type_k = self.type_k,
            type_v = self.type_v,
            n_ctx = self.n_ctx,
            request = request
        )
            
        return result
