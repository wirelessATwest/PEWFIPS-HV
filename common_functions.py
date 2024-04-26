import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import cv2


# Extract FP data
def read_fingerprint_data(file_path):
    """
    Read fingerprint data from a CSV file and return a dictionary.
    :param file_path: Path to the CSV file
    :return: Dictionary containing fingerprint data
    """
    fingerprint_data = {}
    fpData = pd.read_csv(file_path)
    for index, row in fpData.iterrows():
        key = str(row['PosX']) + "_" + str(row['PosY'])
        RSSI = int(row['RSSI'])
        if key in fingerprint_data:
            fingerprint_data[key][row['BSSID']] = RSSI
        else:
            fingerprint_data[key] = {row['BSSID']: RSSI}
    return fingerprint_data

def cdf(x, plot=True, *args, **kwargs):
    x, y = sorted(x), np.arange(len(x)) / len(x)
    return plt.plot(x, y, *args, **kwargs) if plot else (x, y)

def plot_cdf_with_quartiles(data, graph_name, k):
    # Calculate quartiles
    Q1 = np.percentile(data, 25)
    Q2 = np.percentile(data, 50)  # Median (Q2)
    Q3 = np.percentile(data, 75)

    # Sort data for plotting CDF
    sorted_data = np.sort(data)
    n = len(data)

    # Calculate cumulative probabilities
    cdf = np.arange(1, n + 1) / n

    # Plot CDF
    plt.plot(sorted_data, cdf, marker='o', linestyle='-')

    # Add quartile lines
    plt.axvline(Q1, color='r', linestyle='--', label='Q1')
    plt.axvline(Q2, color='g', linestyle='--', label='Q2 (Median)')
    plt.axvline(Q3, color='b', linestyle='--', label='Q3')

    # Add labels and title
    plt.xlabel('Data')
    plt.ylabel('Cumulative Probability')
    plt.title(f'Cumulative Distribution Function (CDF) with Quartile Values, K = {k}')
    plt.legend()

    # Show plot
    plt.grid(True)
    plt.savefig(graph_name)
    plt.show()



def distance(p1, p2):
    return math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))

def sortonerror(e):
    return e[-1]

# Mean Square Error
# locations: [ (x1, y1), ... ]
# distances: [ distance1, ... ]
def mse(x, locations, distances):
    mse = 0.0
    for location, dist in zip(locations, distances):
        distance_calculated = distance(x, location)
        mse += math.pow(distance_calculated - dist, 2.0)
    return mse / len(distances)  # len(data)

def sort_dict_by_rssi(d):
    return {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}


def calculate_results(total_time, ErrorList, PredictionTime, temp_k, file_name, database):
    # Calculate times...
    average_prediction_time = sum(PredictionTime) / len(PredictionTime)
    standard_deviation_time = np.std(PredictionTime)

    # Calculate Accuracy...

    average_error = sum(ErrorList) / len(ErrorList)
    standard_deviation_error = np.std(ErrorList) 

    # how many is accurate
    # threshold = 10  
    # accurate_predictions = sum(1 for error in ErrorList if error <= threshold)
    # accuracy = (accurate_predictions / len(ErrorList)) * 100

    # Calculate Precision...
    rmse = math.sqrt(sum(error ** 2 for error in ErrorList) / len(ErrorList)) # Root Square Mean Error (meters)

    write_results(temp_k, total_time, PredictionTime, average_prediction_time, standard_deviation_time, ErrorList, average_error, standard_deviation_error, file_name, rmse, database)
                  

def write_results(temp_k, total_time, PredictionTime, average_prediction_time, standard_deviation_time, ErrorList, average_error, standard_deviation_error, file_name, rmse, database):
    i = 0

    with open("results/results.txt", "r") as file:
        # Iterate over each line in the file
        for line_number, line in enumerate(file, start=1):
            # Check if the line is empty or contains only whitespace characters
            if line.strip() == "":
                i += 1

    with open('results/results.txt', 'a') as file:
        file.write(f"Result: {i},\t Algorithm: {file_name}\n")
        file.write(f"\tK Value: {temp_k},\t Database: {database}\n")

        file.write("\tError in meters:\n")
        file.write(f"\t\tErrorList (meters): {ErrorList}\n")
        file.write(f"\t\tAvarage Error (meters): {average_error}\n")

        file.write("\tPrecision:\n")
        file.write(f"\t\tStandard deviation Error: {standard_deviation_error}\n")
        file.write(f"\t\tRoot Square Mean Error (meters): {rmse}\n")

        file.write("\tPerformance\n")
        file.write(f"\t\tComputational Times for Predictions: {PredictionTime}\n")
        file.write(f"\t\tAvarage Computational Time for Predictions: {average_prediction_time}\n")
        file.write(f"\t\tStandard deviation Time: {standard_deviation_time}\n")

        file.write(f"\t\tTime for the entire program (References and Tests): {total_time}\n\n")

# Show and Save the new image
def show_save_image(img):
    cv2.imshow('Map with Regions', img)
    cv2.waitKey(0)
    cv2.imwrite("regions.png", img)
