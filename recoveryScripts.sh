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
                echo "Maximum attempts reached. execution may or may not be successful.Please check logs or run this script again."
                break
            fi
            sleep 9
        fi
    done
}

function restartAllServices {
    local AWS_REGION="$1"
    local Instance="$2"
    local outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Restart Services" --parameters commands='sudo su - & sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt & systemctl restart cassandra.service > ScriptExecLog1.txt' --region "$AWS_REGION" --output text --query "Command.CommandId")
    check_command_status "$AWS_REGION" "$outputSendCommand"
}

function updateEcsService {
    REGION="$1"
    cluster_name_prefix="anon-megabus-app-EcsCluster"
    serviceARN=$(aws ecs list-clusters --region "$REGION" --query "clusterArns[?contains(@, '$cluster_name_prefix')]" --output text | xargs -I{} aws ecs list-services --region "$REGION" --cluster {} --query 'serviceArns[*]' --output text)
    for arn in $serviceARN; do
        cluster_name=$(echo "$arn" | awk -F '/' '{print $2}')
        service_name=$(echo "$arn" | awk -F '/' '{print $3}')
        aws ecs update-service --cluster "$cluster_name" --region "$REGION" --service "$service_name" --force-new-deployment
        if [ $? -eq 0 ]; then
            echo "Service $service_name updated with a new force deployment."
        else
            echo "Failed to update service $service_name"
        fi
     done  
}

function_name="$1"
AWS_REGION="$2"
Instance="$3"
cluster_id="$4"
env="$5"
if [ "$function_name" == "restartAllServices" ]; then
    restartAllServices "$AWS_REGION" "$Instance"
elif [ "$function_name" == "updateEcsService" ]; then
    updateEcsService "$AWS_REGION"  
else
    echo "Invalid function name provided."
fi