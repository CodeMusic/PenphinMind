import subprocess
import os

class AudioManager:
    def __init__(self):
        self._configure_audio_hat()
        self.is_playing = False

    def _configure_audio_hat(self):
        """
        Configure Waveshare Audio HAT settings with comprehensive mixer controls
        """
        try:
            # Set all relevant mixer settings
            subprocess.run(["amixer", "-c", "0", "sset", "Speaker", "100%"], check=True)
            subprocess.run(["amixer", "-c", "0", "sset", "Playback", "100%"], check=True)
            subprocess.run(["amixer", "-c", "0", "sset", "Headphone", "100%"], check=True)
            subprocess.run(["amixer", "-c", "0", "sset", "PCM", "100%"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error configuring Audio HAT: {e}")
            print("Available controls:")
            try:
                subprocess.run(["amixer", "-c", "0", "controls"], check=True)
            except subprocess.CalledProcessError:
                print("Could not list audio controls")

    def play_sound(self, sound_file):
        """
        Play audio using aplay with Waveshare HAT device
        """
        try:
            subprocess.run(['aplay', '-D', 'plughw:0,0', sound_file], check=True)
            self.is_playing = True
        except subprocess.CalledProcessError as e:
            print(f"Error playing sound: {e}")

    def stop_sound(self):
        """
        Stop currently playing sound
        """
        if self.is_playing:
            try:
                subprocess.run(['killall', 'aplay'], check=False)
                self.is_playing = False
            except subprocess.CalledProcessError:
                pass

    def set_volume(self, volume):
        """
        Set volume level (0-100) for all outputs
        """
        try:
            volume = max(0, min(100, int(volume * 100)))
            for control in ["Speaker", "Playback", "Headphone", "PCM"]:
                subprocess.run(['amixer', '-c', '0', 'sset', control, f'{volume}%'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error setting volume: {e}") 