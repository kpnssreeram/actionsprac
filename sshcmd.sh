#!/bin/bash

# Parameters
INSTANCE_IP="$2"  # Use instance IP or DNS name if direct instance ID is not accessible
AWS_REGION="$1"  # Update with your AWS region if necessary

# Set AWS CLI environment variables if needed
export AWS_DEFAULT_REGION="$AWS_REGION"

# Execute the command on the instance using SSH
ssh "$INSTANCE_IP" "sudo /usr/local/bin/supervisorctl restart all"

# Check the exit status of the SSH command
if [ $? -eq 0 ]; then
    echo "Command execution successful"
else
    echo "Command execution failed"
fi
