import shelve

import requests
from cloudpathlib import CloudPath
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from pygle import network
from wigle import check_if_BSSID_exists_REST, check_if_BSSID_exists
from collections import Counter

def print_shelve(shelve_file):
    shelve_dict = shelve.open(shelve_file)
    dkeys = list(shelve_dict.keys())
    # dkeys.sort()
    for x in dkeys:
        print(x, shelve_dict[x])
    shelve_dict.close()

def analyse_BSSIDs(BSSID_list):
    count_visibles = 0
    total = len(BSSID_list)
    # BSSID = 'c0:ac:54:f8:b4:a4'
    wigle_cache = shelve.open('wigle_cache.py')
    # print_shelve('wigle_cache.py')

    print(wigle_cache)
    # del wigle_cache['c0:ac:54:f8:b4:a4']
    for BSSID in BSSID_list:
        if BSSID not in wigle_cache:
            try:
                # result_code = check_if_BSSID_exists(BSSID)
                result_code = network.detail(netid=BSSID)

                wigle_cache[BSSID] = result_code

                count_visibles += 1
                # found in WiGLE database
                print('Inserted to cache. BSSID:', BSSID + ',', 'Result:', result_code)
            except Exception as e:
                # not found or other error
                # print(BSSID, e.args[0][0:3])
                if e.args[0][0:3] == '429':
                    break
                wigle_cache[BSSID] = e.args[0].split(':')[0]
                print('Inserted to cache. BSSID:', BSSID + ',', 'Result:', e.args[0].split(':')[0])
        else:
            print('Already in cache. BSSID:', BSSID + ',', 'Result:', wigle_cache[BSSID])

    wigle_cache.close()
    print('Total visible networks:', count_visibles, 'out of', total)


def analyse_securities(securities):
    index = 0
    # securities = securities[securities.Capabilities!='[IBSS]']
    # for security in securities:
    #     if 'IBSS' in security:
    #         securities.drop(index)
    #     index += 1

    counts = securities.value_counts()
    total = len(securities)
    print(counts)
    amounts = []
    has_WPA2_ONLY = 0
    has_WPA = 0
    opened = 0

    for security in securities:
        amount = security.count('[')
        # print(amount)
        amounts.append(amount)
        if amount <= 1:
            opened += 1
        if 'WPA2' in security and 'WPA-' not in security:
            has_WPA2_ONLY += 1
        elif 'WPA' in security:
            has_WPA += 1

    print()
    print('Total networks:', total)
    print('Opened networks:', opened)
    print('Networks which has WPA2 and not WPA:', has_WPA2_ONLY)
    print('Networks which has WPA:', has_WPA)

    # print(amounts)
    # print(counts)
    # print(counts['[ESS]'])
    print()
    histogram = Counter(amounts)
    print('Amount of securities histogram:')
    print(histogram)
    risk_grade = 0
    length = len(amounts)
    for item in histogram:
        risk_grade += item*(histogram[item])
    # the more securities, the more the risk is lower, so dividing.
    risk_grade = 1/risk_grade if risk_grade != 0 else 1
    # risk_grade = risk_grade/length
    average = sum(amounts)/length
    print('securities average:', average)
    print('securities risk grade:', 1/average)

if __name__ == '__main__':

    # cp = CloudPath("s3://storagebucketname130605-dev/private/us-east-1:decaf162-e212-4ee2-96e4-adea45f7d0f6/d46aa25e-8467-4cd4-a1ee-bc3df67fb73d/")
    # cp.download_to("ofir")

    # use glob to get all the csv files
    # in the folder
    # path = os.getcwd() + '/ofir'
    # csv_files = glob.glob(os.path.join(path, "*.csv"))
    # # #
    # df = pd.read_csv(csv_files[0])
    # # # loop over the list of csv files
    # for f in csv_files[1:]:
    #     # read the csv file
    #     df1 = pd.read_csv(f)
    #     df = pd.concat([df, df1])
    # #
    # #     # print the location and filename
    # #     # print('Location:', f)
    # #     # print('File Name:', f.split("\\")[-1])
    # #
    # #     # print the content
    # #     # print('Content:')
    # #     # print(df)
    # #     # print()
    # #
    # df.to_csv('ofir_total.csv')

    df = pd.read_csv('ofir_total.csv')

    # BSSID_list = df['BSSID']
    # analyse_BSSIDs(BSSID_list)
    # print_shelve('wigle_cache.py')

    securities_list = df[df.Capabilities!='[IBSS]']
    securities_list = securities_list['Capabilities']

    analyse_securities(securities_list)


    # df[df['Timestamp'] == '6 days']['SSID'].to_csv('ofek_total_6_days.csv')
    # print(df['Timestamp'].value_counts())
    # print(df[df['Timestamp'] == '5 days']['SSID'].value_counts())
    # print(dfc)
    # df1 = df['SSID'].value_counts()

    # df['SSID'].value_counts().plot(kind='bar')
    # plt.title("Number of appearances per network")
    #
    # plt.xlabel("Network SSID")
    # plt.ylabel("Appearances")
    # plt.tight_layout()
    # plt.savefig('ofirSSID_hist.png')
    # plt.show()
    # print(df['Timestamp'].unique().tolist())
    # df = df.astype(str)
    # plt.figure(figsize=(10, 6))
    #
    # plt.scatter(df.SSID, df.Timestamp, c='g', s=5)
    # plt.xlabel("Network SSID")
    # plt.ylabel("Number of days")
    # plt.title("Number of days from the first appearance for each network")
    # plt.grid()
    # plt.tight_layout()
    # plt.savefig('ofirTimestamp_SSID.png')
    # plt.show()

