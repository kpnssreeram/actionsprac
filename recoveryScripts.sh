#!/bin/bash

function check_command_status {
    local AWS_REGION="$1"
    local outputSendCommand="$2"
    local max_attempts=9
    local attempt_counter=0

    while true; do
        local STATUS=$(aws ssm list-command-invocations \
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
            attempt_counter=$((attempt_counter+1))
            if [ "$attempt_counter" -ge "$max_attempts" ]; then
                echo "Maximum attempts reached. Exiting with failure."
                break
            fi
            sleep 9
        fi
    done
}

function restartAllServices {
    local AWS_REGION="$1"
    local Instance="$2"
    local outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Restart Services" --parameters commands='sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt & systemctl restart cassandra.service > ScriptExecLog1.txt' --region "$AWS_REGION" --output text --query "Command.CommandId")
    check_command_status "$AWS_REGION" "$outputSendCommand"
}

function updateEcsService {
    local AWS_REGION="$1"
    local Instance="$2"
    local DocumentName="$3"
    local outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "$DocumentName" --comment "Update Ecs Service" --parameters commands='ls' --region "$AWS_REGION" --output text --query "Command.CommandId")
    check_command_status "$AWS_REGION" "$outputSendCommand"
}

function_name="$1"
AWS_REGION="$2"
Instance="$3"

# Call the respective function
if [ "$function_name" == "restartAllServices" ]; then
    restartAllServices "$AWS_REGION" "$Instance"
elif [ "$function_name" == "another_aws_ssm_command" ]; then
    another_aws_ssm_command "$AWS_REGION" "$Instance" "AWS-RunShellScript"
else
    echo "Invalid function name provided."
fi