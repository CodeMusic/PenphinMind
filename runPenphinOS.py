import time
import serial
import speech_recognition as sr
from gpiozero import Button

# Set up GPIO for the push button
BUTTON_PIN = 17
button = Button(BUTTON_PIN, pull_up=False)  # Internal pull-down resistor

# Set up serial communication with the M5Stack LLM Module
SERIAL_PORT = "/dev/ttyUSB0"  # Adjust if needed
BAUD_RATE = 115200
llm_serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Speech Recognition Setup
def record_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("Listening... Hold the button to talk.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return "I couldn't understand that."
    except sr.RequestError:
        return "Speech recognition service is unavailable."

# Function to send text to the LLM module for processing & TTS output
def send_to_llm(text):
    command = f"TTS:{text}\n"  # Adjust based on the module's API format
    llm_serial.write(command.encode())  # Send text to LLM module
    print(f"Sent to LLM: {command}")

# Main loop – Waits for button press to start interaction
print("Press and hold the button to speak.")
while True:
    button.wait_for_press()
    spoken_text = record_audio()
    send_to_llm(spoken_text)  # LLM handles processing and TTS output
    time.sleep(0.5)  # Prevent accidental multiple presses
