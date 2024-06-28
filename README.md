# Kaiwa Subnet

KAIWA is a decentralized platform designed to simplify the process of running, fine-tuning, and deploying AI  models. Kaiwa provides user-friendly API, allowing users to integrate AI models with minimal coding and flexibility hardware resources.

## Why Kaiwa

The GPU can be prohibitively expensive for many developers, requiring payment even during idle periods. Leveraging the computing power of the Commune Subnet, Kaiwa offers AI Model inference services, significantly reducing the barrier of entry for AI app developers. These models can range from open-source offerings to those fine-tuned within the Commune Subnet.

## Validation

The Validator continually dispatches inference tasks to the miner while independently executing them for comparison, ensuring accurate execution of model tasks. Consistent output for identical inputs is achieved through fixed random seed settings, verifying model computation accuracy. This technique necessitates adherence to standardized data preprocessing, model architecture, and training procedures. Well-established AI models like Llama3 exemplify this consistency.

## Roadmap

**Phase 1: Run AI models on Commune subnet**
- We'll start by enabling open-source model inference for text-to-text tasks. Initially, we'll focus on models like Llama3 and Mixtrial 7b.
- To ensure accuracy, we'll check that miners produce the right results using fixed random seeds with the chosen model.
- We'll also integrate Portal and Gateway to streamline access to models and data from existing Commune subnet networks like Synthia, 0xScope, and Mosaic. 

**Phase 2: Serve for scenarios on Commune Subnet**
- As we add more models, we'll introduce a universal router to match users' budgets with the best model for their specific needs.
- To maintain quality, we'll enhance our validation process to check specific scenarios, ensuring accurate model results.
