import time
from AuditoryCortex.speech_manager import SpeechManager
from AuditoryCortex.audio_manager import AudioManager
from SomatosensoryCortex.button_manager import ButtonManager
from CorpusCallosum.synaptic_pathways import SynapticPathways
#from CorpusCallosum.redmine_manager import RedmineManager

def main():
    # Initialize managers
    auditory_cortex = SpeechManager()
    audio_cortex = AudioManager()
    somatosensory_cortex = ButtonManager()
    #redmine_system = RedmineManager()

    # Register managers with SynapticPathways
    SynapticPathways.initialize()
    SynapticPathways.register_manager("speech", auditory_cortex)
    SynapticPathways.register_manager("audio", audio_cortex)
    SynapticPathways.register_manager("button", somatosensory_cortex)
    #SynapticPathways.register_manager("redmine", redmine_system)

    print("PenphinOS initialized. Press and hold button to speak, release to process.")
    
    while True:
        try:
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
            llm_response = SynapticPathways.transmit_signal(spoken_text, "TTS")
            
            # Play response
            audio_cortex.play_sound(llm_response)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            continue

if __name__ == "__main__":
    main()
