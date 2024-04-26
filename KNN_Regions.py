
import cv2
import numpy as np
import csv
import pandas as pd
import matplotlib.pyplot as plt
import math
import time
import os

from common_functions import read_fingerprint_data, cdf, calculate_results, write_results, distance, sortonerror, mse, sort_dict_by_rssi


def regionPredictionAlgorithm(img, k, database, csv, test):
    start_total_time = time.time() # start recoding time for total run time for the program 

    # Given list of BSSIDs
    bssid_list = ['70:b3:17:8d:e9:60', '70:b3:17:8e:1c:00', '78:bc:1a:37:7e:00', 
                  '48:8b:0a:ca:a8:00', '48:8b:0a:cb:67:e0', '48:8b:0a:cb:69:20']

    # Run and prepare Reference Data
    fingerprint_data = read_fingerprint_data(database)
    regions = find_highest_rssi_bssid(fingerprint_data, bssid_list)
    # sort Region Data
    region_select, r_data = sort_region_data(regions, bssid_list, fingerprint_data)

    #draw_circles(img, regions)

    ErrorList = []
    PredictionTime = []
    file_name = os.path.basename(__file__)

    csv_filepath = csv
    PredictionTime, ErrorList = open_CSV(csv_filepath, img, k, ErrorList, PredictionTime, region_select, r_data, bssid_list, test)

    end_total_time = time.time() # start recoding time for total run time for the program 
    total_time = end_total_time - start_total_time

    #show_save_image(img)

    return PredictionTime, ErrorList, total_time, file_name, k


# Find the BSSID with the highest RSSI value from the BSSID from the list
def find_highest_rssi_bssid(fingerprint_data, bssid_list):
    highest_rssi_bssid_info = {}
    for key, data in fingerprint_data.items():
        highest_rssi = float('-inf')  # Initialize with negative infinity
        highest_rssi_bssid = None
        for bssid in bssid_list:
            truncated_bssid = bssid[:14]  # Consider only the first 10 characters
            if any(truncated_bssid in full_bssid for full_bssid in data):
                # Check if any BSSID in data starts with the truncated BSSID
                max_rssi_for_truncated_bssid = max(data[full_bssid] for full_bssid in data if truncated_bssid in full_bssid)
                if max_rssi_for_truncated_bssid > highest_rssi:
                    highest_rssi = max_rssi_for_truncated_bssid
                    highest_rssi_bssid = truncated_bssid
        highest_rssi_bssid_info[key] = highest_rssi_bssid
    return highest_rssi_bssid_info

# Choose a color for each region, for visualization
def get_color(truncated_bssid):
    """
    Assigns a color based on the given BSSID.
    """
    color_map = {
        '70:b3:17:8d:e9': (255, 0, 0),    # Red
        '70:b3:17:8e:1c': (0, 255, 0),    # Green
        '78:bc:1a:37:7e': (0, 0, 255),    # Blue
        '48:8b:0a:ca:a8': (255, 255, 0),  # Yellow
        '48:8b:0a:cb:67': (255, 0, 255),  # Magenta
        '48:8b:0a:cb:69': (0, 255, 255)   # Cyan
    }
    for prefix, color in color_map.items():
        if truncated_bssid.startswith(prefix):
            return color
    return (128, 128, 128)  # Default color if BSSID prefix not found


# Filter and return data accoring to region, return only those RP that belong to region
def filter_region(regions, bssid_value):
    filtered_region = {}
    for key, bssid in regions.items():
        if bssid == bssid_value:
            filtered_region[key] = bssid
    return filtered_region

def extract_region_data(fp_data, filter_region):
    extracted_data = {}
    for key, data in fp_data.items():
        if key in filter_region:
            extracted_data[key] = data
    return extracted_data

def select_region(posX, posY, test_Point_Region, region_select, region_data, img):
    selected_region = {}
    key, value = next(iter(test_Point_Region.items()))
    for i in range(len(region_select)):
        if region_select[i][0] == value:
            # select part of the dataset that refers to the correct region
            selected_region = region_data[i]
            # Draw a cirlce on map
            color = get_color(value)
            cv2.circle(img, (posX, posY), 4, color, 2)
            return selected_region

