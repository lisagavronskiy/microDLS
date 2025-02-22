import serial
from serial.tools import list_ports
import time
import csv
import threading

# Configure the serial port
BAUD_RATE = 115200  

ports = [port.device for port in list_ports.comports()]
SERIAL_PORT = next(port for port in ports if 'usbmodem' in port)

class GetArdunioData:
    def __init__(self):
        self.stop_event = threading.Event()

    def csv_write(self, duration=10):
        # Open the serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.5)  # Establish connection

        # Open CSV file for writing
        csv_filename = "data_output.csv"
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time (seconds)", "DLS Value", "Temperature"]) 

            print("Collecting data...")
            start_time = time.time()

            while (time.time() - start_time < duration) and not self.stop_event.is_set():
                line = ser.readline().decode('ISO-8859-1').strip()
                timestamp = time.time() - start_time
                values = [float(x) for x in line.split(",")]
                
                # Write data to CSV
                writer.writerow([timestamp, *values])

        # Close the serial connection
        ser.close()

        print(f"Data saved to {csv_filename}")

    def stop(self):
        self.stop_event.set()
