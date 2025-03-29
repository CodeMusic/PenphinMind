# PenphinMind

## Overview

PenphinMind is an AI assistant that interfaces with the M5Stack LLM Module to provide a chat interface and model management capabilities.

## Features

- Interactive menu system with the following options:
  - **Chat**: Start a conversation with the LLM model
  - **Configure**: View and select available models
  - **Reboot**: Reboot the M5Stack device
  - **Exit**: Exit the application

- Hardware information display at the top of the interface
- Model configuration and selection
- Real-time chat with LLM models

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application with:

```
python main.py --connection wifi
```

Connection options:
- `wifi`: Connect via WiFi (default)
- `serial`: Connect via Serial port
- `adb`: Connect via ADB

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
1. View all available models grouped by type
2. Select a model to view detailed information
3. Set a model as the active model for chat

## Hardware Information

Hardware information is displayed at the top of the interface, showing:
- CPU load
- Memory usage
- Temperature
- Last update timestamp

## Development

The project follows a brain-inspired architecture with modules named after brain structures:

- **CorpusCallosum**: Communication pathways
- **FrontalLobe**: Decision making and control
- **Synaptic Pathways**: Network communication

## License

This project is licensed under the MIT License.
