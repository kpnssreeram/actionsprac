import os
import json
from datetime import datetime, timedelta
from pdpyras import APISession

# Environment variables
PAGERDUTY_API_KEY = os.environ.get('PAGERDUTY_API_KEY')
EXCLUDED_KEYWORD = 'solr'
SERVICE_IDS = ['P0L4T9G', 'PJ06DY7']  # Replace with your list of service IDs

# Initialize PagerDuty API session
session = APISession(PAGERDUTY_API_KEY)

def get_incidents():
    """
    Fetch all incidents that are either acknowledged or triggered
    for the specified services.
    """
    incidents = session.list_all('incidents', params={
        'statuses[]': ['triggered', 'acknowledged'],
        'service_ids[]': SERVICE_IDS,
        'sort_by': 'created_at:desc'
    })
    return incidents


def print_incident_details(incidents):
    """
    Print details of the incidents.
    """
    for incident in incidents:
        # Exclude incidents containing the excluded keyword in the title
        if EXCLUDED_KEYWORD.lower() not in incident['title'].lower():
            print(f"\nIncident ID: {incident['id']}")
            print(f"Title: {incident['title']}")
            print(f"Status: {incident['status']}")
            print(f"Service: {incident['service']['summary']} (ID: {incident['service']['id']})")
            print("Assignees:")
            
            for assignment in incident['assignments']:
                assignee = assignment['assignee']
                print(f"- {assignee['summary']} (ID: {assignee['id']})")
            
            print("-" * 40)

def main():
    # Get incidents within the last 24 hours
    incidents = get_incidents()
    
    if incidents:
        # Print details of each incident
        print_incident_details(incidents)
    else:
        print("No incidents found.")

if __name__ == "__main__":
    main()
