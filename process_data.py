import serial
from serial.tools import list_ports
import time
import csv
import threading
import numpy as np

# Configure the serial port
BAUD_RATE = 115200  
SUBSET_LENGTH = 1600
DELAY = 2
# Automatically detect the correct port
ports = [port.device for port in list_ports.comports()]
SERIAL_PORT = next((port for port in ports if 'COM10' in port), None)

if not SERIAL_PORT:
    raise Exception("COM8 not found. Check your Arduino connection.")

class GetArduinoData:
    def __init__(self):
        self.stop_event = threading.Event()

    def csv_write(self, duration=10):
        batch_times = []
        batch_num = -1
        # Open the serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(DELAY)  # Allow time for connection to stabilize

        # Open CSV file for writing
        csv_filename = "formatted_dls_data.csv"
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time(microseconds)", "DLS Value", "Temperature(C)"])  # Updated header

            print("Collecting data...")
            start_time = time.time()

            while (time.time() - start_time < duration) and not self.stop_event.is_set():
                try:
                    line = ser.readline().decode('ISO-8859-1').strip()
                    values = line.split(",")

                    if len(values) == SUBSET_LENGTH + 1:  # Ensure correct format (800 readings + 1 elapsed time)
                        dls_values = [int(v) for v in values[:-1]]  # First 800 values are DLS intensity
                        elapsed_time_microseconds = int(values[-1])  # Last value is elapsed time in microseconds
                        
                        
                        batch_num += 1
                        # Compute average time step in microseconds
                        time_step_microseconds = elapsed_time_microseconds / SUBSET_LENGTH  
                        
                        # Generate time series in microseconds
                        if batch_num == 0:
                            time_series = [int(i * time_step_microseconds) for i in range(SUBSET_LENGTH)]
                        else:
                            # print(batch_times)
                            # print(np.cumsum(batch_times))
                            time_series = [int(i * time_step_microseconds + np.sum(batch_times)) for i in range(SUBSET_LENGTH)]
                        # Write data to CSV
                        for t, intensity in zip(time_series, dls_values):
                            writer.writerow([t, intensity, 25.0])  # Add fixed temperature
                        batch_times.append(elapsed_time_microseconds)
                    else:
                        # print(f"Skipping malformed data: {line}")
                        print("")

                except Exception as e:
                    print(f"Error reading data: {e}")

        # Close the serial connection
        ser.close()
        print(f"Data saved to {csv_filename}")

    def stop(self):
        self.stop_event.set()
