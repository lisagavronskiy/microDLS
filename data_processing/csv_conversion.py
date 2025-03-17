import pandas as pd
import matplotlib.pyplot as plt
import csv
import numpy as np

SET_LENGTH = 1600
NUM_SETS = 7
selected_range = [0, SET_LENGTH * NUM_SETS]

def plot_peak(x, y, local_min_left, local_min_right, local_max):
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker='o', linestyle='-', color='b', label="Data")

    plt.axvline(x[local_min_left], color='y', linestyle='--', linewidth=2, label="Local min (left)")
    plt.axvline(x[local_min_right], color='r', linestyle='--', linewidth=2, label="Local min (right)")
    plt.axvline(x[local_max], color='g', linestyle='--', linewidth=2, label="Local max")
    # Labels and title
    plt.xlabel("X Data")
    plt.ylabel("Y Data")
    plt.title("Plot of X vs Y")
    plt.legend()
    plt.grid(True)

    # Show plot
    plt.show()

def find_local_extrema(y_values, start_idx=100, tolerance=4):
    """
    Find a local maximum and its nearest local minima on the left and right.
    
    Parameters:
        y_values (list or numpy array): The y-values of the data (intensity, amplitude, etc.).
        start_idx (int): The index from which to start searching for a local maximum.

    Returns:
        tuple: Indices of the left local minimum, local maximum, and right local minimum.
            Returns None if extrema cannot be found.
    """

    if len(y_values) < 3:
        return None  # Need at least three points to find a peak and minima
    
    # Ensure start index is within valid range
    # start_idx = max(1, min(start_idx, len(y_values) - 2))
    # print(type(y_values)) 
    if type(y_values) == np.ndarray:   
        start_idx = y_values.tolist().index(max(y_values))
    else:
        start_idx = y_values.index(max(y_values))

    # Find local maximum starting from start_idx
    # for i in range(start_idx, len(y_values) - 1):
    #     if y_values[i - 1] < y_values[i] > y_values[i + 1]:
    #         peak_idx = i
    #         break
    # else:
    #     return None  # No local maximum found
    peak_idx = start_idx
    # Find nearest local minimum to the left
    left_min_idx = None
    # print(y_values[peak_idx])
    for i in range(peak_idx - 1, 0, -1):
        # print(y_values[i - 1], y_values[i], y_values[i + 1])
        avg_len = 4
        forward_average = sum(y_values[i : i - avg_len : -1]) / avg_len
        # print(forward_average)
        if y_values[i - 1] >= y_values[i] <= y_values[i + 1] and abs(forward_average - y_values[i]) > tolerance/4:
            left_min_idx = i
            break
            
    # Find nearest local minimum to the right
    right_min_idx = None
    for i in range(peak_idx + 1, len(y_values) - 1):
        avg_len = 3
        forward_average = sum(y_values[i : i + avg_len : 1]) / avg_len
        # print(y_values[i - 1], y_values[i], y_values[i + 1], abs(forward_average - y_values[i]))
        if y_values[i - 1] >= y_values[i] <= y_values[i + 1] and abs(forward_average - y_values[i]) > tolerance:
            right_min_idx = i
            break

    # print(forward_average)
    # print(y_values[right_min_idx])
    # print(left_min_idx, peak_idx, right_min_idx)
    # Ensure both minima exist
    if left_min_idx is None or right_min_idx is None:
        return None

    return left_min_idx, peak_idx, right_min_idx

def convert_to_peaks(file_name):
    df = pd.read_csv(file_name)

    time, y_data = df['Time(microseconds)'][selected_range[0]:selected_range[1]], df['DLS Value'][selected_range[0]:selected_range[1]]

    time_plot = np.array(time[0:SET_LENGTH])
   

    average_time = time_plot[-1] / SET_LENGTH

    # If plotting peak is desired, uncomment
    # y_plot = np.array(y_data[0:SET_LENGTH])
    # local_min_left, local_max, local_min_right = find_local_extrema(y_plot)
    # plot_peak(time_plot, y_plot, local_min_left, local_max, local_min_right)

    # Create a time array
    time = time[0:SET_LENGTH]
    # Create a column format
    cols = int(selected_range[1] / SET_LENGTH)

    # All sets contains every data point, subsets is 1600 point chunks
    all_sets = []
    sub_set = []


    # Create subsets from bulk data
    for value in y_data:
        sub_set.append(value)
        if len(sub_set) == SET_LENGTH-1:
            all_sets.append(sub_set)
            sub_set = []


    # Create sub sets for just peaks
    # -- Max iterations used to ensure the data is the same length
    sub_maxs = []
    max_iterations = 0 

    for subset in all_sets:
        data_set = find_local_extrema(subset) # left min, max, right min
        values = subset[data_set[1]:data_set[2]] # Create peak set from max value to right min
        if len(values) > max_iterations: max_iterations = len(values) # Find max iterations
        sub_maxs.append(values)

    # Sort from longest to highest to create the time space
    sub_maxs = sorted(sub_maxs, key=len)
    subset_time_array = np.arange(0, (max_iterations) * average_time, average_time)

    csv_filename = "converted.csv" # Converted is for entire dataset
    csv_subsetfile = "subsets.csv" # subsets extracts peaks only
    col_headers = ["Time(microseconds)"]

    # Convert full files
    for i in range(cols):
        col_headers.append("data_set_" + str(i))

    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(col_headers)  # Updated header
        for j in range(SET_LENGTH-1):
            data = [time[j]]
            for set_val in range(NUM_SETS):
                data.append(all_sets[set_val][j])
            writer.writerow(data)

    print("Full file converted")

    with open(csv_subsetfile, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(col_headers)  # Updated header
        for index, t in enumerate(subset_time_array):
            data = [t]
            for sub in sub_maxs:
                tail = min(sub)
                if index < len(sub):
                    data.append(sub[index])
                else:
                    data.append(tail)
            writer.writerow(data)

    print("Subset file converted")

if __name__ == "__main__":
    convert_to_peaks("0311raw_4v_laser/95J_great.csv")