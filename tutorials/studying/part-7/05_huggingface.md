---
technologies: "Huggingface"
category: "Explanation and use of technology"
difficulty: "Easy"
---

# Huggingface

## Used material

1. <span id="used-material-1"></span> [User access tokens](https://huggingface.co/docs/hub/security-tokens)

2. <span id="used-material-2"></span> [Datasets pip package](https://pypi.org/project/datasets/)

3. <span id="used-material-3"></span> [Huggingface datasets](https://huggingface.co/datasets)

4. <span id="used-material-4"></span> [openai/openai_humaneval](https://huggingface.co/datasets/openai/openai_humaneval)

5. <span id="used-material-5"></span> [google-research-datasets/mbpp](https://huggingface.co/datasets/google-research-datasets/mbpp)

6. <span id="used-material-6"></span> [emirkaanozdemr/bash_command_data_6K](https://huggingface.co/datasets/emirkaanozdemr/bash_command_data_6K)

7. <span id="used-material-7"></span> [OpenCoder-LLM/opc-sft-stage1](https://huggingface.co/datasets/OpenCoder-LLM/opc-sft-stage1)

8. <span id="used-material-8"></span> [OpenCoder-LLM/opc-sft-stage2](https://huggingface.co/datasets/OpenCoder-LLM/opc-sft-stage2)

9. <span id="used-material-9"></span> [Huggingface models](https://huggingface.co/models)

10. <span id="used-material-10"></span> [Deepseek-R1](https://huggingface.co/collections/deepseek-ai/deepseek-r1)

11. <span id="used-material-11"></span> [unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF](https://huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF/tree/main)

12. <span id="used-material-12"></span> [Qwen3.5](https://huggingface.co/collections/Qwen/qwen35)

13. <span id="used-material-13"></span> [unsloth/Qwen3.5-2B-GGUF](https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/tree/main)

14. <span id="used-material-14"></span> [unsloth/Qwen3.5-4B-GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/main)

15. <span id="used-material-15"></span> [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main)

16. <span id="used-material-16"></span> [Qwen/Qwen3.5-27B-FP8](https://huggingface.co/Qwen/Qwen3.5-27B-FP8/tree/main)

17. <span id="used-material-17"></span> [Qwen/Qwen3.5-35B-A3B-FP8](https://huggingface.co/Qwen/Qwen3.5-35B-A3B-FP8/tree/main)

18. <span id="used-material-18"></span> [Qwen/Qwen3.5-122B-A10B-FP8](https://huggingface.co/Qwen/Qwen3.5-122B-A10B-FP8/tree/main)

19. <span id="used-material-19"></span> [Ministral 3](https://huggingface.co/collections/mistralai/ministral-3)

20. <span id="used-material-20"></span> [unsloth/Ministral-3-8B-Instruct-2512-GGUF](https://huggingface.co/unsloth/Ministral-3-8B-Instruct-2512-GGUF/tree/main)
 
21. <span id="used-material-21"></span> [Gemma 4](https://huggingface.co/collections/google/gemma-4)

22. <span id="used-material-22"></span> [unsloth/gemma-4-E4B-it-GGUF](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/tree/main)

## Why use Huggingface?

Hugging Face is the default open-source dataset and LLM ecosystem for the following reasons:

- Provides an industry-standard hub for models and datasets with production-grade tools and straightforward model compliance and data governance (mature)

- Easy-to-use API for running different model architectures, dataset streaming, and hardware-agnostic model configuration (abstracted)

- Widely supported by tools for cross-compatibility with standardized formats and seamless downstream exports (interoperable)

These features make HuggingFace the default dataset and model hub for our local-cloud-HPC workflows. We will use it to get external datasets for general evaluation and load models to be run via suitable inference frameworks. 

## How to use Huggingface?

Assuming you have already created a HuggingFace account, begin by creating a user access token [(1)](#used-material-1) with the following fine-grained custom permissions: read contents of your repos, read contents of public gated repos you can access, and read your collections. Put the token into your $USER/.ssh/.env file with the key HF_TOKEN to enable loading it with:

```
from decouple import Config,RepositoryEnv
env_path = '/home/(your-user)/.ssh/.env'
env_dict = Config(RepositoryEnv(env_path))
hf_token = env_dict.get('HF_TOKEN')
```

Be aware that even though this token only has read permissions, you should still double-check for accidental leaks. The main concerns are Jupyter Notebook prints, code debug prints, and Ray script logs. Remember to double-check at least these sources for exposed tokens before sending files to a public GitHub repository. With the token, we can start to use the Datasets Package [(2)](#used-material-2) to download the external datasets from Hugging Face Datasets [(3)](#used-material-3) mentioned in [LLM application development chapter](./04_llm_application_development.md):

- Openai/openai_humaneval [(3)](#used-material-3):
    - Columns:
        - task_id
        - prompt
        - canonical_solution
        - test
        - entry_point
    - Rows: 164
- Google-research-datasets/mbpp [(4)](#used-material-4):
    - Columns:
        - task_id
        - text
        - code
        - test_list
        - test_setup_code
        - challenge_test_list
    - Rows: 974
- Emirkaanozdemr/bash_command_data_6K [(5)](#used-material-5):
    - Columns:
        - prompt
        - completion
    - Rows: 6150
- OpenCoder-LLM/opc-sft-stage1 [(6)](#used-material-6):
    - Columns:
        - instruction
        - output
        - tag
    - Rows:
        - Filtered_infinity_instruct = 1.03M rows -> 1 027 064 rows
        - Largescale_diverse_instruct = 2.51M rows -> 2 513 420 
        - Realuser_instruct = 676K rows -> 675 837
- OpenCoder-LLM/opc-sft-stage2 [(7)](#used-material-7):
    - Columns:
        - seq_id 
        - instruction
        - output
        - code
        - entry point
        - testcase
        - tag
    - Subsets:
        - educational_instruct = 118k rows -> 118 278 rows
        - evol_instruct = 111K rows -> 111 183
        - mceval_instruct = 35.9K rows -> 35 943
        - package_instruct = 171K rows -> 170 943

These datasets collectively result in 4,659,956 rows, with OpenCoder-LLM/opc-sft-stage1 and OpenCoder-LLM/opc-sft-stage2 requiring splitting into smaller tables of 20,000 rows. We can process the openai_humaneval, mbpp, and bash_command_data_6K in the following ways:

```
from datasets import load_dataset
import pandas as pd

evaluation_dataset_1 = load_dataset(
    'openai/openai_humaneval', 
    '',
    split = 'test',
    streaming = False,
    token = hf_token
)

evaluation_df_1 = pd.DataFrame(evaluation_dataset_1)
formatted_df_1 = evaluation_df_1.filter(['prompt','canonical_solution']).rename(columns = {
    'prompt': 'question',
    'canonical_solution': 'answer'
})

formatted_df_1.to_parquet('material/openai-humaneval.parquet', engine = 'pyarrow')

evaluation_dataset_2 = load_dataset(
    'google-research-datasets/mbpp', 
    'full',
    streaming = False,
    token = hf_token
)

formatted_df_2 = pd.concat([
    evaluation_dataset_2['train'].to_pandas(),
    evaluation_dataset_2['test'].to_pandas(), 
    evaluation_dataset_2['validation'].to_pandas(), 
    evaluation_dataset_2['prompt'].to_pandas()
])

formatted_df_2 = formatted_df_2.filter(['text','code']).rename(columns = {
    'text': 'question',
    'code': 'answer'
})

formatted_df_2.to_parquet('material/mbpp.parquet', engine = 'pyarrow')

evaluation_dataset_3 = load_dataset(
    'emirkaanozdemr/bash_command_data_6K',
    streaming = False,
    token = hf_token
)

formatted_df_3 = evaluation_dataset_3['train'].to_pandas().rename(columns = {
    'prompt': 'question',
    'completion': 'answer'
})

formatted_df_3.to_parquet('material/bash-command-data.parquet', engine = 'pyarrow')
```

In the case of OpenCoder-LLM/opc-sft-stage1 and OpenCoder-LLM/opc-sft-stage2 we need to utilize Dask mentioned in [Pandas chapter](../part-5/03_pandas.md) via the following function:

```
from icebreaker.setup.processing import processing_save_data

evalution_dataset_4/5/6_total_time = processing_save_data(
    dataset_repository = 'OpenCoder-LLM/opc-sft-stage1',
    dataset_name = 'filtered_infinity_instruct/largescale_diverse_instruct/realuser_instruct',
    hf_token = hf_token,
    table_size = 20000,
    size_limit = 1500000/2600000/680000,
    relevant_columns = [
        'instruction',
        'output'
    ],
    renamed_columns = {
        'instruction': 'question',
        'output': 'answer'
    },
    target_directory = 'material'
)

evalution_dataset_7/8/9/10_total_time = processing_save_data(
    dataset_repository = 'OpenCoder-LLM/opc-sft-stage2',
    dataset_name = 'educational_instruct/evol_instruct/mceval_instruct/package_instruct',
    hf_token = hf_token,
    table_size = 20000,
    size_limit = 119000/112000/36000/172000,
    relevant_columns = [
        'instruction',
        'output'
    ],
    renamed_columns = {
        'instruction': 'question',
        'output': 'answer'
    },
    target_directory = 'material'
)
```

We can store the external data into Allas with the following function:

```
from icebreaker.setup.experiment import experiment_store_data

total_storage_time = experiment_store_data(
    storage_client = setup_swift_client,
    file_parameters = {
        'bucket-target': 'experiment',
        'bucket-prefix': 'mlch',
        'bucket-user': 'user@example.com',
        'data-source': 'material'
    },
    data_type = 'external'
)
```

With this, we are now able to use the functions mentioned in [SWIFT chapter](../part-5/04_swift.md) to interact with these datasets by loading them into available RAM. For models, we will let inference frameworks handle downloading and loading by providing the token until download sizes get too large or constraints make it hard for the inference frameworks to manage the file system, which we will cover later. 

For this reason, we will primarily use Hugging Face Models [(9)](#used-material-9) to check model family collections for available variants and find a suitable quantization for running them. The collections, variants quantizations of the models mentioned [LLM application development chapter](./04_llm_application_development.md) are:

- Collection: DeepSeek-R1 [(10)](#used-material-10)
    - Variant: deepseek-ai/DeepSeek-R1-Distill-Llama-8B 
    - Quantization: 
        - unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF-Q4_K_M.gguf [(11)](#used-material-11)
    - Reason: Good reasoning, summary and coding abilities for the size for producing synthetic data
- Collection: Qwen3.5 [(12)](#used-material-12)
    - Variant: Qwen/Qwen3.5 with sizes from 2B to 122B
    - Quantization: 
        - unsloth/Qwen3.5-2B-GGUF-Q4_K_M.gguf [(13)](#used-material-13)
        - unsloth/Qwen3.5-4B-GGUF-Q4_K_M.gguf [(14)](#used-material-14)
        - unsloth/Qwen3.5-9B-GGUF-Q4_K_M.gguf [(15)](#used-material-15)
        - Qwen/Qwen3.5-27B-FP8 [(16)](#used-material-16)
        - Qwen/Qwen3.5-35B-A3B-FP8 [(17)](#used-material-17)
        - Qwen/Qwen3.5-122B-A10B-FP8 [(18)](#used-material-18)
    - Reason: Good coding and discussion abilities with large variety to be a coding assistant and behavior controller
- Collection: Ministral 3 [(19)](#used-material-19)
    - Variant: mistralai/Ministral-3-8B-Instruct-2512
    - Quantization:
        - unsloth/Ministral-3-8B-Instruct-2512-GGUF-Q4_K_M.gguf [(20)](#used-material-20)
    - Reason: Good summary and coding abilities for size to judge document and code answers
- Collection: Gemma 4 [(21)](#used-material-21)
    - Variant: google/gemma-4-E4B-it
    - Quantization:
        - unsloth/gemma-4-E4B-it-GGUF [(22)](#used-material-22)
    - Reason: Good summary and coding abilities for size to judge document and code answers

These models enable incremental development within the constraints of local-cloud infrastructure, while allowing us to increase assistant size with HPC infrastructure to confirm whether increasing model size affects the abilities of coding assistance. The small sizes of the data generator, behavior controller, and answer evaluators also let us run multiple models on the same GPU, which we will use for parallelized workflows later.

---