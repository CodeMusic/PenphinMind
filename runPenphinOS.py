import time
from AuditoryCortex.speech_manager import SpeechManager
from AuditoryCortex.audio_manager import AudioManager
from SomatosensoryCortex.button_manager import ButtonManager
from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import NeuralCommands
#from CorpusCallosum.redmine_manager import RedmineManager

def cleanup():
    """
    Cleanup system resources
    """
    try:
        SynapticPathways.close_connections()
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    # Initialize managers
    auditory_cortex = None
    audio_cortex = AudioManager()
    somatosensory_cortex = ButtonManager()
    #redmine_system = RedmineManager()

    try:
        while True:
            try:
                if not auditory_cortex:
                    auditory_cortex = SpeechManager()
                    # Register managers with SynapticPathways
                    SynapticPathways.initialize()
                    SynapticPathways.register_manager("speech", auditory_cortex)
                    SynapticPathways.register_manager("audio", audio_cortex)
                    SynapticPathways.register_manager("button", somatosensory_cortex)
                    #SynapticPathways.register_manager("redmine", redmine_system)
                    print("PenphinOS initialized. Press and hold button to speak, release to process.")

                # Wait for button press to start recording
                somatosensory_cortex.wait_for_press()
                print("Recording started...")
                
                # Start recording via LLM module
                auditory_cortex.start_recording()
                
                # Wait for button release
                somatosensory_cortex.wait_for_release()
                print("Recording stopped, processing...")
                
                # Get transcribed text and process with LLM
                spoken_text = auditory_cortex.stop_recording()
                llm_response = SynapticPathways.transmit_json(NeuralCommands.tts_command(spoken_text))
                
                # Play response
                audio_cortex.play_sound(llm_response)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                auditory_cortex = None  # Force reinitialize on next loop
                time.sleep(1)  # Prevent rapid retry loop
                continue
                
    except KeyboardInterrupt:
        print("\nShutting down PenphinOS...")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
