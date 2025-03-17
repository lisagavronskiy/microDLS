import serial
from serial.tools import list_ports
import time
import csv
import threading
import numpy as np


# Configure the serial port
BAUD_RATE = 115200  
SUBSET_LENGTH = 800
DELAY = 2

class GetArdunioData:
    def __init__(self):
        self.stop_event = threading.Event()

        ports = [port.device for port in list_ports.comports()]
        serial_port = next((port for port in ports if 'usbmodem' in port or 'COM8' in port), None)
        self.ser = serial.Serial(serial_port, BAUD_RATE, timeout=1)
        time.sleep(DELAY)  # Establish connection

        self.error = None # if self.ser.is_open else serial.PortNotOpenError

    def csv_write(self, duration=10):
        batch_times = []
        batch_num = -1
    
        # Open the serial connection
        print('Connection established')
        # print('Turning laser on...')
        try:
            # self.ser.write('H'.encode())
            
            time.sleep(DELAY)

            # Open CSV file for writing
            csv_filename = "data_output.csv"


            with open(csv_filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Time(microseconds)", "DLS Value", "Temperature(C)"]) 

                print("Collecting data...")
                start_time = time.time()
        
                while (time.time() - start_time < duration) and not self.stop_event.is_set():
                    line = self.ser.readline().decode('ISO-8859-1').strip()
                    values = line.split(",")

                    if len(values) == SUBSET_LENGTH + 2:  # Ensure correct format (800 readings + 1 elapsed time)
                        dls_values = [int(v) for v in values[:-2]]  # First 800 values are DLS intensity
                        elapsed_time_microseconds = int(values[-2])  # Second last value is elapsed time in microseconds
                        temp_c = float(values[-1]) # Last value is temperature in Celcius
                        
                        batch_num += 1

                        # Compute average time step in microseconds
                        time_step_microseconds = elapsed_time_microseconds / SUBSET_LENGTH  
                        
                        # Generate time series in microseconds
                        if batch_num == 0:
                            time_series = [int(i * time_step_microseconds) for i in range(SUBSET_LENGTH)]
                        else:
                            time_series = [int(i * time_step_microseconds + np.sum(batch_times)) for i in range(SUBSET_LENGTH)]
                        # Write data to CSV
                        for t, intensity in zip(time_series, dls_values):
                            writer.writerow([t, intensity, temp_c])  
                        batch_times.append(elapsed_time_microseconds)
                    else:
                        pass
                        # if values[0] == '-1':
                        #    self.error = Exception('LID OPEN: Measurement Stopping')
                        #    self.stop()
                            
                print(f"Data saved to {csv_filename}")

        except Exception as e:
            pass


        self.close_connection()

    def close_connection(self):
        if self.ser.is_open:
            # Turn off laser
            # print('Turning laser off...')
            #self.ser.write('L'.encode())

            # Close the serial connection
            self.ser.close()

    def stop(self):
        # Close
        self.stop_event.set()