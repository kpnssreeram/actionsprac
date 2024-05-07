#!/bin/bash

# Parameters
AWS_REGION="$1"
Instance="$2"

# SSM Document Name
DOCUMENT_NAME="AWS-RunShellScript"

# Command to run on the instance
COMMAND="hostname"

# Send the SSM command
output=$(aws ssm send-command \
    --region "$AWS_REGION" \
    --targets "Key=instanceids,Values=$Instance" \
    --document-name "$DOCUMENT_NAME" \
    --parameters commands="$COMMAND" \
    --output text \
    --query 'Command.CommandId' 2>&1)

echo "Command output sent with ID: $output"
