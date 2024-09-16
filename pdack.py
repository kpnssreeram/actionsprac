import os
import json
from datetime import datetime, timedelta
from pdpyras import APISession

PAGERDUTY_API_KEY = os.environ.get('PAGERDUTY_API_KEY')
ACKNOWLEDGED_FILE = 'acknowledged_incidents.json'
EXCLUDED_KEYWORD = 'solr'

# Initialize PagerDuty API session
session = APISession(PAGERDUTY_API_KEY)

def get_new_incidents():
    # Get incidents from the last 24 hours
    since = (datetime.utcnow() - timedelta(days=1)).isoformat()
    incidents = session.list_all('incidents', params={
        'since': since,
        'statuses[]': ['triggered', 'acknowledged'],
        'sort_by': 'created_at:desc'
    })
    return incidents

def load_acknowledged_incidents():
    if os.path.exists(ACKNOWLEDGED_FILE):
        with open(ACKNOWLEDGED_FILE, 'r') as f:
            return json.load(f)
    return []

def save_acknowledged_incidents(incidents):
    with open(ACKNOWLEDGED_FILE, 'w') as f:
        json.dump(incidents, f)

def acknowledge_incident(incident_id):
    try:
        session.rput(f'/incidents/{incident_id}', json={
            'incident': {
                'type': 'incident_reference',
                'status': 'acknowledged'
            }
        })
        print(f"Incident {incident_id} acknowledged successfully")
        return True
    except Exception as e:
        print(f"Error acknowledging incident {incident_id}: {str(e)}")
        return False

def should_process_incident(incident):
    # Check if the excluded keyword is in the title or description
    if EXCLUDED_KEYWORD.lower() in incident['title'].lower():
        return False
    if incident['description'] and EXCLUDED_KEYWORD.lower() in incident['description'].lower():
        return False
    return True

def main():
    new_incidents = get_new_incidents()
    acknowledged_incidents = load_acknowledged_incidents()

    for incident in new_incidents:
        if incident['id'] not in acknowledged_incidents and incident['status'] == 'triggered':
            if should_process_incident(incident):
                if acknowledge_incident(incident['id']):
                    acknowledged_incidents.append(incident['id'])
                    print(f"New incident acknowledged: {incident['id']} - {incident['title']}")
            else:
                print(f"Skipping incident (contains '{EXCLUDED_KEYWORD}'): {incident['id']} - {incident['title']}")

    save_acknowledged_incidents(acknowledged_incidents)

if __name__ == "__main__":
    main()