"""
testLEDMatrix script to demonstrate LED Matrix functionality on Raspberry Pi 
and a mock matrix on macOS.
"""

import platform
import time

# Conditional import based on platform
if platform.system() == "Linux":
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
else:
    # Note the leading dot for relative import
    from .mock_rpi_rgb_led_matrix import (
        CognitiveMatrix as RGBMatrix,
        CognitiveMatrixOptions as RGBMatrixOptions
    )


def runPsychologyDrivenMatrixTest():
    """
    Run a test of the LED matrix at 50% brightness, provide status output, 
    then clear on interruption or after the delay.
    """
    # Architecture-focused LED matrix options
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = "regular"
    options.brightness = 50

    matrix = RGBMatrix(options=options)

    try:
        print("✅ Running LED Matrix Test at 50% Brightness...")
        matrix.Fill(128, 128, 128)  # Grey background
        time.sleep(5)
        print("✅ Test Complete!")
    except KeyboardInterrupt:
        print("\n🔹 Exiting... Clearing Matrix.")
    finally:
        matrix.Clear()


if __name__ == "__main__":
    runPsychologyDrivenMatrixTest() 