#!/bin/bash

# Parameters
AWS_REGION="$1"
Instance="$2"

# Restart services using AWS Systems Manager Run Command
outputSendCommand=$(aws ssm send-command \
    --instance-ids "$Instance" \
    --document-name "AWS-RunShellScript" \
    --comment "Restart services" \
    --parameters commands='sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt && sudo systemctl restart cassandra.service > ScriptExecLog1.txt' \
    --region "$AWS_REGION" \
    --output text \
    --max-concurrency "5" \
    --max-errors "2" \
    --query "Command.CommandId")

# Wait for the command to complete and get the status
retries=0
max_retries=2
while true; do
    STATUS=$(aws ssm list-command-invocations \
        --region "$AWS_REGION" \
        --command-id "$outputSendCommand" \
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
        retries=$((retries + 1))
        if [ "$retries" -ge "$max_retries" ]; then
            echo "Maximum retries ($max_retries) reached. Exiting."
            break
        fi
        sleep 5
    fi
done
