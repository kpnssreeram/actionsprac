#!/bin/bash

# Parameters
AWS_REGION="$1"
Instance="$2"

# SSM Document Name
DOCUMENT_NAME="AWS-RunShellScript"

# Command to run on the instance
COMMAND="hostname"

# Send the SSM command and capture the output
# COMMAND_ID=$(aws ssm send-command \
#     --region "$AWS_REGION" \
#     --targets "Key=instanceids,Values=$Instance" \
#     --document-name "$DOCUMENT_NAME" \
#     --parameters commands="$COMMAND" \
#     --output text \
#     --query 'Command.CommandId')

# echo "Command sent with ID: $COMMAND_ID"

# # Wait for the command to complete
# while true; do
#     COMMAND_STATUS=$(aws ssm list-command-invocations \
#         --region "$AWS_REGION" \
#         --command-id "$COMMAND_ID" \
#         --details \
#         --query "CommandInvocations[0].Status" \
#         --output text)

#     if [ "$COMMAND_STATUS" == "Success" ]; then
#         break
#     elif [ "$COMMAND_STATUS" == "Failed" ]; then
#         echo "Command failed."
#         exit 1
#     else
#         echo "Command is still running..."
#         sleep 5
#     fi
# done
outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Run echo command" --parameters commands='hostname'  --region $AWS_REGION --output text --query "Command.CommandId")
executedOutput=$(aws ssm list-command-invocations  --region $AWS_REGION  --command-id "$outputSendCommand" --no-cli-pager --details --output text --query "CommandInvocations[].CommandPlugins[].{Output:Output}")
                

# # Get the command output
# COMMAND_OUTPUT=$(aws ssm get-command-invocation \
#     --region "$AWS_REGION" \
#     --command-id "$COMMAND_ID" \
#     --instance-id "$Instance" \
#     --query "CommandInvocation.CommandPlugins[0].Output" \
#     --output text)

echo "Command output: $COMMAND_OUTPUT"