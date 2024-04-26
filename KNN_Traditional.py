import cv2
import numpy as np
import csv
import pandas as pd
import matplotlib.pyplot as plt
import math
import time
import os

from common_functions import read_fingerprint_data, cdf, calculate_results, write_results, distance, sortonerror, mse, sort_dict_by_rssi







# Step 3  Read test pos file

# GT Points
def GetCandidatePos(online, fpdb, temp_k):
    candidates = []
    for key in fpdb.keys():
        candidate = fpdb[key]
        errRSSI = []
        k = temp_k  # k is the number of Neighbouring WiFi access points
        for bssid in candidate.keys():
            if bssid in online.keys():
                if k == 0:
                    break
                k = k - 1
                errRSSI.append(abs(candidate[bssid] - online[bssid]))
        if errRSSI:
            average = sum(errRSSI) / len(errRSSI)
            candidates.append([key, average])
        

    # Step select final position candidate
    candidates.sort(key=sortonerror)
    return candidates[0]


def open_CSV(filepath, img, temp_k, ErrorList, PredictionTime, map, test_map):
    # this file is with your test locations
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        for gtPtInfo in reader:
            gtPtX = int(gtPtInfo[1])
            gtPtY = int(gtPtInfo[2])
            gtPtFile = gtPtInfo[3]
            cv2.circle(img, (gtPtX, gtPtY), 4, (255, 0, 0), 2)
            cv2.putText(img, gtPtFile, (gtPtX + 15, gtPtY + 15), cv2.QT_FONT_NORMAL, 0.5, (0, 0, 0), 1)

            fileName = gtPtFile
            listScans = []

            test_filepath = test_map + fileName + ".txt"

            start_time = time.time()
            
            ErrorList = open_test(test_filepath, listScans, gtPtX, gtPtY, img, temp_k, ErrorList, map)

            end_time = time.time()
            duration = end_time - start_time
            PredictionTime.append(duration)
    
    return PredictionTime, ErrorList


def open_test(filepath, listScans, gtPtX, gtPtY, img, temp_k, ErrorList, map):
    ## SORT TEST POINT AFTER RSSI
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
                    listBSSIDnRSSI[bssid] = rssi
                elif prvTag == "WIFI" and apInfo[0] != "WIFI":
                    listScans.append([scanid, listBSSIDnRSSI])
                    listBSSIDnRSSI = {}
                prvTag = apInfo[0]
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

    return ErrorList


def ogPredictionAlgorithm(img, k, database, csv, test):
    start_total_time = time.time() # start recoding time for total run time for the program 

    map = read_fingerprint_data(database)

    img = cv2.imread('images/output_image.png')  # use your map img
    ErrorList = []
    PredictionTime = []
    file_name = os.path.basename(__file__)
    
    csv_filepath = csv

    PredictionTime, ErrorList = open_CSV(csv_filepath, img, k, ErrorList, PredictionTime, map, test)

    end_total_time = time.time() # start recoding time for total run time for the program 
    total_time = end_total_time - start_total_time

    #show_save_image(img)

    return PredictionTime, ErrorList, total_time, file_name, k

# this file is with your test locations

#PredictionTime, ErrorList, total_time, file_name, temp_k = ogPredictionAlgorithm()
#print(PredictionTime, ErrorList, total_time, file_name, temp_k)

#calculate_results(end_total_time, start_total_time, end_init_time, start_init_time, ErrorList, PredictionTime, 'precision_histogram_original.png', temp_k, file_name)


if "__main__" == __name__:
    img = 'images/output_image.png'  # use your map img
    k = 5
    database = "fpData-Full.txt"
    csv_path = "CSV/Test All.csv"
    test_path = 'b_All_Tests/'
    ogPT, ogEL, ogTL, ogFN, ogK = ogPredictionAlgorithm(img, k, database, csv_path, test_path)
    cdf(ogEL)
    plt.show()

