import ray
 
@ray.remote(
    num_cpus = 1,
    num_gpus = 0.5,
    memory = 0.8 * 1024 * 1024 * 1024
) 
class Assistant:
    def __init__(
        self,
        server_name: str,
        model_parameters: dict
    ):
        from icebreaker.llama.setup import llama_setup_model
        
        self.server_name = server_name
        self.n_gpu_layers = model_parameters['n-gpu-layers']
        self.n_ctx = model_parameters['n-ctx']
        self.type_k = model_parameters['type-k']
        self.type_v = model_parameters['type-v']
        self.flash_attention = model_parameters['flash-attention']
        model_repo_id = model_parameters['repo-id']
        model_file_name = model_parameters['file-name']
        self.model_name = f'{model_repo_id}|{model_file_name}'
        
        self.model = llama_setup_model(
            model_parameters = model_parameters
        )

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
