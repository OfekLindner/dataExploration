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
from mac_vendor_lookup import MacLookup
from time import strptime
import datetime


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
        risk_grade += item * (histogram[item])
    # the more securities, the more the risk is lower, so dividing.
    risk_grade = 1 / risk_grade if risk_grade != 0 else 1
    # risk_grade = risk_grade/length
    average = sum(amounts) / length
    print('securities average:', average)
    print('securities risk grade:', 1 / average)


def addVendors(networkData: pd.DataFrame):
    vendors = []
    for _, row in networkData.iterrows():
        try:
            vendors.append(MacLookup().lookup(row['BSSID']))
        except:
            vendors.append(np.nan)
    networkData['vendor'] = vendors
    return networkData


def downloadFromS3(sourceFolderName, desFolderName):
    bucketName = "storagebucketname130605-dev/private/us-east-1:decaf162-e212-4ee2-96e4-adea45f7d0f6/"
    cp = CloudPath("s3://" + bucketName + sourceFolderName + "/")
    cp.download_to(desFolderName)


def mergeAllFiles(FolderName):
    path = os.getcwd() + "/" + FolderName
    csv_files = glob.glob(os.path.join(path, "*.csv"))
    networkData = pd.read_csv(csv_files[0])
    for f in csv_files[1:]:
        networkData1 = pd.read_csv(f)
        networkData = pd.concat([networkData, networkData1])
    return networkData


def changeScanTimeType(networkData: pd.DataFrame):
    scanTimes = []
    for _, row in networkData.iterrows():
        st = row['ScanTime'].split()
        mon = int(strptime(st[1], '%b').tm_mon)
        stTime = st[3].split(":")
        stTime = list(map(int, stTime))
        st = datetime.datetime(int(st[5]), mon, int(st[2]), stTime[0], stTime[1], stTime[2])
        scanTimes.append(st)
    networkData['ScanTime'] = scanTimes
    return networkData


def presenceDensity(fileName="Test444") -> pd.DataFrame:
    networkData = pd.read_csv(fileName + ".csv")

    df = networkData.drop_duplicates(subset=["BSSID", "ScanTime"])
    scanCount = df["ScanTime"].nunique()
    df = df.groupby(['BSSID', 'SSID'])[['BSSID', 'SSID']].size().sort_values(ascending=True).reset_index(name='counts')
    # print(df)
    conditions = [
        (df['counts'] / scanCount >= 2 / 3),
        (df['counts'] / scanCount >= 1 / 18) & (df['counts'] / scanCount < 2 / 3),
        (df['counts'] / scanCount < 1 / 18)
    ]

    values = ['persistent', 'occasional', 'rare']

    df['Presence Density'] = np.select(conditions, values)
    df1 = df[["BSSID", "SSID", "Presence Density"]].copy()

    # print(type(df1))
    return df1  # BSSID SSID Presence Density


def calcLifetime(r):
    return round((r['maxScanTime'] - r['minScanTime']).seconds / 3600, 2) + (r['maxScanTime'] - r['minScanTime']).days * 24


def lifetime(fileName="Test444"):
    networkData = pd.read_csv(fileName + ".csv")
    networkData = networkData.drop_duplicates(subset=["BSSID", "ScanTime"])

    networkData = changeScanTimeType(networkData)
    ScanTimes = networkData.groupby(['BSSID', 'SSID']).agg(
        minScanTime=('ScanTime', 'min'),
        maxScanTime=('ScanTime', 'max')).reset_index(['BSSID', 'SSID'])
    print(ScanTimes)
    ScanTimes['lifetime'] = ScanTimes.apply(lambda row: calcLifetime(row), axis=1)
    # BSSID SSID minScanTime maxScanTime lifetime
    return ScanTimes[['BSSID', 'SSID', 'lifetime']]


def analyse_securities1(r):
    return r['Capabilities'].count('[') <= 1


def hasWPA2only(r):
    return 'WPA2' in r['Capabilities'] and 'WPA-' not in r['Capabilities']


def hasWPA(r):
    if 'WPA2' in r['Capabilities'] and 'WPA-' not in r['Capabilities']:
        return False
    elif 'WPA' in r['Capabilities']:
        return True
    return False


