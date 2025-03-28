import serial
import time

ser = serial.Serial('COM3', 115200, timeout=1)

ser.write(b'{"request_id":"ping","action":"ping"}\n')

time.sleep(1)

response = ser.read_all()
print("Response:", response)

ser.close()
