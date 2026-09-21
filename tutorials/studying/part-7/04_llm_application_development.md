---
technologies: "LLM application development"
category: "Explanation and use of concept"
difficulty: "Intermediate"
---

# LLM application development

## Used material

1. <span id="used-material-1"></span> [Towards Vietnamese Question and Answer Generation: An Empirical Study](https://dl.acm.org/doi/10.1145/3675781)

2. <span id="used-material-2"></span> [AI-Assisted Code Authoring at Scale: Fine-Tuning, Deploying, and Mixed Methods Evaluation](https://dl.acm.org/doi/10.1145/3643774)

3. <span id="used-material-3"></span> [OpenAI Models](https://developers.openai.com/api/docs/models)

4. <span id="used-material-4"></span> [Self-Collaboration Code Generation via ChatGPT](https://dl.acm.org/doi/10.1145/3672459)

5. <span id="used-material-5"></span> [Introducing Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)

6. <span id="used-material-6"></span> [A survey on large language model (LLM) security and privacy: The Good, The Bad, and The Ugly](https://www.sciencedirect.com/science/article/pii/S266729522400014X?via%3Dihub)

7. <span id="used-material-7"></span> [AI Tools in Society: Impacts on Cognitive Offloading and the Future of Critical Thinking](https://www.mdpi.com/2075-4698/15/1/6)

8. <span id="used-material-8"></span> [Green MLOps to Green GenOps: An Empirical Study of Energy Consumption in Discriminative and Generative AI Operations](https://www.mdpi.com/2078-2489/16/4/281)

9. <span id="used-material-9"></span> [Unleashing the potential of prompt engineering for large language models](https://www.sciencedirect.com/science/article/pii/S2666389925001084)

10. <span id="used-material-10"></span> [Maximizing RAG efficiency: A comparative analysis of RAG methods](https://www.cambridge.org/core/journals/natural-language-processing/article/maximizing-rag-efficiency-a-comparative-analysis-of-rag-methods/D7B259BCD35586E04358DF06006E0A85)

11. <span id="used-material-11"></span> [Transformers in source code generation: A comprehensive survey](https://www.sciencedirect.com/science/article/abs/pii/S1383762124001309?via%3Dihub)

12. <span id="used-material-12"></span> [Ollama](https://ollama.com/)

13. <span id="used-material-13"></span> [Ray Serve: Scalable and Programmable Serving](https://docs.ray.io/en/latest/serve/index.html)

14. <span id="used-material-14"></span> [Large Language Model (LLM) for Telecommunications: A Comprehensive Survey on Principles, Key Techniques, and Opportunities](https://ieeexplore.ieee.org/document/10685369)

15. <span id="used-material-15"></span> [Magika](https://securityresearch.google/magika/introduction/overview/)

16. <span id="used-material-16"></span> [FastText](https://fasttext.cc/)

## What is LLM application development?

As we described in the [LLMOps chapter](./03_llmops.md), we need to consider the phases and best practices of LLMOps to create LLM applications for specific use cases. Based on them we can formulate the following considerations:

- Purpose:
    - Definition: What is the LLM expected to do?
    - Categories:
        - Search: LLM is expected to provide educational information 
            - Example: Question-answer LLM for Vietnamese [(1)](#used-material-1)
        - Solution: LLM is expected to use known knowledge to provide a working solution 
            - Example: Meta's code authoring tool CodeCompose [(2)](#used-material-2)
        - Dialog: LLM is expected to maintain long conversations that flexibly switch between search and solution assistance 
            - Example: OpenAI's conversational interface for their models [(3)](#used-material-3)
        - Collaboration: LLM is expected to take a specific area of responsibility with software and models 
            - Example: Developing software with LLM agents [(4)](#used-material-4)
    
- Utilization:
    - Definition: How is the LLM used?
    - Categories:
        - Modular: LLM is used by software for specific tasks
            - Example: Using LLM to provide further context for document chunks [(5)](#used-material-5)
        - Abstracted: LLM is integrated into software to handle triggered requests 
            - Example: LLM providing code snippets when user presses a key in IDE [(2)](#used-material-2)
        - Interactive: LLM responds directly to user inputs
            - Example: OpenAI's conversational interface for their models [(3)](#used-material-3)

- Experience [(2)](#used-material-2):
    - Definition: How is the LLM run?
    - Constraints:
        - Hardware selection:
            - Definition: What kind of GPUs will be used?
            - Types:
                - Access
                - Specification
                - Speed
                - Budget
                - Software
        - System design:
            - Definition: What kind of setup will be prepared?
            - Types:
                - Latency
                - Throughput
                - Development
        - Model selection:
            - Definition: What kind of models will be picked?
            - Types:
                - Access
                - Architecture
                - Ability
                - Size
                - Improvement
        - Utilization design:
            - Definition: What kind of interface will be built?
            - Types:
                - Granularity
                - Flow
                - Trust
                - Coexistance
                - Generalization
            
- Threats:
    - Security and privacy [(6)](#used-material-6):
        - Definition: What kinds of attacks and vulnerabilities do LLMs enable?
        - Attacks:
            - Types:
                - Hardware
                - Operating system
                - Software
                - Network
                - User-level
        - Vulnerabilities:
            - Groups:
                - AI inherent exploits:
                    - Adversarial
                    - Inference
                    - Extraction
                    - Instruction tuning
                    - Bias and unfairness 
                - Non-AI inherent exploits:
                    - Remote code execution
                    - Side-channel
                    - Supply-chain  
    - Cognitive [(7)](#used-material-7):
        - Definition: What kind of effects does the use of LLMs have on the user's cognitive abilities?
        - Considerations:
            - Delegation of tasks
            - Increased use of external tools
            - Perceived reliability 
            - Acquired convenience
            - Negative effects on critical thinking
            - Educational interventions
            - Cognitive costs
    - Environmental [(8)](#used-material-8):
        - Definition: What kind of effects does the use of LLMs have on energy and resource consumption?
        - Considerations:
            - Increased system complexity
            - Multiple model types, variants, and sizes
            - Simultaneous use of multiple models
            - Strategies for reducing energy and resource consumption
            - Balancing abilities vs. size
            - Model-appropriate requests per second
            - Multi-threaded inference framework

- Development:
    - Definition: What are the steps of creating an LLM application?
    - Steps:
        - Selecting a trained model: Choosing either a commercial model behind an API or an open-source model run on an inference framework 
        - Finding suitable data: Choosing either self-made or ready-made data
        - Enhancing the model: 
            - Prompt engineering (PE): Orienting model behavior with input design and optimization [(9)](#used-material-9)
            - Retrieval-augmented generation (RAG): Providing the model with relevant and up-to-date external knowledge sources [(10)](#used-material-10)
            - Fine-tuning (FT): Adjusting model parameters to improve its abilities in specific areas [(11)](#used-material-4)
            - Behavior control (BC): Enforcing user inputs and improving generated outputs toward specific quality guarantees [(6)](#used-material-6)
        - Deploying the model:
            - Out-of-the-box: Ollama [(12)](#used-material-12)
            - Abstracted self-implementation: Ray [(13)](#used-material-13)

- Evaluation [(14)](#used-material-14):
    - Types:
        - Manual vs automated metric range:
            - Example for manual metric: Human evaluator searching for problematic outputs
            - Example for automated metric: Hardware sensors monitoring energy consumption
        - Model vs concrete metric range:
            - Example of model metric: Match-based CodeBLEU aligned to human judgment
            - Example of concrete metric: Unit tests assessing output code 
    - Groups:
        - Accuracy: Measures the model's ability to understand and process queries, generate responses, and perform specific tasks using datasets and benchmarks
        - Hallucination: Measures the model's ability to provide correct and consistent information 
        - Alignment: Measures a model's ability to produce outputs in line with human values, preferences, and expectations
        - Efficiency: Measures the acquired performance relative to consumed resources such as compute, energy, speed, money, and hardware 

With this framework, we can list the necessary development requirements for our LLM application. We will use this to define the demonstration use case for our local-cloud-HPC MLOps platform. 
    
## How to do LLM application development?

The demonstration for the local-cloud-HPC MLOps platform will be a enhanced coding assistant that enables users to discuss all the tutorial material. The LLM development considerations are the following:

- Purpose:
    - Dialog: LLM coding assistant for discussing tutorial material
    - Collaboration: LLM for data generation, answer evaluation, and behavior control

- Utilization:
    - Modular: Functions utilizing the generators, evaluators, and controllers
    - Interactive: Using the coding assistant through Open WebUI via Istio

- Experience:
    - Hardware selection:
        - Access: Local, cloud, and HPC infrastructure
        - Specification: NVIDIA GPUs of P100 16GiB, RTX4070 8 GiB, RTX4090 16 GiB and GH200 96 GiB
        - Speed: Compute capability varies
        - Budget: Use of already-bought local hardware and MyCSC billing units for cloud, storage, and HPC platforms
        - Software: CUDA between 12.2 and 13.7 with container toolkit, NVIDIA GPU Operator, and NVshare for KinD
    - System design:
        - Latency: 
            - Data Generator: Max 60 sec
            - Answer evaluator: Max 2 sec
            - Behavior controller: Max 1 sec
            - Coding assistant: Max 5 sec
        - Throughput: 
            - Data Generator: Must be high due to the amount of data
            - Answer evaluator: Must be high due to the amount of data
            - Behavior controller: Can be low due to one per server
            - Coding assistant: Can be low due to lack of users
        - Development:
            - Critical software:
                - Docker
                - NVIDIA GPU Operator
                - NvShare
                - Ray 
                - llama-cpp
                - Open WebUI
                - LMod
                - SLURM
                - Apptainer
                - vLLM
            - Self-implemented:
                - Functions for interactions
                - Inference code
                - Model prompts
                - Data analysis of metrics
    - Model selection:
        - Access: Open-source LLMs with MIT, Apache-2.0, and Llama 3.1 licenses
        - Architecture: Near state-of-the-art multimodal architectures 
        - Ability: 
            - Data generator: Reasoning for generating data
            - Answer evaluator: Accuracy for judging based on scoring rubric
            - Behavior controller: Speed for judging based on set expectations
            - Coding assistant: Coding abilities for discussing tutorials
        - Size:
            - Data generator: 8B
            - Answer evaluator: 7-8B
            - Behavior controller: 0.8-2B
            - Coding assistant: 2-122B
        - Improvement:
            - Data generator: PE
            - Answer evaluator: PE
            - Behavior controller: PE
            - Coding assistant: PE-RAG-BC
    - Utilization design:
        - Granularity: Complete answer to a question based on material
        - Flow: Entering input, waiting for output, and creating another input
        - Trust: At least answers to enable searching for correct ones
        - Coexistence: Browser-based interface that works like commercial models  
        - Generalization: Atleast ability to discuss the material
    
- Threats:
    - Security and privacy:
        - Accidental AI-Inherent attack
            - Example: User accidentally gives credentials in the query
            - Counter: Input processing
        - Accidental AI-Inherent vulnerability
            - Example: Input makes model output gibberish
            - Counter: Output processing
    - Cognitive:
        - Problem: User might take the model's mistakes at face value due to convenience and long sessions
        - Counter: Educational intervention via an attached mistake reminder with used material, links, and files at the start of the output
    - Environmental
        - Problems:
            - Complexity of local-cloud-HPC MLOps platform consumes significant resources that are difficult to optimize
            - Demonstration will run multiple types of models with different architectures and sizes
         - Counters:
            - Suitable LLM quantization
            - Sending model-appropriate requests per second to maximize GPU utilization
            - Running models on vLLM when VRAM and CUDA compatibility make it possible
        
- Development
    1. Selecting a trained model:
        - Choose near-SOTA open-source models from HuggingFace in the 2-122B range that run either in llama-cpp or vLLM:
            - Data generator: 
                - unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF with Q4_K_M
            - Answer evaluator:
                - unsloth/Ministral-3-8B-Instruct-2512-GGUF with Q4_K_M
                - unsloth/gemma-4-E4B-it-GGUF with Q4_K_M
            - Behavior controller: 
                - unsloth/Qwen3.5-2B-GGUF with Q4_K_M
            - Coding assistant:    
                - Local-cloud
                    - unsloth/Qwen3.5-2B-GGUF with Q4_K_M
                    - unsloth/Qwen3.5-4B-GGUF with Q4_K_M
                    - unsloth/Qwen3.5-9B-GGUF with Q4_K_M
                - HPC
                    - Qwen/Qwen3.5-27B-FP8
                    - Qwen/Qwen3.5-35B-A3B-FP8
                    - Qwen/Qwen3.5-122B-A10B-FP8
    2. Finding suitable data:
        - Self-made internal data: 
            - Datasets:
                - 8 self-contained tutorial folders parsed into RAG documents
            - Formats: 
                - Markdown
                - Notebook
                - Python
                - Bash
                - YAML
                - Text
                - Env
        - Ready-made external data:
            - Open-source HuggingFace datasets with MIT, Apache-2.0 and cc-by-4.0 licenses:
            - Datasets:
                - openai-humaneval
                    - Formats:
                        - Python
                - mbpp
                    - Formats:
                        - Python
                - bash-command-data-6K
                    - Formats:
                        - Bash
                - opc-sft-stage1
                    - Formats:
                        - Markdown
                        - Python
                        - YAML
                        - Text
                - opc-sft-stage2
                    - Formats:
                        - Markdown
                        - Python
                        - YAML
                        - Text
    3. Enhancing the model:
        - PE: Provides output consistency for all models
        - RAG: Provides internal material to the coding assistant
            - Type: Hybrid distribution-based score fusion (DBSF)
            - Query limit: 5
            - Fusion limit: 20
            - Dense model: BAAI/bge-m3
            - Sparse model: prithivida/Splade_PP_en_v1
        - BC: Sanitizes input and output of the coding assistant 
    4. Deploying the model:
        - Ray Serve with llama-cpp or vLLM

- Evalution
    - Model:
        - Accuracy:
            - Correctness average: 
                - Type: Automated model metric via LLM-as-judge
                - Definition: Measures the model's ability to provide a correct solution
                - Value: Binary 0 or 1
        - Hallucination:
            - Relevance average:
                - Type: Automated model metric via LLM-as-judge
                - Definition: Measures the model's ability to maintain credibility
                - Value: Binary 0 or 1
        - Alignment:
            - Faithfulness average:
                - Type: Automated model metric via LLM-as-judge
                - Definition: Measures the model's ability to meet coding assistant expectations
                - Value: Binary 0 or 1 
        - Efficiency:
            - Average total inference latency:
                - Type: Automated concrete metric via time collection
                - Definition: Measures the average time between the model starting to process the input and finishing generating the final token
                - Value: Time in seconds
            - Average time per output token:
                - Type: Automated concrete metric via time collection
                - Definition: Measures the average time it takes for the model to generate a single token during output generation 
                - Value: Time in seconds
            - Avereage inference time to first token:
                - Type: Automated concrete metric via time collection
                - Definition: Measures the average time between the model starting the process of processing the input and generating the first token
                - Value: Time in seconds
            - Average inference tokens per second:
                - Type: Automated concrete metric via time collection
                - Definition: Measures the average time it takes for the model to generate all the tokens of the output
                - Value: Time in seconds
    - RAG:
        - Search:
            - Weighted grading: 
                - Definition: Each chunk from the tutorials is given a grade between 1 and 3
                    1. Least relevant
                    2. Secondary material referenced by primary material
                    3. Primary material
                - Use: Dictionary of chunk IDs with grade 
                - Effect: Retrieving chunks from the same relevant document, with chunks being primary documents, gets the highest score
            - Types:
                - Precision@1
                    - Type: Automated concrete metric via provided chunk ID comparison
                    - Definition: Measures if the single top-ranked retrieved document is relevant 
                    - Value: Binary 0 or 1
                    - Stats: Mean, std
                - Recall@3
                    - Type: Automated concrete metric via provided chunk ID comparison
                    - Definition: Measures the proporition of all existing relevant documents being succesfully retrieved in top 3 positions
                    - Value: Float of 0.0 to 1.0
                    - Stats: Mean, std
                - NDCG@3
                    - Type: Automated concrete metric via provided graded chunk ID comparison
                    - Definition: Measures ranking quality based on graded relevance and position penalty of top 3 documents
                    - Value: Float of 0.0 to 1.0
                    - Stats: Mean, std
                - NDCG@5
                    - Type: Automated concrete metric via provided graded chunk ID comparison
                    - Definition: Measures ranking quality based on graded relevance and position penalty of top 5 documents
                    - Value: Float of 0.0 to 1.0
                    - Stats: Mean, std
        - Latency:
            - Embedding dense model latency:
                - Type: Automated concrete metric via time collection
                - Definition: The time taken by dense model to create vector representation 
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
            - Embedding sparse model latency:
                - Type: Automated concrete metric via time collection
                - Definition: The time taken by sparse model to create vector representation
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
            - Embedding latency:
                - Type: Automated concrete metric via time collection
                - Definition: The time taken to convert a text query into vector representations using embedding models
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
            - Search dense model latency:
                - Type: Automated concrete metric via time collection
                - Definition: The time taken by dense model to create vector representation for query
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
            - Search sparse model latency:
                - Type: Automated concrete metric via time collection
                - Definition: The time taken by sparse model to create vector representation for query
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
            - Search latency:
                - Type: Automated concrete metric via time collection
                - Definition: The time spent querying database to find and retriev top-K most relevant document chunks
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
            - Total retrieval latency
                - Type: Automated concrete metric via time collection
                - Definition: The time spent between submitted query, receiving chunks and preparing them to be injected into LLM system prompt
                - Value: Time in milliseconds
                - Stats: Mean, median, p95, p99
        - Document:
            - Average characters per retrieval
                - Type: Automated concrete metric via character counting
                - Definition: The average amount of characters in the whole top-k query
                - Value: Mean, std, Min and Max

With these requirements and the lifecycle phases described in the [LLMOps chapter](./03_llmops.md), we can define the workflow stages of data analysis, data preprocessing, model evaluation, and solution analysis. 

In the data analysis stage, we will use a mix of basic and ML methods to gather category statistics such as formats using Magika [(15)](#used-material-15) and languages using FastText [(16)](#used-material-16) from internal and external datasets.

In the data processing stage, we will load the internal datasets into a RAG vector database, filter external datasets to create a 500-row general evaluation dataset, and use a data generator to produce a 500-row synthetic dataset consisting of factual, synthesis, and negative questions created from chunks of the internal datasets.

In the model evaluation, we will evaluate 6 different Qwen3.5 model sizes using 4 assistant variants. The compared model sizes are 2B, 4B, 9B, 27B, 35B, and 122B, with 2-9B in Unsloth GGUF Q4_K_M quantization and 27-122B in Qwen FP8 quantization. We compare the baseline, PE, PE-RAG, and PE-RAG-BC variants to assess their positive and negative effects.

In the solution analysis, we will evaluate the collected metrics with statistical methods and review artifacts manually to select the best model and variant. After that, we will confirm, through manual prompting, that the best model and variant behave as expected using a conversational interface. We will show later how to use the provided tools to implement this demonstration scenario.

---