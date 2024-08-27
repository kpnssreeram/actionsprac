import boto3
import time
import sys

INSTANCES = [
    "i-064b7b60c22f68885",
    "i-09f67bd435c4c6e4d"
]

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

def runCanaryAckScript(aws_region):
    ssm_client = boto3.client('ssm', region_name=aws_region)
    
    for instance in INSTANCES:
        command = ssm_client.send_command(
            InstanceIds=[instance],
            DocumentName="AWS-RunShellScript",
            Comment="Debug and Run Script",
            Parameters={
                'commands': [
                    "ls -la /",
                    "cd /shovel || cd ~/shovel || echo \"Failed to find shovel directory\"",
                    f"nohup python3 canaryack.py eu-west-1 > outputcanaryAck.log 2>&1 &"
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
    
    if function_name == "runCanaryAckScript":
        runCanaryAckScript(aws_region)
    else:
        print(f"Unknown function: {function_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()