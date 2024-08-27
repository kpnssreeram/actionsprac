import time
import boto3
import botocore
import sys
import argparse

INSTANCE_NAMES = ["shovelAck"]

def get_sso_session():
    try:
        session = boto3.Session()
        return session
    except botocore.exceptions.NoCredentialsError:
        print("No AWS credentials found. Please check your IAM role and AWS configuration.")
        sys.exit(1)

def execute_command(ssm, instance_id, commands):
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': commands}
        )

        command_id = response['Command']['CommandId']
        print(f"Command sent to instance {instance_id}, command ID: {command_id}")

        # No need to wait for the command to complete, so the script exits after sending the command

    except botocore.exceptions.ClientError as e:
        print(f"Error executing command on instance {instance_id}: {str(e)}")
        return None

def list_instances(instance_names, region, session):
    ec2 = session.client('ec2', region_name=region)
    instances = []

    for instance_name in instance_names:
        response = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])
        if not response['Reservations']:
            print(f"No instances found with name {instance_name} in region {region}")
        else:
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'State': instance['State']['Name'],
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'Name': instance_name
                    })

    return instances

def restart_services(instance_names, region, session,exreg):
    instances = list_instances(instance_names, region, session)

    if not instances:
        print(f"No instances found in region {region} with the given names.")
        return

    for instance in instances:
        instance_id = instance['InstanceId']
        instance_name = instance['Name']
        print(f"Processing instance {instance_id} (Name: {instance_name}) in region {region}...")

        try:
            ssm = session.client('ssm', region_name=region)

            # Restart services using supervisorctl with dynamic region
            restart_command = [
               f"sudo su && cd ~/shovel && nohup python3 canaryack.py --aws-region {exreg} > outputcanaryAck.log 2>&1 &"
            ]

            print("Restarting all services...")
            execute_command(ssm, instance_id, restart_command)

            print("Waiting for 30 seconds before proceeding...")
            time.sleep(30)

        except botocore.exceptions.ClientError as e:
            print(f"Error processing instance {instance_id}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Script to execute commands on AWS EC2 instances.")
    parser.add_argument("aws_region", help="The AWS region to target.")
    
    args = parser.parse_args()

    session = get_sso_session()

    print("Listing all instances:")
    print(f"\nRegion: us-east-1")
    instances = list_instances(INSTANCE_NAMES, "us-east-1", session)
    if instances:
        for instance in instances:
            print(f"Instance ID: {instance['InstanceId']}, State: {instance['State']}, Private IP: {instance['PrivateIpAddress']}, Name: {instance['Name']}")
    else:
        print("No instances found in this region.")

    print("\nStarting service restart process:")
    print(f"\nProcessing region: us-east-1")
    restart_services(INSTANCE_NAMES, "us-east-1", session,args.aws_region)

if __name__ == "__main__":
    main()
