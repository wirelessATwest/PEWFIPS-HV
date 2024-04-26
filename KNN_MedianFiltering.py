import cv2
import numpy as np
from numpy import median
import csv
import pandas as pd
import matplotlib.pyplot as plt
import math
import time
import os

from common_functions import read_fingerprint_data, cdf, calculate_results, write_results, distance, sortonerror, mse, sort_dict_by_rssi, show_save_image


def medianFilteringPredictionAlgorithm(img, k, database, csv, test):
    start_total_time = time.time() # start recoding time for total run time for the program

    map = read_fingerprint_data(database)

    file_name = os.path.basename(__file__)
    ErrorList = []
    PredictionTime = []

    csv_filepath = csv
    PredictionTime, ErrorList = open_CSV(csv_filepath, img, k, ErrorList, PredictionTime, map, test)

    end_total_time = time.time() # start recoding time for total run time for the program 
    total_time = end_total_time - start_total_time

    return PredictionTime, ErrorList, total_time, file_name, k

def GetCandidatePos(online, fpdb, temp_k):
    candidates = []
    count = 0
    for key in fpdb.keys():
        candidate = fpdb[key]
        errRSSI = []
        k = temp_k  # Dynamically adjust k based on the number of access points available
        for i, bssid in enumerate(candidate.keys()):
            if bssid in online.keys():
                if k == 0:
                    break
                # Calculate error only if both online and candidate RSSI values are available
                err = abs(online[bssid] - candidate[bssid])
                errRSSI.append(err)
                # Include previous error only if count is divisible by 5 and previous key exists
                if count % 5 == 0 and i - 1 >= 0:
                    prev_bssid = list(candidate.keys())[i - 1]
                    if prev_bssid in online.keys():
                        prev_err = abs(online[prev_bssid] - candidate[prev_bssid])
                        errRSSI.append(prev_err)
                k -= 1
                
        # Error mitigation
        filtered_errRSSI = filter_errors(errRSSI)
        if filtered_errRSSI:
            average = sum(filtered_errRSSI) / len(filtered_errRSSI)
            candidates.append([key, average])
    candidates.sort(key=sortonerror)
    return candidates[0]

def filter_errors(errRSSI):
    # Implement median filtering technique
    window_size = 3  # Adjust window size based on the specific scenario
    #print(f"errRSSI \n\t\t{errRSSI}\n")

    filtered_errRSSI = []
    for i in range(len(errRSSI)):
        # Determine the range of indices for the window
        start_index = max(0, i - window_size // 2)
        end_index = min(len(errRSSI), i + window_size // 2 + 1)

        # Extract the window of values
        window_values = errRSSI[start_index:end_index]

        # Apply median filtering
        median_value = median(window_values)
        filtered_errRSSI.append(median_value)

    #print(f"filtered_errRSSI \n\t\t{filtered_errRSSI}\n")

    return filtered_errRSSI

def open_CSV(filepath, img, temp_k, ErrorList, PredictionTime, map, test_map):
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        for gtPtInfo in reader:
            gtPtX = int(gtPtInfo[1])
            gtPtY = int(gtPtInfo[2])
            gtPtFile = gtPtInfo[3]
            cv2.circle(img, (gtPtX, gtPtY), 4, (0, 0, 255), 2)
            cv2.putText(img, gtPtFile, (gtPtX + 15, gtPtY + 15), cv2.QT_FONT_NORMAL, 0.5, (0, 0, 0), 1)

            fileName = gtPtFile
            listScans = []

            test_filepath = test_map + fileName + ".txt"

            start_time = time.time()
            
            ErrorList, img = open_test(test_filepath, listScans, gtPtX, gtPtY, img, temp_k, ErrorList, map)

            end_time = time.time()
            duration = end_time - start_time
            PredictionTime.append(duration)
    #show_save_image(img)
    return PredictionTime, ErrorList

def open_test(filepath, listScans, gtPtX, gtPtY, img, temp_k, ErrorList, map):
    with open(filepath, 'r') as fileGT:
        reader = csv.reader(fileGT, delimiter=';')
        scanid = 0
        prvTag = "NONE"
        listBSSIDnRSSI = {}
        for apInfo in reader:
            if (len(apInfo) > 4):
                if apInfo[0] == "WIFI":
                    scanid = apInfo[2]
                    bssid = apInfo[4]
                    rssi = int(apInfo[5])
                    if check_BSSID_existence(map,bssid):
                        listBSSIDnRSSI[bssid] = rssi
                elif prvTag == "WIFI" and apInfo[0] != "WIFI":
                    if check_BSSID_existence(map,bssid):
                        listScans.append([scanid, listBSSIDnRSSI])
                        listBSSIDnRSSI = {}
                prvTag = apInfo[0]

        if not listScans:
            ErrorList.append(0)
            return ErrorList, img
        #print(listScans)
        listBSSIDnRSSI = listScans[0][1]

        listScans = [[1, listBSSIDnRSSI]]
        if listScans:
            listScans[-1][1] = sort_dict_by_rssi(listScans[-1][1])

        for scan in listScans:
            onlineScan = scan[1]
            # Step 5  Estimate Candidate Position Positions Using RMSE
            locXY, errRSSI = GetCandidatePos(onlineScan, map, temp_k)

            loc = locXY.split('_')

            # Step 6  Display result on map

            posX = int(loc[0])  # ???
            posY = int(loc[1])  # ???
            cv2.circle(img, (posX, posY), 4, (0, 0, 0), 2)

            # example Line
            cv2.line(img, (gtPtX, gtPtY), (posX, posY), (0, 255, 0), 2)
            ErrorList.append(abs(distance((posX, posY), (gtPtX, gtPtY)) / 35.7))

    return ErrorList, img


def check_BSSID_existence(data_map, bssid):
    for pos_key in data_map.values():
        if bssid in pos_key:
            return True
    return False



