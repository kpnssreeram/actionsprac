#!/bin/bash

# Parameters
AWS_REGION="$1"
INSTANCE_ID="$2"

# Retrieve the public IP address of the instance
INSTANCE_IP=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

# Check if the instance IP is retrieved successfully
if [ -z "$INSTANCE_IP" ]; then
    echo "Failed to retrieve instance IP"
    exit 1
fi

# Execute the command on the instance using SSH
ssh -o StrictHostKeyChecking=no "$INSTANCE_IP" "sudo /usr/local/bin/supervisorctl restart all"

# Check the exit status of the SSH command
if [ $? -eq 0 ]; then
    echo "Command execution successful"
else
    echo "Command execution failed"
fi
