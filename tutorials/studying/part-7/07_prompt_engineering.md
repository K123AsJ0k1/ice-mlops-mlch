---
technologies: "Prompt engineering"
category: "Explanation and use of concept"
difficulty: "Intermediate"
---

# Prompt engineering

## Used material

1. <span id="used-material-1"></span> [Unleashing the potential of prompt engineering for large language models](https://www.sciencedirect.com/science/article/pii/S2666389925001084)

## Why use Prompt engineering?

Prompt engineering is the systematic design and optimization of input prompts to ensure high accuracy, relevance, coherence, and usability of the generated LLM outputs [(1)](#used-material-1). The prompt engineering methodologies used are the following:

- Basic methods:
    - Providing instructions:
        - Definition: Providing directives to guide the behavior and output of a model 
            - Ensures the model handles tasks as intended by avoiding ambiguity and misinterpretations
            - Poorly designed or overly general instructions can create outputs that lack specificity and relevance
    - Being clear and precise:
        - Definition: Providing clean and precise instructions to guide the model to generate accurate and relevant output
            - Reduces the range of possible interpretations via unambiguous and specific prompts to narrow the response space and align output with goals
    - Role-based prompting:
        - Role prompting:
            - Definition: Assign a role to make the model generate outputs with contextual accuracy and task-specific precision
                - Enables consistent output aligned with predefined roles
        - Role-play prompting:
            - Definition: The model is allowed to adjust across multiple-turn interactions
                - Enables models to evolve based on user input
    - Use of delimiters for separation:
        - Definition: Use of triple quotes or custom symbols to separate different parts of a prompt or encapsulate multi-line strings
            - Enables addressing complex prompts with multiple components by making the model accurately interpret and differentiate various input elements
            - Reduces the risk of prompt injection attacks as user input is treated strictly as data
    - Trying several times:
        - Definition: Generating multiple responses for the same prompt
            - Enables selecting the best output with predefined criteria
    - One-shot or few-shot prompting:
        - Definition: Giving either a single example or multiple examples to learn from in the prompt
            - Provides additional context and guidance to improve model performance
            - One- or few-shot depends on task complexity and capabilities of the model
            - There are some scenarios where not having examples is better
    - Temperature and top-p:
        - Definition: Configuring model temperature and top-p values to fit the task
            - Temperature and top-p control the randomness of the output
            - They significantly affect the quality and diversity of the outputs

- Advanced methods:
    - Chain-of-thought prompting:
        - Zero-shot chain-of-thought prompting:
            - Definition: Augmenting prompts with 'Let us think step by step'
                - Assumes that the model would benefit from having detailed and logical steps
                - Benefiting models show improvement in logical coherence and comprehensiveness 
        - Golden chain-of-thought method:
            - Definition: Adding a set of ground-truth CoT solutions into the prompt
                - Increases the accuracy of the model
                - Is limited due to the requirement for ground-truth CoT solutions
    - Self-consistency:
        - Definition: Generating multiple reasoning paths to evaluate and marginalize them into a final answer that reflects these reasoning paths
            - Can enhance abilities in arithmetic, commonsense, and symbolic reasoning tasks
            - Can help models overcome limitations with proof planning and selection of appropriate proof steps
            - Can be combined with CoT to get guided CoT reasoning with a correctness discriminator to enhance reasoning abilities 
    - Generated knowledge:
        - Definition: Using a model to generate potentially useful information before generating the final response
            - Effective for tasks that require commonsense reasoning via additional context not necessarily found in the prompt
    - Least-to-most prompting:
        - Definition: Breaking down a complex problem into smaller subproblems
            - Assumes that it is possible to break down sophisticated tasks into manageable components systematically
            - Effective approach for complex problems in various domains
    - Tree of thoughts:
        - Definition: Enabling a model to explore reasoning paths with the ability to look ahead, backtrack, and self-evaluate
            - Can make models more flexible and adaptable for complex tasks
            - Enhances models by making their thought processes structured
    - Graph of thoughts:
        - Definition: Model thoughts are used to build a detailed graph that is analyzed to get a precise, multifaceted answer
            - Generalization of CoT and ToT methods
            - Graph vertices are individual units of information, and edges are dependencies between them
            - Enables different graph traversal methods for solution construction
            - Can be used to solve complex challenges
    - Decomposed prompting:
        - Definition: Breaking down a complex task into manageable subtasks that are processed by specialized handlers
            - Modular extension of the least-to-most method
            - Consists of 4 components: Decomposer model, prompting program, sub-task handlers, and imperative controller
            - Prompting program consisting of simpler subqueries and subtask functions
            - Imperative controller for managing execution of the program that passes inputs and outputs between decomposer and subtask handlers
            - Provides modularity of handlers, error-correction subtask handlers, diverse decomposition, and subtask handlers can be shared between different tasks
            - Enables a more flexible and modular approach than least-to-most
            - Allows nonlinear and recursive decomposition with dedicated handlers that can be optimized and replaced
            - Superior performance in specific domains such as symbolic reasoning and multistep questions 
    - Active prompting:
        - Definition: Provides systematically selected and annotated questions with CoT reasoning
            - Focused on improving reasoning capabilities
            - Generated multiple predictions for each question to gather uncertainty metrics
            - Can be combined with the self-consistency method for better reliability
            - Can be used to identify the most efficient one-shot or few-shot examples in specific domains
    - Prompt pattern catalog:
        - Definition: An organized collection of prompt templates and patterns for systematically simplifying prompt engineering
            - Standardized set of prompts applied to various tasks to ensure consistency and reduce variability and errors
            - Enables saving time and resources, while enabling models to adapt to new tasks and domains
            - Requires conceptualization and design of prompt patterns with proper structure and documentation
            - Five primary categories: input semantics, output customization, error identification, prompt improvement, and interactions
    - Prompt optimization:
        - Prompt optimization with textual gradients (ProTeGi):
            - Definition: Using textual gradients to adjust a prompt to get the desired task performance
                - Uses an iterative approach with beam search and bandit selection to explore potential prompts and select promising candidates
                - Shows strong performance in different natural language processing tasks without needing access to internal LLM workings
        - Black-box prompt optimization (BPO):
            - Definition: Training a sequence-to-sequence model using feedback-based prompt pairs to enhance alignment between prompts and expectations iteratively
                - Enables fixing prompts to get more comprehensive responses to achieve expected depth and relevance
                - Is agnostic and applicable across models without needing model internals
                - Is interpretable with transparent and observable prompt modifications
                - Can outperform RLHF and DPO across various models
                - Can complement other methods to improve outcomes
        - Model-adaptive prompt optimization (MAPO):
            - Definition: Fine-tuning prompts to the specifics of individual models
                - Uses a two-phase optimization process with a warm-up dataset and combined supervised fine-tuning and reinforcement learning
                - Can provide significant performance in QA, classification, and text generation
        - PromptAgent:
            - Definition: Using Monte Carlo tree search to enable self-reflective trial-and-error search of expert-level prompts
                - Iteratively refines prompts using error feedback to simulate and prioritize high-reward paths
                - Performs well across general NLP challenges and specialized domains with precise terminology
        - Reinforcement learning (RL):
            - Definition: Using RL principles to explore parameter spaces and optimize prompts to get task-specific performance
                - The reward function uses the effectiveness of the prompt based on model output
                - The feedback is used to adjust and optimize the prompts through iterations
                - The used model can learn to generate better prompts for similar questions in the future
        - GPTs (plugins):
            - Definition: External prompt engineering assistant
                - They analyze user inputs and produce pertinent outputs within a self-defined context 
                - Reduce the effort required to create your own prompts
                - Can be integrated into Python and invoked directly
                - Their closed-source nature makes it unclear what methods are implemented
    - Retrieval augmentation:
        - Definition: Incorporating up-to-date external knowledge into the input to reduce hallucinations
            - Makes the model less inconsistent with facts 
            - Enables real-world data support
            - Has many variations
    - Reasoning and active interaction:
        - Automatic reasoning and tool usage (ART):
            - Definition: Encourages the generation of reasoning steps with strategic use of external tools
                - Combines the principles of CoT
                - Enables tasks that require precise calculations, updated information, and complex data processing 
                - Valuable for technical problem-solving tasks such as financial calculations and data analysis
        - Reasoning and acting framework (ReAct):
            - Definition: Prompting a model to generate reasoning traces and task-specific actions
                - Uses a dual approach to make the model consider the problem, divide the reasoning sequence, and execute actions with tools
                - Effective in scenarios that require detailed reasoning followed by specific actions
                - Provides more robust and reliable outcomes than static prompts alone
                - Is not trivial to implement as it requires detailed understanding and available tools
        
- Multimodal methods:
    - Zero-shot and few-shot prompting:
        - Definition: Giving either a single example or multiple examples to learn from multimodal input
            - Enables multimodal models to handle new tasks with minimal or no task-specific training
            - Can be used for multimodal classification tasks
    - Continuous prompt vectors:
        - Definition: Using prompt vectors to fine-tune models for complex video understanding tasks
            - Continuous prompt vectors are learned during training
            - Involves appending or prepending sequences of random vectors to the input text
            - The vectors bridge the gap between static image-based pretraining and the dynamic requirements of video tasks
            - The method has competitive performance with few parameters trained, while providing flexibility and accuracy 
    - Context optimization (CoOp):
        - Definition: Use of embedded context vectors in the architecture of the model and fine-tuned to minimize classification loss
            - Enables better performance and generalizability in different scenarios
            - The method is very valuable in scenarios where context can vary significantly
    - Conditional context optimization (CoCoOp):
        - Definition: Using a lightweight neural network to create input-conditioned prompt vectors for each image without modifying the used model
            - Enables the model to adapt to new and unseen data without needing to fine-tune
            - Addresses the limitations of static prompt methods such as CoOp
    - Multimodal prompt learning (MaPLe):
        - Definition: Embedding prompts within the stages of transformer architecture to adaptively learn task-specific contextual information 
            - Uses a hierarchical learning mechanism to enable the model to process and integrate information at different abstraction levels
            - Shown to outperform CoCoOp
            - Enables fine-tuning the model to address both the visual context and textual question
            - Hierarchical processing enables integrating the visual cuses with textual context to provide accurate answer

- Assessment methods:
    - Subjective and objective evaluations:
        - Subjective evaluations:
            - Definition: Using human evaluators to check the quality of generated content
                - Usually done by reading and scoring the generated text
                - Includes aspects such as fluency, accuracy, novelty, and relevance
                - An example is the HuggingFace Chatbot Arena Leaderboard
                - Enables linking subjective evaluations to measures user-driven metrics
                - Used in areas that are difficult to represent with datasets and are abstract
        - Objective evaluations:
            - Definition: Using algorithms to evaluate the quality of generated content or conducting tests with various benchmarks
                - Usually done with different evaluation metrics
                - AN example is ROUGE, which assesses the similarity between output text and reference text
                - Automated metrics often do not fully capture the results of human evaluators and should be used with caution
                - There are four types of benchmarks: Math word problems, QA tasks, Language understanding tasks, and multimodal tasks
                - Math word problems test models' ability to understand number-related questions
                - QA tasks expect models to return feedback based on the given question
                - Language understanding tasks require solving language understanding and inductive tasks
                - Multimodal tasks evaluate MMLM ability to process and integrate information from multiple modalities such as text and images

- Improved applications:
     - Assessments ot teaching and learning:
        - Definition: Using PE to create personalized learning environments, plan education, and automate grading in educational scenarios
            - Enables models to adapt to the learning pace and style of individuals with specific learning needs
            - Can be used to create rubrics or guidelines for courses
            - Automating preliminary assessments to reduce workload and provide instant feedback to students
            - Analyzing gathered data to provide insights regarding learning patterns and informing about areas that require attention and improvement
    - Content creation and editing:
        - Definition: Using PE to enable dynamic and controlled creation and editing of multimodal media
            - Has been used for cross-lingual short stories and extending stories
    - Computer programming:
        - Definition: Using PE to enable the generation of better code
            - Has been used for self-debugging, multistep, and prompt optimization 
    - Reasoning tasks:
        - Definition: Using PE to enable solving complex problems wth reasoning steps
            - Has been used for various word-based math benchmarks
            - Few-shot prompts, self-talk, and CoT encourage the model to verbalize reasoning steps
            - Properly customized prompts can obtain better results 
    - Dataset generation:
        - Definition: Using PE to make the model generate synthetic datasets 
            - Can be used for unlabeled data annotation, training data generation, and assisted training data generation
            - Has been used for synthetic data for classification tasks
    - Agents:
        - AI Agents:
            - Definition: Using PE to improve the abilities of task-oriented agent systems 
                - Focus on concrete applications and predefined functionalities
                - Providing effective task decomposition and tool invocation processes
                - Enables the utilization of external tools such as internet searching, code execution, and third-party software integration
                - PE methods enhance adaptability, robustness, and real-world utility of task-specific AI agents
        - Agent AI:
            - Definition: Using PE to guide interactions to synergize generalized agent systems
                - Emphasize adaptive multimodal reasoning in complex environments
                - Providing orchestration of multimodal inputs, continuous adaptation, and strategic planning for increased flexibility and capability
                - Enabled by integrating large-scale models, memory systems, planning algorithms, and tool interfaces
                - Consists of five perspectives: models, prompt templates, chains, agents, and multi-agents
                - Models provide linguistic and reasoning substrates
                - Prompt templates standardize input structures to align outputs closely with targeted objectives
                - Chains, agents, and multi-agents create more complex multi-agent ecosystems where autonomous systems collaborate
                - PE is the central component for shaping interpretative fidelity, guiding strategic adjustments, and self-regulation in dynamic and uncertain environments 

- Security methods:
    - Training phase defenses and mitigations:
        - Data poisoning: 
            - Definition: Injecting malicious or misleading data into the corpus to corrupt model knowledge 
                - Requires ensuring the quality and authenticity of the training data corpus
                - Main approaches are data sanitization and filtering, certified defenses, and robust training algorithms
        - Backdoor attacks: 
            - Definition: Embedding hidden vulnerabilities during the training phase to activate later during inference with specific triggers
                - Requires detecting and neutralizing triggers embedded during training
                - Main approaches are model inspection and trigger detection methods, and model auditing and model editing techniques
        - A general defense against both is data quality assurance, robust optimization, model auditing, and community benchmarks
    - Inference-phase defenses and mitigations:
        - Prompt-level adversarial attacks:
            - Definition: Injecting textual cues into the input to make the model produce undesired or misleading output without alerting the parameters
        - Model stealing:
            - Definition: Using PE to replicate functionality or extract proprietary knowledge from the model
        - General defenses against both are prompt validation, sanitation techniques, content moderation, alignment reinforcement schemes, adversarial training, and access control measures 

With this framework, we can list the necessary design requirements when creating prompts for different models and specific tasks in our LLM applications. We will use this to produce prompts for our demonstration use case. 

## How to use Prompt engineering?

As described in the [LLM application development chapter](./04_llm_application_development.md), the demonstration use-case application will require a data generator, coding assistant, behavior controller, and answer evaluator models. We can achieve this with suitable prompt engineering for the models chosen for these roles. The YAML-based prompts for the roles are as follows:

- Data generator:
    - Model: DeepSeek-R1-Distill-Llama-8B-GGUF with Q4_K_M
    - Task: Producing factual, synthesis, and negative QA pairs
    - [Used PE methods](./prompts/data-generator-prompts.yaml)
        - Providing instructions
        - Being clear and precise
        - Role prompting
        - Use of delimiters for separation
        - Few-shot prompting
        - Temperature and top-p

- Coding assistant:
    - Model: Qwen3.5-(2-122)B-GGUF with Q4_K_M/FP8
    - Task: Assisting developers with searching for knowledge, providing solutions, and discussing information and solutions
    - [Used PE methods](./prompts/coding-assistant-prompts.yaml)
        - Providing instructions
        - Being clear and precise
        - Role prompting
        - Use of delimiters for separation
        - Temperature and top-p
        - Retrieval augmentation

- Behavior controller:
    - Qwen3.5-2B-GGUF with Q4_K_M
    - Task: Checking user inputs and model outputs
    - [Used PE methods](./prompts/behavior-controller-prompts.yaml)
        - Providing instructions
        - Being clear and precise
        - Role prompting
        - Use of delimiters for separation
        - Few-shot prompting
        - Temperature and top-p

- Answer evaluator:
    - Ministral-3-8B-Instruct-2512-GGUF and Gemma-4-E4B-it-GGUF with Q4_K_M
    - Task: Evaluating the given candidate answer against the ground truth and the user question
    - [Used PE methods](./prompts/answer-evaluator-prompts.yaml)
        - Providing instructions
        - Being clear and precise
        - Role prompting
        - Use of delimiters for separation
        - Temperature and top-p

With these prompts, we can use the chosen models consistently to complete the expected tasks. We only need to replace the place holders with suitable text, sent the created prompt to be processed and preprocess the produced output. 
    
---