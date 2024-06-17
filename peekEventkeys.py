import boto3
from botocore.config import Config
import requests
import csv
import time
import json
import subprocess
import sys

# AWS SSO profile name
profile_name = 'emodb-nexus-qa'

# Create a session using your AWS SSO profile
session = boto3.Session(profile_name=profile_name)
credentials = session.get_credentials().get_frozen_credentials()

# Use the credentials to sign the request if necessary
# base_url = "http://emodb.bazaar.us-east-1.nexus.bazaarvoice.com:8080/bus/1/stash-incremental-sor-ugc/"
if len(sys.argv) > 1:
    api_key_val = sys.argv[1]
    base_url = sys.argv[2]
    time_to_run = float(sys.argv[3])
else:
    print("Please provide a value for the API key and base URL as a command line argument.")
    sys.exit(1)

def send_curl_request(event_keys):
    url = base_url + "ack"
    event_data = json.dumps(event_keys)
    headers = f'X-BV-API-Key: {api_key_val}'
    curl_command = [
        'curl',
        '--location',
        url,
        '--header', headers,
        '--header', 'Content-Type: application/json',
        '--data', event_data
    ]
    try:
        subprocess.run(curl_command, check=True)
        print("   Request successful!")
    except subprocess.CalledProcessError as e:
        print("Request failed with status code:", e.returncode)

def get_data_size():
    url = base_url + "size"
    headers = {
        "X-BV-API-Key": api_key_val
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response
    else:
        return "Failed to retrieve data size. Status code: " + str(response.status_code)

url = base_url + "peek?limit=3000"
headers = {
    "X-BV-API-Key": api_key_val
}
print(f'X-BV-API-Key: {api_key_val}')

start_time = time.time()
print(start_time)
while time.time() - start_time < time_to_run:
    print(time.time() - start_time)
    response = get_data_size()
    size_data = response.json()
    if isinstance(size_data, (int, float)):
        print(f"Number of events in databus: {size_data}")
    else:
        print("Failed to retrieve data size. Status code: " + str(response.status_code))
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        event_ids = []
        event_keys = []
        count = 0
        for index, item in enumerate(data):
            if item['content']['~version'] == 0:
                count += 1
                event_keys.append(item['eventKey'])
                event_ids.append([item['eventKey'], item['content']['~id'], item['content']['client'], item['content']['~table']])
        print(f"Number of phantom events: {count}")
        if count > 0:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            filename = f"event_ids_peek_us_east1_{timestamp}.csv"
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['eventKey', '~id', 'client', 'table'])
                writer.writerows(event_ids)
            print("CSV file created successfully.")
            event_data = json.dumps(event_keys)
            print("event_keys")
            print(event_data)
            send_curl_request(event_keys)
        else:
            print("No phantom events")
    else:
        print("Error: Failed to fetch data from the API.")
    time.sleep(30)
