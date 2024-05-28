import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def restart_ecs_service(cluster_name, service_name, region='us-east-1'):
    try:
        # Initialize a session using Amazon ECS
        ecs_client = boto3.client('ecs', region_name=region)
        print(ecs_client)

        # Describe the service to get the current desired count
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        print(response)
        if len(response['services']) == 0:
            print(f"No service found with name {service_name}")
            return

        service = response['services'][0]
        desired_count = service['desiredCount']

        # Update the service with the same desired count to trigger a restart
        ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=desired_count,
            forceNewDeployment=True
        )

        print(f"Service {service_name} in cluster {cluster_name} is being restarted")

    except NoCredentialsError:
        print("AWS credentials not found.")
    except PartialCredentialsError:
        print("Incomplete AWS credentials found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Replace with your cluster name, service name, and role ARN
    cluster_name = 'cert-etl-c1-app-EcsCluster-EVx5ZL8P2n38'
    service_name = 'cert-etl-c1-app-Service-RIT03rnaZI1x'
    role_arn = 'arn:aws:ecs:us-east-1:549050352176:role/cert-etl-c1-app-EcsCluster-EVx5ZL8P2n38'

    restart_ecs_service(cluster_name, service_name)