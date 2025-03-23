# PenphinOS (RoverAI Inception) - Bicameral Mind AI Implementation

## Overview
This project is a **fork of the Rover Project**, designed to integrate both **local AI (DeepSeek)** and **cloud-based AI (OpenAI)** into an evolving autonomous system. The local model will **train on inputs and refine output accuracy**, eventually enabling it to become more self-directed. The OpenAI component will assist with **higher-level reasoning and complex problem-solving**.

## Key Features
- **Dual AI System**: Local AI (DeepSeek) + OpenAI for reasoning.
- **Bicameral Mind Implementation**:
  - **Left-Brained AI** → Logical, bottom-up processing.
  - **Right-Brained AI** → Creative, top-down processing.
  - Both perspectives generate responses and consolidate for decision-making.
- **Training & Learning Mechanism**:
  - Redmine tracks **songs learned, teaching processes, and important insights**.
  - AI **trains overnight**, updating its model and improving decision-making.
  - Over time, the AI becomes **more autonomous** based on learned patterns.
- **Meta-Programming GPT-Like System**:
  - Implements **custom GPTs** to generate unique viewpoints.
  - Designed for **self-improving feedback loops**.
- **Adaptive Behavior**:
  - Uses **context-based learning** to enhance predictions.
  - Tracks historical performance for **long-term growth**.

## Installation & Setup
1. **Clone the Repository**
   ```sh
   git clone https://github.com/yourusername/PenphinOS.git
   cd PenphinOS
   ```
2. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure Redmine API** (for tracking training & progress)
   ```sh
   export REDMINE_API_KEY=your_api_key
   ```
4. **Run the Assistant**
   ```sh
   python penphinos.py
   ```

## Training Workflow
- **Real-time interaction with local AI (DeepSeek)**
- **High-level queries processed via OpenAI**
- **Nightly training cycle** to refine the model
- **Tracking progress via Redmine**

## Initial Commit Notes
- **Forked from the Rover Project**
- Integrated **DeepSeek for local AI learning**
- Established **Bicameral AI architecture**
- Implemented **meta-programming-based perspectives** for logical & creative responses
- Connected to **Redmine for tracking training data**

## Future Enhancements
- Improve **long-term memory and contextual reasoning**
- Integrate **advanced reinforcement learning techniques**
- Expand **the number of meta-programmed perspectives**

🎭 *This project is designed to balance structured reasoning with pattern-driven learning, enabling an adaptive and evolving AI assistant!* 🚀
