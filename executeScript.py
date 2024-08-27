import boto3
import time
import sys

AWS_PROFILE = "emodb-nexus-prod"  # Replace with your AWS profile if needed
INSTANCES = [
    "i-064b7b60c22f68885",
    "i-09f67bd435c4c6e4d"
]

def get_sso_session(profile_name):
    try:
        session = boto3.Session(profile_name=profile_name)
        return session
    except boto3.exceptions.ProfileNotFound:
        print(f"AWS profile '{profile_name}' not found. Please check your AWS configuration.")
        sys.exit(1)

def check_command_status(ssm_client, command_id, instance_id):
    while True:
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        status = result['Status']
        if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
            print(f"Command {command_id} on instance {instance_id} finished with status: {status}")
            if status == 'Failed':
                print(f"Error: {result.get('StandardErrorContent', 'No error message available')}")
            return status
        time.sleep(5)

def runCanaryAckScript(session, aws_region):
    ssm_client = session.client('ssm', region_name=aws_region)
    
    for instance in INSTANCES:
        command = ssm_client.send_command(
            InstanceIds=[instance],
            DocumentName="AWS-RunShellScript",
            Comment="Debug and Run Script",
            Parameters={
                'commands': [
                    "ls -la /",
                    "cd /shovel || cd ~/shovel || echo \"Failed to find shovel directory\"",
                    f"nohup python3 canaryack.py {aws_region} > outputcanaryAck.log 2>&1 &"
                ]
            }
        )
        
        command_id = command['Command']['CommandId']
        print(f"Executing Script on {instance}")
        check_command_status(ssm_client, command_id, instance)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 run_canary_script.py <function_name> <AWS_REGION>")
        sys.exit(1)

    function_name = sys.argv[1]
    aws_region = sys.argv[2]

    session = get_sso_session(AWS_PROFILE)
    
    if function_name == "runCanaryAckScript":
        runCanaryAckScript(session, aws_region)
    else:
        print(f"Unknown function: {function_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()