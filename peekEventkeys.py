import requests
import csv
import time
import json
from typing import List, Collection
import subprocess
import sys

# base_url = "http://emodb.bazaar.us-east-1.nexus.bazaarvoice.com:8080/bus/1/stash-incremental-sor-ugc/"
if len(sys.argv) > 1:
    api_key_val = sys.argv[1]
    base_url = sys.argv[2]
    time_to_run = float(sys.argv[3])
else:
    print("Please provide a value for the API key and base URL as a command line argument.")
    sys.exit(1)

def send_curl_request(event_keys):
    # API endpoint
    url = base_url+"ack"

    event_data = json.dumps(event_keys)
    # Convert event keys to JSON string
    
    headers = f'X-BV-API-Key: {api_key_val}'
    # Construct curl command
    curl_command = [
        'curl',
        '--location',
        url,
        '--header', headers,
        '--header', 'Content-Type: application/json',
        '--data', event_data
    ]

    # Execute curl command
    try:
        subprocess.run(curl_command, check=True)
        print("   Request successful!")
    except subprocess.CalledProcessError as e:
        print("Request failed with status code:", e.returncode)




def get_data_size():
    url = base_url+"size"

    headers = {
        "X-BV-API-Key": api_key_val
    }

    # Send the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Return the response
        return response
    else:
        # Return a custom error message
        return "Failed to retrieve data size. Status code: " + str(response.status_code)


# Define the API endpoint
# url = "http://emodb.bazaar.us-east-1.nexus.bazaarvoice.com:8080/bus/1/polloi_bazaar_agrippasrc_srcprdusdal-bulkdatabus/peek?limit=3000"
# url = "http://emodb.bazaar.eu-west-1.nexus.bazaarvoice.com:8080/bus/1/stash-incremental-sor-ugc/peek?limit=1000"
url = base_url+"peek?limit=3000"


# Define headers with the API key
headers = {
    "X-BV-API-Key": api_key_val
}
headers_val = f'X-BV-API-Key: {api_key_val}'
print(headers_val)

# Track the start time
start_time = time.time()
print(start_time)
# Run the loop for 1 hour ---> 3600  this is in seconds
while time.time() - start_time < time_to_run:
    print(time.time() - start_time )
    response = get_data_size()
    size_data = response.json()
    # Check if size_data is a number
    if isinstance(size_data, (int, float)):
        print(f"Number of events in databus: {size_data}")
    else:
        print("Failed to retrieve data size. Status code: " + str(response.status_code))
    # Make the GET request with headers
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Initialize a list to store eventKey and ~id pairs
        event_ids = []
        event_keys = []
        count = 0
        # Iterate over the content items
        for index, item in enumerate(data):
            if item['content']['~version'] == 0:
                count = count + 1
                event_keys.append(item['eventKey'])
                event_ids.append([item['eventKey'], item['content']['~id'], item['content']['client'], item['content']['~table']])
        
        print(f"Number of phantom events: {count}")
        if(count > 0):
            timestamp = time.strftime("%Y%m%d%H%M%S")
            filename = f"event_ids_peek_us_east1_{timestamp}.csv"
            # Write the eventKey and ~id pairs to a CSV file
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['eventKey', '~id' , 'client', 'table'])  # Write header
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


    