def securities(fileName="Test444"):
    networkData = pd.read_csv(fileName + ".csv")

    df = networkData.drop_duplicates(subset=["BSSID", "ScanTime"])
    df = df[['BSSID', 'SSID','Capabilities']].drop_duplicates()

    df['Open'] = df.apply(lambda row: analyse_securities1(row), axis=1)

    df['WPA2 Only'] = df.apply(lambda row: hasWPA2only(row), axis=1)

    df['WPA'] = df.apply(lambda row: hasWPA(row), axis=1)

    return df[['BSSID','SSID','Open','WPA2 Only','WPA']]


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    sourceFolderName = "Test444"
    # desFolderName = "Test444"
    # downloadFromS3(sourceFolderName,"ofekScans-21-3")
    # networkData = mergeAllFiles("ofekScans-21-3")
    # networkData.to_csv("ofekScans-21-3" + ".csv")
    # networkData = pd.read_csv("ofekScans-21-3" + ".csv")
    # df = networkData[networkData.Capabilities != '[IBSS]']
    # df.to_csv("ofekScans-21-3" + ".csv")
    # df = pd.read_csv("ofekScans-21-3.csv")

    # s = securities("ofekScans-21-3")
    #
    # p = presenceDensity("ofekScans-21-3")
    #
    # l = lifetime("ofekScans-21-3")
    #
    # df = p.merge(l)
    # df = df.merge(s)
    # df.to_csv("MERGE-ofekScans-21-3.csv")
    df = pd.read_csv("MERGE-ofekScans-21-3.csv")
    presenceDensity = df['Presence Density'].value_counts().rename(index='')
    ax = presenceDensity.plot(kind='pie')
    ax.set_title("Presence Density")
    plt.tight_layout()
    plt.show()

    sec = df[['Open','WPA2 Only','WPA']].value_counts().rename(index='')
    ax = sec.plot(kind='pie')
    ax.set_title("Securities distribution - Open, WPA2 only, WPA")
    plt.tight_layout()
    plt.show()

    df.value_counts('lifetime').sort_index(ascending=False).plot(kind='barh')
    plt.xlabel("Amount of networks")
    plt.ylabel("Lifetime [hours]")
    plt.tight_layout()
    plt.show()

    # downloadFromS3(sourceFolderName,desFolderName)
    # networkData = mergeAllFiles(desFolderName)
    # networkData.to_csv(desFolderName + ".csv")
    # networkData = addVendors(networkData)
    # networkData.to_csv(desFolderName + ".csv")

    # networkData = changeScanTimeType(networkData)
    # # networkData.to_csv("changeScanTimeType.csv")
    # # networkData = pd.read_csv(desFolderName + ".csv")
    # #
    # ScanTimes = networkData.groupby(['BSSID']).agg({'ScanTime': ['min', 'max']})
    # ScanTimes.to_csv("ScanTimes.csv")
    # # ScanTimes = pd.read_csv("ScanTimes.csv")
    # # ScanTimes = ScanTimes.drop(labels=[0,1], axis=0)
    # # print(ScanTimes.columns)
    #
    # minDate = ScanTimes[('ScanTime', 'min')]
    # maxDate = ScanTimes[('ScanTime', 'max')]
    # # for i, x in enumerate(minDate):
    # #     print(x)
    #
    # timePeriods = []
    # for idx, minDateVal in enumerate(minDate):
    #     timePeriods.append(round((maxDate[idx] - minDateVal).seconds / 3600, 2))
    # ScanTimes['timePeriod'] = timePeriods
    # ScanTimes.to_csv("timePeriods.csv")
    # ScanTimes.value_counts('timePeriod').sort_index(ascending=False).plot(kind='barh')
    # plt.xlabel("Amount of networks")
    # plt.ylabel("Duration from first to last appearance (hours)")
    # # plt.title("Mince Pie Consumption 18/19")
    #
    # plt.tight_layout()
    # plt.show()

    # addVendors(pd.read_csv('Test444.csv'))
    # df.to_csv('ofir_total.csv')
    #
    # df = pd.read_csv('ofir_total.csv')
    #
    # # BSSID_list = df['BSSID']
    # # analyse_BSSIDs(BSSID_list)
    # # print_shelve('wigle_cache.py')
    #
    # securities_list = df[df.Capabilities != '[IBSS]']
    # securities_list = securities_list['Capabilities']
    #
    # analyse_securities(securities_list)

    # df[df['Timestamp'] == '6 days']['SSID'].to_csv('ofek_total_6_days.csv')
    # print(df['Timestamp'].value_counts())
    # print(df[df['Timestamp'] == '5 days']['SSID'].value_counts())
    # print(dfc)
    # df1 = df['SSID'].value_counts()

    # # df[df['Timestamp'] == '6 days']['SSID'].to_csv('ofek_total_6_days.csv')
    # # print(df['Timestamp'].value_counts())
    # # print(df[df['Timestamp'] == '5 days']['SSID'].value_counts())
    # # print(dfc)
    # # df1 = df['SSID'].value_counts()
    #
    # # df['SSID'].value_counts().plot(kind='bar')
    # # plt.title("Number of appearances per network")
    # #
    # # plt.xlabel("Network SSID")
    # # plt.ylabel("Appearances")
    # # plt.tight_layout()
    # # plt.savefig('ofirSSID_hist.png')
    # # plt.show()
    # # print(df['Timestamp'].unique().tolist())
    # df = df.astype(str)
    # plt.figure(figsize=(10, 6))
    #
    # plt.scatter(df.SSID, df.Timestamp, c='g', s=5)
    # plt.xlabel("Network SSID")
    # plt.ylabel("Number of days")
    # plt.title("Number of days from the first appearance for each network")
    # plt.grid()
    # plt.tight_layout()
    # # plt.savefig('ofirTimestamp_SSID.png')
    # # plt.show()
    # # print(df['Timestamp'].unique().tolist())
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
