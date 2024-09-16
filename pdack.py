import os
import json
from datetime import datetime, timedelta
from pdpyras import APISession

PAGERDUTY_API_KEY = os.environ.get('PAGERDUTY_API_KEY')
EXCLUDED_KEYWORD = 'solr'
ASSIGNED_USER_ID = 'PYUFFMG'  # Replace with the user ID you want to check for assignments
SERVICE_IDS = ['P0L4T9G', 'PJ06DY7']  # Replace with your list of service IDs

session = APISession(PAGERDUTY_API_KEY)

def get_incidents():
    """
    Fetch incidents that are either acknowledged or triggered within the last 24 hours
    for the specified services.
    """
    incidents = session.list_all('incidents', params={
        'statuses[]': ['triggered', 'acknowledged'],
        'service_ids[]': SERVICE_IDS,
        'sort_by': 'created_at:desc'
    })
    return incidents

def is_assigned_to_user(incident, user_id):
    """
    Check if the incident is assigned to the specified user.
    """
    if 'assignments' in incident:
        return any(assignment['assignee']['id'] == user_id for assignment in incident['assignments'])
    return False

def acknowledge_incident(incident_id):
    """
    Acknowledge the specified incident.
    """
    try:
        session.rput(f'/incidents/{incident_id}', json={
            'incident': {
                'type': 'incident_reference',
                'status': 'acknowledged'
            }
        })
        print(f"Incident {incident_id} has been acknowledged.")
    except Exception as e:
        print(f"Failed to acknowledge incident {incident_id}: {str(e)}")

def process_and_print_incidents(incidents):
    """
    Process incidents: acknowledge if triggered, exclude if title contains 'solr',
    and print details if assigned to the specified user.
    """
    for incident in incidents:
        if EXCLUDED_KEYWORD.lower() in incident['title'].lower():
            continue  # Skip this incident if it contains 'solr' in the title

        if incident['status'] == 'triggered':
            acknowledge_incident(incident['id'])

        if is_assigned_to_user(incident, ASSIGNED_USER_ID):
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
        print("Processing incidents...")
        process_and_print_incidents(incidents)
    else:
        print("No incidents found.")

if __name__ == "__main__":
    main()