#
def sort_region_data(regions, bssid_list, fingerprint_data):
    region_select = [] # 
    r_data = [] # Contains fingerprint data, each list value is a dict corresponding to one region

    for i in range(len(bssid_list)):
        r1 = filter_region(regions, bssid_list[i][:14])
        r1_data = extract_region_data(fingerprint_data, r1)
        r_data.append(r1_data)

        r1 = [bssid_list[i][:14], r1]
        region_select.append(r1)
    
    return region_select, r_data

# GT Points
def GetCandidatePos(online, fpdb, temp_k):
    #print(online.keys())
    candidates = []
    #print(fpdb)
    for key in fpdb.keys():
        #print(key)
        candidate = fpdb[key]
        #print(candidate)
        #print()
        #print(candidate)
        errRSSI = []
        k = temp_k  # k is the number of Neighbouring WiFi access points
        for bssid in candidate.keys():
            #print(bssid)
            if bssid in online.keys():
                # look at the first K with the same bssid?
                if k == 0:
                    break
                k = k - 1
                #print("found RSSI")
                errRSSI.append(abs(candidate[bssid] - online[bssid]))
                #print(abs(candidate[bssid] - online[bssid]))
        #print(errRSSI)
        if errRSSI:
            average = sum(errRSSI) / len(errRSSI)
            #print(average)
            candidates.append([key, average])
        

    # Step  select final position candidate
    candidates.sort(key=sortonerror)
    #print()
    #print(candidates[1])
    return candidates[0]

# draw all reference points (RP)
def draw_circles(img, regions):
    for key, bssid in regions.items():
        loc = key.split('_') # split the key into x and y cooridates
        posX = int(loc[0])
        posY = int(loc[1])
        color = get_color(bssid) # get a color for each key based on the BSSID 
        cv2.circle(img, (posX, posY), 4, color, 2)




# Use this to open the CSV file
def open_CSV(filepath, img, temp_k, ErrorList, PredictionTime, region_select, r_data, bssid_list, test_map):
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        for gtPtInfo in reader: 
            gtPtX = int(gtPtInfo[1])
            gtPtY = int(gtPtInfo[2])
            gtPtFile = gtPtInfo[3]
            fileName = gtPtFile
            listScans = []

            test_filepath = test_map + fileName + ".txt"

            start_time = time.time()

            open_test(test_filepath, listScans, gtPtX, gtPtY, img, temp_k, ErrorList, region_select, r_data, bssid_list)

            end_time = time.time()
            duration = end_time - start_time
            PredictionTime.append(duration)

    return PredictionTime, ErrorList


# Use this to open the Test Point Files
def open_test(filepath, listScans, gtPtX, gtPtY, img, temp_k, ErrorList, region_select, r_data, bssid_list):
    with open(filepath, 'r') as fileGT:
        reader = csv.reader(fileGT, delimiter=';')
        scanid = 0
        prvTag = "NONE"
        listBSSIDnRSSI = {}

        # Read Line in the file and extract info
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

        # Select Test Points Region
        tpMap = {}
        tpPosition = str(gtPtX) + "_" + str(gtPtY)
        tpMap[tpPosition] = listBSSIDnRSSI
        tpRegion = find_highest_rssi_bssid(tpMap, bssid_list) # one pos and one bssid (region)

        selected_region = select_region(gtPtX, gtPtY, tpRegion, region_select, r_data, img)
        
        # Order the information after RSSI strenght (heighest to lowest)
        if listScans:
            listScans[-1][1] = sort_dict_by_rssi(listScans[-1][1])

        listScans = [[1, listBSSIDnRSSI]]

        #print(len(listScans))
        for scan in listScans:
            #print(scan)
            onlineScan = scan[1]
            locXY, errRSSI = GetCandidatePos(onlineScan, selected_region, temp_k)

            #draw_circles(img, locXY)

            loc = locXY.split('_')
            posX = int(loc[0])
            posY = int(loc[1])
            cv2.circle(img, (posX, posY), 4, (0, 0, 0), 2) # draw circle for predicted
            #print(posX, posY)

            # example Line
            cv2.line(img, (gtPtX, gtPtY), (posX, posY), (0, 255, 0), 2) # line between acutal and predicted
            #print((posX, posY), (gtPtX, gtPtY))
            ErrorList.append(abs(distance((posX, posY), (gtPtX, gtPtY)) / 35.7))





#calculate_results(end_total_time, start_total_time, end_init_time, start_init_time, ErrorList, PredictionTime, 'precision_histogram_region.png', temp_k)

#show_save_image(img)
