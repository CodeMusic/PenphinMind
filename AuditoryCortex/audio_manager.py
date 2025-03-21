import subprocess
import os

class AudioManager:
    def __init__(self):
        self._configure_audio_hat()
        self.is_playing = False

    def _configure_audio_hat(self):
        """
        Configure Waveshare Audio HAT settings
        """
        try:
            # Set default mixer settings
            subprocess.run(['amixer', '-c', '0', 'sset', 'PCM', '100%'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error configuring Audio HAT: {e}")

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
        Set volume level (0-100)
        """
        try:
            volume = max(0, min(100, int(volume * 100)))
            subprocess.run(['amixer', '-c', '0', 'sset', 'PCM', f'{volume}%'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error setting volume: {e}") 