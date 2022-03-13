import json
import requests
from pygle import network
from requests.auth import HTTPBasicAuth

# url for config file: C:\Users\ofira\Anaconda3\Lib\site-packages\pygle\config.py
def check_if_BSSID_exists(BSSID):
    return network.detail(netid=BSSID)

def check_if_BSSID_exists_REST(BSSID):
    report_url = 'https://api.wigle.net/api/v2/network/detail'
    # params = {'Authorization':'Basic ',
    #           'netid': BSSID}
    params = {'netid': BSSID}
    # sending request to WiGLE API and get a response:
    response = requests.get(report_url, params=params)

    if response.status_code == 401:
        response = requests.get('https://api.wigle.net/api/v2/network/detail',
                                auth=HTTPBasicAuth('networisk', 'ofirofek123'))

    return response.status_code
