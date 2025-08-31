import requests
import argparse
import logging
import time

# Set up the logger
def setup_logger():
    # Create a logger
    logger = logging.getLogger("PurgeRequestLogger")
    logger.setLevel(logging.DEBUG)  # Set the minimum log level to DEBUG for detailed logging
    
    # Create handlers: one for console output and one for writing to a file
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('purge_request.log')

    # Set the level for handlers (both will capture everything including DEBUG)
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)

    # Create a logging format
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Apply the format to both handlers
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def purge_data(region, api_key, sor_type, logger, retries=3, delay=2):
    logger.info("Starting purge request")
    logger.debug(f"Received arguments - region: {region}, sor_type: {sor_type}")

    # Construct the base URL with the region passed as a parameter
    base_url = f"http://emodb.bazaar.{region}.nexus.bazaarvoice.com:8080"
    logger.debug(f"Base URL constructed: {base_url}")
    
    # Use the sortype in the endpoint
    endpoint = f"/bus/1/__system_bus:canary-bazaar_{sor_type}_default/purge"
    url = base_url + endpoint

    logger.debug(f"Constructed endpoint URL: {url}")

    # Set up the headers
    headers = {
        'X-BV-API-KEY': api_key
    }
    logger.debug(f"Headers set for request: {headers}")

    # Retry loop
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt}: Sending POST request to {url}")
            response = requests.post(url, headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                logger.info("Purge request successful")
                print("Purge request successful")
                return  # Exit the function after successful request
            else:
                logger.warning(f"Attempt {attempt}: Failed with status code: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                print(f"Attempt {attempt}: Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")

        except requests.exceptions.RequestException as e:
            # Handle any errors in the request
            logger.error(f"Attempt {attempt}: An error occurred during the request: {e}")
            print(f"Attempt {attempt}: An error occurred: {e}")

        # Wait before retrying (if it's not the last attempt)
        if attempt < retries:
            logger.info(f"Waiting {delay} seconds before retrying...")
            time.sleep(delay)

    # If all attempts fail, log an error and exit
    logger.error(f"All {retries} attempts failed. Exiting.")
    print(f"All {retries} attempts failed. Exiting.")


if __name__ == "__main__":
    # Initialize the logger
    logger = setup_logger()
    logger.info("Starting purge_request script")

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Send a POST request to purge data')

    # Add command-line arguments for region, API key, and sor_type
    parser.add_argument('--region', type=str, required=True, help='Region for the API (e.g., us-east-1, eu-west-1)')
    parser.add_argument('--apikey', type=str, required=True, help='API key for authentication')
    parser.add_argument('--sortype', type=str, required=True, choices=['sor_ugc', 'sor_cat'], help='SOR type (sor_ugc or sor_cat)')

    # Parse the arguments
    args = parser.parse_args()

    # Log the input arguments
    logger.debug(f"Command-line arguments: region={args.region}, apikey={args.apikey}, sortype={args.sortype}")

    # Call the function with the parsed arguments
    purge_data(args.region, args.apikey, args.sortype, logger)
