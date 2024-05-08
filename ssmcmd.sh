#!/bin/bash

# Parameters
AWS_REGION="$1"
Instance="$2"

# Restart services using AWS Systems Manager Run Command
# COMMAND_OUTPUT=$(aws ssm send-command \
#     --region "$AWS_REGION" \
#     --instance-ids "$Instance" \
#     --document-name "AWS-RunShellScript" \
#     --parameters '{"commands":["sudo /usr/local/bin/supervisorctl restart all"]}' \
#     --query 'Command.CommandId' \
#     --output text)

# # Check if the command was sent successfully
# if [ -z "$COMMAND_OUTPUT" ]; then
#     echo "Failed to send command"
#     exit 1
# fi

# # Wait for the command to complete and get the status
# while true; do
#     STATUS=$(aws ssm list-command-invocations \
#         --region "$AWS_REGION" \
#         --command-id "$COMMAND_OUTPUT" \
#         --query 'CommandInvocations[0].Status' \
#         --output text)

#     if [ "$STATUS" == "Success" ]; then
#         echo "Command execution successful"
#         break
#     elif [ "$STATUS" == "Failed" ]; then
#         echo "Command execution failed"
#         break
#     else
#         echo "Command status: $STATUS"
#         sleep 5
#     fi
# done

# # Get the command output
# OUTPUT=$(aws ssm get-command-invocation \
#     --region "$AWS_REGION" \
#     --command-id "$COMMAND_OUTPUT" \
#     --instance-id "$Instance" \
#     --query 'CommandInvocation.CommandPlugins[0].Output' \
#     --output text)

# echo "Command output:"
# echo "$OUTPUT"
#!/bin/bash

# Parameters
AWS_REGION="$1"
Instance="$2"

# Restart services using AWS Systems Manager Run Command
COMMAND_OUTPUT=$(aws ssm send-command \
    --region "$AWS_REGION" \
    --instance-ids "$Instance" \
    --document-name "AWS-RunShellScript" \
    --parameters '{"commands":["sudo /usr/local/bin/supervisorctl restart all"]}' \
    --query 'Command.CommandId' \
    --output text)

# Check if the command was sent successfully
if [ -z "$COMMAND_OUTPUT" ]; then
    echo "Failed to send command"
    exit 1
fi

# Function to fetch logs
fetch_logs() {
    aws ssm get-command-invocation \
        --region "$AWS_REGION" \
        --command-id "$COMMAND_OUTPUT" \
        --instance-id "$Instance" \
        --query 'CommandInvocation.CommandPlugins[0].Output' \
        --output text
}

# Continuously fetch logs until command completes
while true; do
    OUTPUT=$(fetch_logs)
    if [ "$OUTPUT" == "none" ]; then
        echo "No output from the command"
    else
        echo "$OUTPUT"
    fi

    # Check if command has completed
    STATUS=$(aws ssm list-command-invocations \
        --region "$AWS_REGION" \
        --command-id "$COMMAND_OUTPUT" \
        --query 'CommandInvocations[0].Status' \
        --output text)

    if [ "$STATUS" == "Success" ]; then
        echo "Command execution successful"
        break
    elif [ "$STATUS" == "Failed" ]; then
        echo "Command execution failed"
        break
    else
        echo "Command status: $STATUS"
    fi

    sleep 5
done


# outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Run echo command" --parameters commands='sudo /usr/local/bin/supervisorctl restart all'  --region $AWS_REGION --output text --query "Command.CommandId")
# executedOutput=$(aws ssm list-command-invocations  --region $AWS_REGION  --command-id "$outputSendCommand" --no-cli-pager --details --output text --query "CommandInvocations[].CommandPlugins[].{Output:Output}")
# echo "Command output: $executedOutput"