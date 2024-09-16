import os
import json
from datetime import datetime, timedelta
from pdpyras import APISession

PAGERDUTY_API_KEY = os.environ.get('PAGERDUTY_API_KEY')
EXCLUDED_KEYWORD = 'solr'
YOUR_USER_ID = 'PYUFFMG'  # Replace with your PagerDuty user ID
YOUR_TEAM_IDS = ['PSQP0BX', 'PA1YFHI']  # Replace with your team IDs

session = APISession(PAGERDUTY_API_KEY)

def get_incidents():
    """
    Fetch incidents that are either acknowledged or triggered within the last 24 hours.
    """
    since = (datetime.utcnow() - timedelta(days=1)).isoformat()
    incidents = session.list_all('incidents', params={
        'since': since,
        'statuses[]': ['triggered', 'acknowledged'],  # Fetch triggered and acknowledged incidents
        'sort_by': 'created_at:desc'
    })
    return incidents

def print_incident_details(incidents):
    """
    Print details of the incidents, including ID, title, status, and assignees.
    """
    for incident in incidents:
        if EXCLUDED_KEYWORD.lower() not in incident['title'].lower():
            print(f"\nIncident ID: {incident['id']}")
            print(f"Title: {incident['title']}")
            print(f"Status: {incident['status']}")
            print("Assignees:")
            
            if 'assignments' in incident and incident['assignments']:
                for assignment in incident['assignments']:
                    assignee = assignment['assignee']
                    print(f"- {assignee['summary']} (ID: {assignee['id']})")
            else:
                print("No assignees for this incident.")
            
            print("-" * 40)

def main():
    # Get incidents within the last 24 hours
    incidents = get_incidents()
    
    if incidents:
        print(f"Found {len(incidents)} incidents.")
        # Print details of each incident (ID, title, status, and assignees)
        print_incident_details(incidents)
    else:
        print("No incidents found.")

if __name__ == "__main__":
    main()
