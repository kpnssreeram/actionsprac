import boto3
import time
import subprocess
import sys

def check_command_status(aws_region, command_id):
    ssm_client = boto3.client('ssm', region_name=aws_region)
    max_attempts = 9
    attempt_counter = 0
    
    while True:
        response = ssm_client.list_command_invocations(
            CommandId=command_id,
            Details=False
        )
        
        if response['CommandInvocations']:
            status = response['CommandInvocations'][0]['Status']
            
            if status == 'Success':
                print("Command execution successful")
                break
            elif status == 'Failed':
                print("Command execution failed")
                break
            else:
                print(f"Command status: {status}")
                attempt_counter += 1
                if attempt_counter >= max_attempts:
                    print("Maximum attempts reached. Execution may or may not be successful. Please check logs or run this script again.")
                    break
                time.sleep(9)
        else:
            print("No command invocations found")
            break

def restart_all_services(aws_region, instance):
    ssm_client = boto3.client('ssm', region_name=aws_region)
    response = ssm_client.send_command(
        InstanceIds=[instance],
        DocumentName="AWS-RunShellScript",
        Comment="Restart Services",
        Parameters={
            'commands': ['sudo su - && sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt && systemctl restart cassandra.service > ScriptExecLog1.txt']
        }
    )
    command_id = response['Command']['CommandId']
    check_command_status(aws_region, command_id)

def run_shovel_ack_script(aws_region):
    instances = [
        "i-0e7bdc0b313e82093",
        "i-0bdde7a38ccdf8dd9",
        "i-064b7b60c22f68885",
        "i-09f67bd435c4c6e4d"
    ]
    ssm_client = boto3.client('ssm', region_name=aws_region)
    
    for instance in instances:
        response = ssm_client.send_command(
            InstanceIds=[instance],
            DocumentName="AWS-RunShellScript",
            Comment="Debug and Run Python Script",
            Parameters={
                'commands': [
                    "ls -la /",
                    "cd /shovel || cd ~/shovel || echo \"Failed to find shovel directory\"",
                    "nohup python3 shovelack.py > outputShovelAck.log 2>&1 &"
                ]
            }
        )
        command_id = response['Command']['CommandId']
        print(f"Executing shovel script on {instance}")
        check_command_status(aws_region, command_id)

def run_canary_ack_script(aws_region):
    instances = [
        "i-064b7b60c22f68885",
        "i-09f67bd435c4c6e4d"
    ]
    ssm_client = boto3.client('ssm', region_name=aws_region)
    
    for instance in instances:
        response = ssm_client.send_command(
            InstanceIds=[instance],
            DocumentName="AWS-RunShellScript",
            Comment="Debug and Run Python Script",
            Parameters={
                'commands': [
                    "ls -la /",
                    "cd /shovel || cd ~/shovel || echo \"Failed to find shovel directory\"",
                    f"nohup python3 canaryack.py {aws_region} > outputcanaryAck.log 2>&1 &"
                ]
            }
        )
        command_id = response['Command']['CommandId']
        print(f"Executing Canary Script on {instance}")
        check_command_status(aws_region, command_id)

def update_ecs_service(region, env, cluster):
    ecs_client = boto3.client('ecs', region_name=region)
    cluster_name_prefix = f"{env}-etl-{cluster}-app-EcsCluster"
    
    clusters = ecs_client.list_clusters()['clusterArns']
    matching_clusters = [c for c in clusters if cluster_name_prefix in c]
    
    for cluster_arn in matching_clusters:
        services = ecs_client.list_services(cluster=cluster_arn)['serviceArns']
        
        for service_arn in services:
            cluster_name = service_arn.split('/')[1]
            service_name = service_arn.split('/')[2]
            
            try:
                ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_name,
                    forceNewDeployment=True
                )
                print(f"Service {service_name} update triggered successfully. Waiting for deployment to complete...")
            except Exception as e:
                print(f"Failed to trigger update for service {service_name}. Error: {str(e)}")
                continue
            
            while True:
                response = ecs_client.describe_services(
                    cluster=cluster_name,
                    services=[service_name]
                )
                deployment = next((d for d in response['services'][0]['deployments'] if d['status'] == 'PRIMARY'), None)
                
                if deployment:
                    deployment_status = deployment['rolloutState']
                    if deployment_status == 'COMPLETED':
                        print(f"Service {service_name} has been updated successfully.")
                        break
                    elif deployment_status == 'FAILED':
                        print(f"Service {service_name} update failed.")
                        break
                    else:
                        print(f"Waiting for service {service_name} update to complete...")
                        time.sleep(30)
                else:
                    print(f"No PRIMARY deployment found for service {service_name}")
                    break

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <function_name> <aws_region> [<instance>] [<cluster_id>] [<env>]")
        sys.exit(1)

    function_name = sys.argv[1]
    aws_region = sys.argv[2]

    if function_name == "restartAllServices":
        if len(sys.argv) < 4:
            print("Usage: python script.py restartAllServices <aws_region> <instance>")
            sys.exit(1)
        instance = sys.argv[3]
        restart_all_services(aws_region, instance)
    elif function_name == "updateEcsService":
        if len(sys.argv) < 6:
            print("Usage: python script.py updateEcsService <aws_region> <env> <cluster_id>")
            sys.exit(1)
        env = sys.argv[3]
        cluster_id = sys.argv[4]
        update_ecs_service(aws_region, env, cluster_id)
    elif function_name == "runShovelAckScript":
        run_shovel_ack_script(aws_region)
    elif function_name == "runCanaryAckScript":
        run_canary_ack_script(aws_region)
    else:
        print("Invalid function name provided.")