import os
import json
from datetime import datetime, timedelta
from pdpyras import APISession

PAGERDUTY_API_KEY = os.environ.get('PAGERDUTY_API_KEY')
EXCLUDED_KEYWORD = 'solr'
ASSIGNED_USER_ID = 'PYUFFMG'  # Replace with the user ID you want to check for assignments
SERVICE_IDS = ['P0L4TG', 'PJ06DY7']  # Replace with your list of service IDs

session = APISession(PAGERDUTY_API_KEY)

def get_incidents():
    """
    Fetch incidents that are either acknowledged or triggered within the last 24 hours
    for the specified services.
    """
    since = (datetime.utcnow() - timedelta(days=1)).isoformat()
    incidents = session.list_all('incidents', params={
        'since': since,
        'statuses[]': ['triggered', 'acknowledged'],
        'service_ids[]': SERVICE_IDS,
        'sort_by': 'created_at:desc'
    })
    return incidents

# def is_assigned_to_user(incident, user_id):
#     """
#     Check if the incident is assigned to the specified user.
#     """
#     if 'assignments' in incident:
#         return any(assignment['assignee']['id'] == user_id for assignment in incident['assignments'])
#     return False

def print_incident_details(incidents):
    """
    Print details of the incidents assigned to the specified user.
    """
    for incident in incidents:
        # if EXCLUDED_KEYWORD.lower() not in incident['title'].lower() and is_assigned_to_user(incident, ASSIGNED_USER_ID):
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
        # assigned_incidents = [inc for inc in incidents if is_assigned_to_user(inc, ASSIGNED_USER_ID)]
        # print(f"Found {len(assigned_incidents)} incidents assigned to the specified user.")
        # Print details of each incident assigned to the specified user
        print_incident_details(incidents)
    else:
        print("No incidents found.")

if __name__ == "__main__":
    main()