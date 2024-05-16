#!/bin/bash

# Helper function to check command status
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

# Function to execute the SSM command to restart services
function execute_aws_ssm_command {
    local AWS_REGION="$1"
    local Instance="$2"

    local outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Run echo command" --parameters commands='sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt & systemctl restart cassandra.service > ScriptExecLog1.txt' --region "$AWS_REGION" --output text --query "Command.CommandId")

    # Call the helper function to check command status
    check_command_status "$AWS_REGION" "$outputSendCommand"
}

# Add more functions here as needed, each with its own parameters and logic

# Example function with different parameters
function another_aws_ssm_command {
    local AWS_REGION="$1"
    local Instance="$2"
    local DocumentName="$3"

    local outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "$DocumentName" --comment "Run custom command" --parameters commands='ls' --region "$AWS_REGION" --output text --query "Command.CommandId")

    # Call the helper function to check command status
    check_command_status "$AWS_REGION" "$outputSendCommand"
}

function_name="$1"
AWS_REGION="$2"
Instance="$3"
DocumentName="AWS-RunShellScript"
# Call the specified function
$function_name "$AWS_REGION" "$Instance"