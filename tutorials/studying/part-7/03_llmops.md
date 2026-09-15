---
technologies: "LLMOps"
category: "Explanation and use of concept"
difficulty: "Intermediate"
---

# LLMOps

## Used material

1. <span id="used-material-1"></span> [Transitioning from MLOps to LLMOps: Navigating the Unique Challenges of Large Language Models ](https://www.mdpi.com/2078-2489/16/2/87)

## Why use LLMOps?

Large language model operations (LLMOps) is an iteration paradigm from MLOps that specializes in implementing Generative AI, especially LLMs, in practical applications. LLMOps utilizes the following life cycle [(1)](#used-material-1) and best practices:

- Lifecycle phases:
    - Discover: Define the problem, constraints, data, and goals of the use case
    - Distill: Develop the use case system, model, and behavior 
    - Deploy: Prepare the system, model, and behavior for a production application
    - Deliver: Monitor the application and use the data to iterate its components

- Best practices:
    1. Data management
    2. Model training and fine-tuning
    3. Infrastructure and scalability
    4. Monitoring and observability
    5. Security and compliance
    6. Inference optimization
    7. Continuous Integration / Continuous Deployment
    8. Collaboration and documentation
    9. Human-in-the-loop
    10. Ethical considerations

With these, we can begin planning how to use the local-cloud-HPC integrated MLOps platform to demonstrate an LLM application.

## How use LLMOps?

LLMOps practices are very similar to those described in the [MLOps chapter](../part-1/01_mlops.md), with the difference being a focus on large amounts of data, GenAI models, improving LLM behavior, and handling inference challenges. However, because we focus on integration, we will mainly pick the relevant practices for implementing the demonstration, which we will cover in more detail later. 

---