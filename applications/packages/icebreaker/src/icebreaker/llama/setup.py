
def llama_setup_model(
    model_parameters: dict
):
    try:
        import time as t
        from llama_cpp import Llama
    except ImportError as e:
        raise ImportError(f'llama/setup failed to import: {e}')
    
    model = None
    if 0 < len(model_parameters):
        start_time = t.time()
        model_repo_id = model_parameters['repo-id']
        model_file_name = model_parameters['file-name']
        n_gpu_layers = model_parameters['n-gpu-layers']
        n_ctx = model_parameters['n-ctx']
        type_k = model_parameters['type-k']
        type_v = model_parameters['type-v']
        flash_attention = model_parameters['flash-attention']
        model_name = f'{model_repo_id}|{model_file_name}'
        print(f'Model configurations {n_gpu_layers}|{n_ctx}|{type_k}|{type_v}')
        print(f'Fetching and initializing {model_name} directly from Hugging Face Hub...')
        model = Llama.from_pretrained(
            repo_id = model_repo_id, 
            filename = model_file_name,                    
            n_gpu_layers = n_gpu_layers, 
            n_ctx = n_ctx,
            type_k = type_k,
            type_v = type_v,   
            flash_attn = flash_attention, 
            verbose = False
        )
        print('Model downloaded and successfully loaded into memory!')
        end_time = t.time()

        total_time = round(end_time-start_time,5)
        print(f'Spent seconds loading model: {total_time}')

    return model