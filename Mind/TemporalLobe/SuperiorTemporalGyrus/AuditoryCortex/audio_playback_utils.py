"""
Audio Playback Utility Functions - located within the Auditory Cortex structure.
Provides high-level functions for playing sounds using system commands.
"""

import os
import subprocess
import time

# Default Audio Config (Consider moving to main config)
AUDIO_DEVICE = "plughw:0,0"

def detect_audio_devices():
    """
    Detects available audio devices using aplay -l command.
    Returns a dict mapping device IDs to their descriptions.
    """
    audio_devices = {}
    
    try:
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                if line.startswith('card '):
                    parts = line.split(':', 1)
                    if len(parts) >= 2:
                        # Extract card and device numbers
                        card_info = parts[0].strip()
                        description = parts[1].strip()
                        
                        # Parse card and device numbers
                        card_parts = card_info.split()
                        if len(card_parts) >= 4:
                            card_num = card_parts[1]
                            device_num = card_parts[3].rstrip(':')
                            
                            # Format device ID as plughw:card,device
                            device_id = f"plughw:{card_num},{device_num}"
                            audio_devices[device_id] = description
            
            print(f"[Audio Playback Util] Found {len(audio_devices)} audio devices")
        else:
            print(f"[Audio Playback Util] Error detecting audio devices: {result.stderr}")
    except FileNotFoundError:
        print("[Audio Playback Util] aplay command not found. Audio detection skipped.")
    except Exception as e:
        print(f"[Audio Playback Util] Error in audio device detection: {e}")
    
    return audio_devices

def set_audio_device(device_id):
    """
    Sets the specified audio device as the default.
    Returns True if successful, False otherwise.
    """
    global AUDIO_DEVICE
    
    # Validate device ID format
    if not device_id.startswith(("plughw:", "hw:", "default")):
        print(f"[Audio Playback Util] Invalid audio device format: {device_id}")
        return False
    
    # Test the device with a quick speaker test
    try:
        print(f"[Audio Playback Util] Testing audio device: {device_id}")
        result = subprocess.run(
            ['speaker-test', '-D', device_id, '-t', 'sine', '-f', '1000', '-l', '1'], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=1
        )
        
        if result.returncode == 0:
            # Device works, set it as default
            AUDIO_DEVICE = device_id
            print(f"[Audio Playback Util] Successfully set audio device to: {device_id}")
            return True
        else:
            print(f"[Audio Playback Util] Failed to set audio device: {device_id}")
            return False
    except subprocess.TimeoutExpired:
        # If it times out, it might actually be working (just not terminating properly)
        # We'll consider this a success
        AUDIO_DEVICE = device_id
        print(f"[Audio Playback Util] Set audio device to: {device_id} (timeout during test)")
        return True
    except Exception as e:
        print(f"[Audio Playback Util] Error setting audio device: {e}")
        return False

def play_sound(sound_file: str, audio_device: str = AUDIO_DEVICE):
    """Play the specified sound file using aplay with fallback to speaker-test."""
    if not os.path.exists(sound_file):
        print(f"[Audio Playback Util] Warning: Sound file {sound_file} not found")
        return
        
    success = False
    try:
        print(f"[Audio Playback Util] Attempting audio playback of {sound_file}...")
        
        # First, try playing the sound file directly using aplay
        try:
            print(f"[Audio Playback Util] Playing sound file on {audio_device}")
            # Use os.system with & to run in background without blocking
            # Redirect stdout/stderr to /dev/null to avoid cluttering console
            # Ensure sound_file path is properly quoted for the shell
            command = f'aplay -D {audio_device} "{sound_file}" > /dev/null 2>&1 &'
            print(f"[Audio Playback Util] Running command: {command}")
            os.system(command)
            # Assume success if command executes without immediate error
            success = True 
            print("[Audio Playback Util] Sound playback initiated via aplay")
        except Exception as e:
            print(f"[Audio Playback Util] aplay command failed: {e}")
            
        # Fallback to speaker-test as a quick pulse to activate the device
        try:
            print(f"[Audio Playback Util] Using speaker-test on {audio_device} as pulse")
            sp_process = subprocess.Popen(
                ['speaker-test', '-D', audio_device, '-t', 'sine', '-f', '1000', '-l', '1'], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            time.sleep(0.1) 
            if sp_process.poll() is None:
                sp_process.terminate()
                try:
                    sp_process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    sp_process.kill() # Force kill if terminate doesn't work
            print("[Audio Playback Util] Speaker test pulse completed")
        except FileNotFoundError:
             print("[Audio Playback Util] speaker-test command not found. Skipping pulse.")
        except Exception as e:
            print(f"[Audio Playback Util] Speaker test pulse failed: {e}")
            
    except Exception as e:
        print(f"[Audio Playback Util] Error in audio playback function: {e}") 