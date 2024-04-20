import boto3

# Create an S3 client
s3_client = boto3.client('s3')

# List all buckets
response = s3_client.list_buckets()

# Print bucket names
for bucket in response['Buckets']:
    print(bucket['Name'])