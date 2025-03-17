import pandas as pd
import matplotlib.pyplot as plt
import csv
import numpy as np
from scipy.signal import argrelextrema, find_peaks

SET_LENGTH = 1600
NUM_SETS = 4
EXPECTED_TIME = 14110 # Microseconds per subset_length
TIME_PER_DATA = EXPECTED_TIME / SET_LENGTH

selected_range = [0, SET_LENGTH * NUM_SETS]

df = pd.read_csv("0311raw_4v_laser/95J_great.csv")

time, y_data = df['Time(microseconds)'][selected_range[0]:selected_range[1]], df['DLS Value'][selected_range[0]:selected_range[1]]

time_plot = np.array(time[0:SET_LENGTH])
y_plot = np.array(y_data[0:SET_LENGTH])

# time_plot = np.array(time[3200:4800])
# y_plot = np.array(y_data[3200:4800])

average_time = time_plot[-1] / SET_LENGTH
# print(average_time)

# y_plot = y_data[0:SET_LENGTH]

# plt.figure(figsize=(8, 5))
# plt.plot(time_plot, y_plot, marker='o', linestyle='-', color='b', label="Data")

# # Labels and title
# plt.xlabel("X Data")
# plt.ylabel("Y Data")
# plt.title("Plot of X vs Y")
# plt.legend()
# plt.grid(True)

# # Show plot
# plt.show()

time = time[0:SET_LENGTH]

cols = int(selected_range[1] / SET_LENGTH)

num_sets = []

sub_set = []


# Create subsets from bulk data
for value in y_data:
    sub_set.append(value)
    if len(sub_set) == SET_LENGTH:
        num_sets.append(sub_set)
        sub_set = []


plt.figure(figsize=(8, 5))
for i in range(NUM_SETS):
    
    plt.plot(time_plot, num_sets[i], marker='o', linestyle='-', label="Data")

    # Labels and title
plt.xlabel("Time us")
plt.ylabel("Raw Intensity")
plt.title("Plot of X vs Y")
plt.legend()
plt.grid(True)
plt.show()

avg_data = []

for i in range(SET_LENGTH):
    for j in range(NUM_SETS):
        if j == 0:
            avg_data.append(num_sets[j][i])
        else:
            avg_data[i] += num_sets[j][i]
    avg_data[i] = avg_data[i] / NUM_SETS

plt.figure(figsize=(8, 5))
plt.plot(time_plot, avg_data, marker='o', linestyle='-', label="Average Signal")
plt.xlabel("Time us")
plt.ylabel("Raw Intensity")
plt.title("Plot of X vs Y")
plt.legend()
plt.grid(True)
plt.show()

csv_filename = "average_data.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Time(microseconds)", "Average Signal"])  # Updated header
    for j in range(SET_LENGTH-1):
        data = [time[j]]
        data.append(avg_data[j])
        writer.writerow(data)

def smooth_signal(y_values, window=5):
    """Applies a simple moving average for noise reduction."""
    return np.convolve(y_values, np.ones(window)/window, mode='same')

def extract_extrema(y_values, prominence=0.5, smooth_window=5):
    """
    Extract the index of the maximum peak and the two local minima on either side,
    with noise reduction and prominence filtering.
    
    :param y_values: List or numpy array of y-values (raw data)
    :param prominence: Minimum prominence for peak detection to ignore small bumps.
    :param smooth_window: Window size for moving average smoothing.
    :return: Tuple (left_min_index, max_index, right_min_index)
    """
    y_values = np.array(y_values)
    smoothed_y = smooth_signal(y_values, window=smooth_window)
    
    # Find local maxima and minima with prominence filtering
    maxima_indices, _ = find_peaks(smoothed_y, prominence=prominence)
    minima_indices, _ = find_peaks(-smoothed_y, prominence=prominence)
    
    if len(maxima_indices) == 0 or len(minima_indices) < 2:
        raise ValueError("Not enough significant extrema found to determine a peak with two surrounding minima.")
    
    # Identify the global max index among local maxima
    max_index = maxima_indices[np.argmax(smoothed_y[maxima_indices])]
    
    # Find the closest left and right minima
    left_minima = minima_indices[minima_indices < max_index]
    right_minima = minima_indices[minima_indices > max_index]
    
    if len(left_minima) == 0 or len(right_minima) == 0:
        raise ValueError("Could not find both left and right local minima around the peak.")
    
    left_min_index = left_minima[-1]  # Last (closest) left minimum
    right_min_index = right_minima[0]  # First (closest) right minimum
    
    return left_min_index, max_index, right_min_index

left_min_idx, peak_idx, right_min_idx = extract_extrema(avg_data)

plt.figure(figsize=(8, 5))
plt.plot(time_plot, avg_data, marker='o', linestyle='-', color='b', label="Data")

plt.axvline(x=time_plot[left_min_idx], color='y', linestyle='--', linewidth=2, label="Local min (left)")
plt.axvline(x=time_plot[peak_idx], color='r', linestyle='--', linewidth=2, label="Local min (right)")
plt.axvline(x=time_plot[right_min_idx], color='g', linestyle='--', linewidth=2, label="Local max")
# Labels and title
plt.xlabel("X Data")
plt.ylabel("Y Data")
plt.title("Plot of X vs Y")
plt.legend()
plt.grid(True)

# Show plot
plt.show()

# print(left_min_idx, peak_idx, right_min_idx)

csv_filename = "average_data_peak.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Time(microseconds)", "Average Signal"])  # Updated header
    for j in range(peak_idx, right_min_idx):
        data = [time[j] - time[peak_idx]]
        data.append(avg_data[j])
        writer.writerow(data)