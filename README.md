# PenphinMind

## Overview

PenphinMind is an AI assistant that interfaces with the M5Stack LLM Module to provide a chat interface and model management capabilities. Running on Raspberry Pi, PenphinMind can plug into various devices to control them, with the first implementation being an arcade-style device called "Penphin" featuring a 64x64 RGB LED matrix display.

## Features

- Interactive menu system with the following options:
  - **Chat**: Start a conversation with the LLM model
  - **Configure**: View and select available models
  - **Reboot**: Reboot the M5Stack device
  - **Exit**: Exit the application

- Hardware information display at the top of the interface
- Model configuration and selection
- Real-time chat with LLM models
- Generative game creation and pixel art animation
- Visual identity animation on 64x64 LED matrix
- Futurama-inspired "What-If Machine" capabilities

## Hardware Components

- **Brain Language & Auditory Centers**: Utilizes AX630C device for speech processing
- **Visual Cortex**: 64x64 RGB LED matrix for visual output and animations
- **Auditory Output**: Configurable for local or device speakers (including Mac)
- **Core Processing**: Raspberry Pi connected to M5Stack LLM Module

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   For macOS specific dependencies:
   ```
   pip install -r requirements_macos.txt
   ```

## Usage

Run the application with:

```
python main.py --connection tcp
```

Connection options:
- `tcp`: Connect via WiFi (default)
- `serial`: Connect via Serial port
- `adb`: Connect via ADB

### Mind Modes

PenphinMind starts in full mode by default, but you can run specific brain regions for debugging or targeted functionality:

```
python run.py --mode fc
```

Available modes:
- `full`: Run the complete brain (default)
- `fc`: Frontal Cortex only - for working with just the LLM
- `ac`: Auditory Cortex only - for testing audio features
- `vc`: Visual Cortex only - for testing LED matrix
- `debug`: Enhanced debugging mode with verbose output

## Menu System

### Main Menu

The main menu provides the following options:

1. **Chat**: Start a conversation with the LLM
2. **Configure**: View and select available models
3. **Reboot**: Reboot the M5Stack device
4. **Exit**: Exit the application

### Chat Interface

In the chat interface:
- Type your message and press Enter to send
- Type 'exit' to return to the main menu
- Type 'reset' to reset the LLM

### Model Configuration

The Configure option allows you to:
1. View all available models on the local llm grouped by type
2. Select a model to view detailed information
3. Set a model as the active model for chat

## Hardware Information

Hardware information is displayed at the top of the interface, showing:
- CPU load
- Memory usage
- Temperature
- Last update timestamp

## Creative Capabilities

### Generative Pixel Art

PenphinMind can generate pixel art animations suitable for the 64x64 display:

- Converts prompts into visually appealing pixel art
- Optimizes images for LED matrix display
- Supports animation sequences
- Integrates with the OpenAI API for image generation

### Game Generation

The GameCortex module provides:

- Self-playing mini-games generated from text prompts
- Animation and visualization components
- Slot machine-like randomized game elements
- Cellular automata visualizations

### What-If Machine

Inspired by Futurama's "What-If Machine," this module allows PenphinMind to:

- Generate creative responses to hypothetical scenarios
- Visualize results through pixel art generation
- Create self-playing mini-games based on prompts
- Display results on the 64x64 LED matrix
  
## Brain-Inspired Architecture (2025 Refactor)

PenphinMind is structured to mirror biological cognition. It is built around the interaction between a central **Mind** and distributed processing across hemispheres and subcortices. The new structure enforces clarity, modularity, and neuro-symbolic metaphor:

### 🧠 Architectural Overview

```
/PenphinMind/
├── Interaction/           # Input/output interface
├── Mind/                  # Root mind controller and main loop
├───── LeftHemisphere/        # Logical and control cortices
├───── RightHemisphere/       # Creative and perceptual cortices
├───── Subcortices/           # Non-cortical regions (Basal Ganglia, Cerebellum)
├───── CorpusCallosum/        # Inter-hemispheric communication
```

### 🧭 Communication Flow

- `Interaction/` creates a `Mind` instance
- `Mind/` routes requests to:
  - A `Hemisphere` (Left or Right), or
  - The `CorpusCallosum` (if cross-talk or integration is needed)
- Each `Hemisphere` contains:
  - A `hemisphere_interface.py`
  - Cortex folders (e.g., `PrefrontalCortex/`, `GameCortex/`, `PsychicCortex/`, `SomatasensoryCortex/`, etc )
- Each cortex has:
  - `cortex_interface.py` (public entrypoint)
  - Internal submodules
- Cortex-to-cortex communication is **restricted to the same hemisphere**
- Cross-hemisphere calls must go through `CorpusCallosum`

### 📦 Cortex Organization

- **LeftHemisphere** → Logical control, Prefrontal, Language
- **RightHemisphere** → Visual, Creative, Emotional
- **Subcortices** → Motor control, reinforcement learning
- **CorpusCallosum** → Bridge logic and routing between hemispheres

### 🔄 Interfaces

- `mind.py` → Talks only to hemispheres or corpus
- `hemisphere_interface.py` → Talks only to cortices inside it
- `cortex_interface.py` → Handles all cortex-specific logic and delegates to submodules

### 🎮 GameCortex Structure

The `GameCortex` module implements:

```
/Mind/GameCortex/
├── base_module.py           # Base module for all game components 
├── game_manager.py          # Manages game state and interactions
├── Visualizers/             # Visual effects for the LED matrix
├── Slots/                   # Slot machine game components 
├── Automata/                # Cellular automata visualizations
```

All game modules inherit from `BaseModule` which properly manages:
- Animation state control
- Resource cleanup
- Frame timing
- Debug visualization

---

## Visual Identity

The project features an animated visualization that blends:

- 🔴 Red Dolphin (logical time)
- 🔵 Blue Penguin (intuitive depth)
- 🟣 Purple fusion symbolizing "Penphin Flow"
- 🟡 Gold-orange animated background with pulse effects
- 🎖 "PENPHINMIND" logo glowing beneath the emblem

This animation plays as a **boot-up identity sequence** on 64x64 LED displays using RGBMatrix.

## Project Structure
(TODO update strcuture for hemisphere refactor)
```
/PenphinMind/
├── Mind/                  # Primary brain processing
│   ├── OccipitalLobe/     # Visual processing
│   ├── TemporalLobe/      # Auditory processing
│   ├── GameCortex/        # Game generation
│   └── CorpusCallosum/    # Inter-module communication
├── Interaction/           # User interface components
├── api/                   # External API integrations
├── documentation/         # Project documentation
├── tests/                 # Test suite
└── requirements.txt       # Dependencies
```

---

## License

This project is licensed under the MIT License.
