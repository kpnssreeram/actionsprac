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
    REGION="$1"
    CLUSTER_NAME_PREFIX="anon-megabus-app-EcsCluster"

    SERVICE_ARNS=$(aws ecs list-clusters --region "$REGION" --query "clusterArns[?contains(@, '$CLUSTER_NAME_PREFIX')]" --output text | xargs -I{} aws ecs list-services --region "$REGION" --cluster {} --query 'serviceArns[*]' --output text)
    echo "$SERVICE_ARNS"
    for SERVICE_ARN in $SERVICE_ARNS; do
        CLUSTER_NAME=$(echo "$SERVICE_ARN" | awk -F/ '{print $4}')
        SERVICE_NAME=$(echo "$SERVICE_ARN" | awk -F/ '{print $2}')
        TASK_DEFINITION_ARN=$(aws ecs describe-services --region "$REGION" --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].taskDefinition' --output text)

        aws ecs update-service --region "$REGION" --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" --force-new-deployment --task-definition "$TASK_DEFINITION_ARN"
        
        if [ $? -eq 0 ]; then
            echo "Service $SERVICE_NAME updated with a new force deployment."
        else
            echo "Failed to update service $SERVICE_NAME."
        fi
    done
}

function_name="$1"
AWS_REGION="$2"
Instance="$3"
cluster_name="$4"
env="$5"
# Call the respective function
if [ "$function_name" == "restartAllServices" ]; then
    restartAllServices "$AWS_REGION" "$Instance"
elif [ "$function_name" == "updateEcsService" ]; then
    updateEcsService "$AWS_REGION"  
else
    echo "Invalid function name provided."
fi