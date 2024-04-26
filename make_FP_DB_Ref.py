import cv2
import csv
import pandas as pd

# Phase 1: Fingureprinting Calibration
#Off-line Finger printing generation

# Step 1
img = cv2.imread('images/output_image.png') #NIK- Chnage the name with your map img
# height, width
height = img.shape[0]
width = img.shape[1]

h = 0

print("Image Size (W,H):" , width , height)

# Step 1   Read Raw scan files
# change the csv file with your referencd points database (One with log files name)
with open('CSV/Ref All.csv', 'r') as file:
    # List of SSIDs to filter
    ssid_list = ["HV-HYBRID", "HV-GUEST", "HV-INTERNAL", "HV-COF", "eduroam"]
    bssids_not_used = ["48:8b:0a:cb:67:", ]
    
    data = []
    reader = csv.reader(file)
    for refPtInfo in reader:
        #print(gtPtInfo)
        if(refPtInfo[0] == "ID"):
            continue
        refNo = int(refPtInfo[0])
        refPtX = int(refPtInfo[1])
        refPtY = int(refPtInfo[2])
        refPtFile = refPtInfo[3]
        cv2.circle(img, (refPtX,refPtY), 4,(0, 0, 255), 2)
        #cv2.putText(img, refPtFile, (refPtX + 15, refPtY + 15), cv2.QT_FONT_NORMAL, 0.5, (0, 0, 0), 1)

        valuePairs = {'PosX': int(refPtX), 'PosY': int(refPtY), 'PosZ': int(0)}

        fileName = refPtFile + '.txt'
        listScans=[]
        with open('a_All_Logs/' + fileName, 'r') as fileGT:
            reader = csv.reader(fileGT, delimiter=';')
            scanid = 0
            listBSSIDnRSSI = {}
            for apInfo in reader:
                #print(apInfo[0])
                if(len(apInfo)>4):
                    if apInfo[0] == "WIFI" and len(apInfo) > 4:
                        scanid = apInfo[2]
                        ssid = apInfo[3]
                        bssid = apInfo[4]
                        rssi = int(apInfo[5])
                        if ssid in ssid_list:
                            valuePairs2 = valuePairs.copy();
                            valuePairs2['SSID'] = ssid
                            valuePairs2['BSSID'] = bssid
                            valuePairs2['RSSI'] = rssi
                            data.append(valuePairs2)

        rawData = pd.DataFrame(data)
        rawData.to_csv('Data/rawData-Full.txt', sep=',')

        # Step 2  transform raw db to fingerprint db

        fpData = rawData.groupby(['PosX', 'PosY', 'PosZ', 'BSSID'])['RSSI'].mean().sort_values(ascending=False)        
        # print(fpData)

        fpData.to_csv('fpData-Full2.txt', sep=',') #this will create a database file for WiFi logs only
        print(h)
        h += 1

cv2.imshow('Output', img)

cv2.waitKey(0) 
