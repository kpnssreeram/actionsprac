#!/bin/bash

function check_command_status {
    local AWS_REGION="$1"
    local outputSendCommand="$2"
    local AWS_PROFILE="$3"
    local max_attempts=9
    local attempt_counter=0
    while true; do
        local STATUS=$(aws ssm list-command-invocations \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" \
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
                echo "Maximum attempts reached. Execution may or may not be successful. Please check logs or run this script again."
                break
            fi
            sleep 9
        fi
    done
}

function restartAllServices {
    local AWS_REGION="$1"
    local Instance="$2"
    local AWS_PROFILE="$3"
    local outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Restart Services" --parameters commands='sudo su - & sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt & systemctl restart cassandra.service > ScriptExecLog1.txt' --region "$AWS_REGION" --profile "$AWS_PROFILE" --output text --query "Command.CommandId")
    check_command_status "$AWS_REGION" "$outputSendCommand" "$AWS_PROFILE"
}

function updateEcsService {
    local REGION="$1"
    local ENV="$2"
    local CLUSTER="$3"
    local AWS_PROFILE="$4"
    local cluster_name_prefix="$ENV-etl-$CLUSTER-app-EcsCluster"
    local serviceARN=$(aws ecs list-clusters --region "$REGION" --profile "$AWS_PROFILE" --query "clusterArns[?contains(@, '$cluster_name_prefix')]" --output text | xargs -I{} aws ecs list-services --region "$REGION" --profile "$AWS_PROFILE" --cluster {} --query 'serviceArns[*]' --output text)
    
    for arn in $serviceARN; do
        local cluster_name=$(echo "$arn" | awk -F '/' '{print $2}')
        local service_name=$(echo "$arn" | awk -F '/' '{print $3}')

        aws ecs update-service --cluster "$cluster_name" --region "$REGION" --profile "$AWS_PROFILE" --service "$service_name" --force-new-deployment
        if [ $? -eq 0 ]; then
            echo "Service $service_name update triggered successfully. Waiting for deployment to complete..."
        else
            echo "Failed to trigger update for service $service_name."
            continue
        fi

        while true; do
            local deployment_status=$(aws ecs describe-services --cluster "$cluster_name" --region "$REGION" --profile "$AWS_PROFILE" --services "$service_name" --query 'services[0].deployments[?status==`PRIMARY`].rolloutState' --output text)
            if [ "$deployment_status" == "COMPLETED" ]; then
                echo "Service $service_name has been updated successfully."
                break
            elif [ "$deployment_status" == "FAILED" ]; then
                echo "Service $service_name update failed."
                break
            else
                echo "Waiting for service $service_name update to complete..."
                sleep 30 
            fi
        done
    done  
}

function_name="$1"
AWS_REGION="$2"
Instance="$3"
cluster_id="$4"
env="$5"
AWS_PROFILE="emodb-nexus-qa"

if [ "$function_name" == "restartAllServices" ]; then
    restartAllServices "$AWS_REGION" "$Instance" "$AWS_PROFILE"
elif [ "$function_name" == "updateEcsService" ]; then
    updateEcsService "$AWS_REGION" "$env" "$cluster_id" "$AWS_PROFILE"
else
    echo "Invalid function name provided."
fi
