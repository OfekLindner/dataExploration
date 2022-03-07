from cloudpathlib import CloudPath
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from pygle import network

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
    df = df.astype(str)
    plt.figure(figsize=(10, 6))

    plt.scatter(df.SSID, df.Timestamp, c='g', s=5)
    plt.xlabel("Network SSID")
    plt.ylabel("Number of days")
    plt.title("Number of days from the first appearance for each network")
    plt.grid()
    plt.tight_layout()
    plt.savefig('ofirTimestamp_SSID.png')
    plt.show()

