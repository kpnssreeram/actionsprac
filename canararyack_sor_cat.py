##nohup python3 canaryack_sor_cat.py --aws-region eu-west-1 > outputcanaryAck.log 2>&1 &
import requests
import csv
import time
import json
import logging
import sys
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app_cat.log"),
                        logging.StreamHandler()
                    ])

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--aws-region', required=True, help='AWS region (e.g., us-east-1 or eu-west-1)')
args = parser.parse_args()

# Extract the AWS region from command-line arguments
aws_region = args.aws_region

# Set the base_url dynamically based on the AWS region
base_url = f"http://emodb.bazaar.{aws_region}.nexus.bazaarvoice.com:8080/bus/1/__system_bus:canary-bazaar_sor_cat_default/"
api_key_val = "bazaar_admin"
time_to_run = float(120000)

# Extract the second to last part of the base_url
base_url_parts = base_url.rstrip('/').split('/')
if len(base_url_parts) > 1:
    url_identifier = base_url_parts[-1]
else:
    url_identifier = base_url

def send_post_request(event_keys):
    url = base_url + "ack"
    event_data = json.dumps(event_keys)
    headers = {
        'X-BV-API-Key': api_key_val,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=event_data)
        response.raise_for_status()
        logging.info("Request successful!")
    except requests.RequestException as e:
        logging.error("Request failed: %s", e)

def get_data_size():
    url = base_url + "size"
    headers = {
        "X-BV-API-Key": api_key_val
    }

    response = requests.get(url, headers=headers)
    return response

# Define the API endpoint
url = base_url + "peek?limit=3000"

# Define headers with the API key
headers = {
    "X-BV-API-Key": api_key_val
}

logging.info("API Key Header: %s", headers)

# Track the start time
start_time = time.time()
logging.info("Start time: %s", start_time)

# Run the loop for the specified duration
while time.time() - start_time < time_to_run:
    logging.info("Elapsed time: %s", time.time() - start_time)
    logging.info("Subscription Name: %s", url_identifier)

    response = get_data_size()
    logging.info("Data size response: %s", response)

    if response.status_code == 200:
        size_data = response.json()
        if isinstance(size_data, (int, float)):
            logging.info("Number of events in databus %s: %s", url_identifier, size_data)
        else:
            logging.error("Unexpected size data format: %s", size_data)
    else:
        logging.error("Failed to retrieve data size. Status code: %s", response.status_code)

    response = requests.get(url, headers=headers)
    logging.info("Response Status code: %s", response.status_code)

    if response.status_code == 200:
        data = response.json()
        event_ids = []
        event_keys = []
        count = 0

        for index, item in enumerate(data):
            count += 1
            event_keys.append(item['eventKey'])
            event_ids.append([item['eventKey'], item['content']['~id'], item['content']['~table']])

        logging.info("Number of events: %s", count)

        if count > 0:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            send_post_request(event_keys)
        else:
            logging.info("No events")
    else:
        logging.error("Error: Failed to fetch data from the API.")

    time.sleep(2)