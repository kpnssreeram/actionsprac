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

function runShovelAckScript {
    local AWS_REGION="$1"
    local Instances=(
        "i-0e7bdc0b313e82093"
        "i-0bdde7a38ccdf8dd9"
        "i-064b7b60c22f68885"
        "i-09f67bd435c4c6e4d"
    )
    for Instance in "${Instances[@]}"; do
        local CommandId=$(aws ssm send-command \
            --instance-ids "$Instance" \
            --document-name "AWS-RunShellScript" \
            --comment "Debug and Run Python Script" \
            --parameters 'commands=[
                "ls -la /",
                "cd /shovel || cd ~/shovel || echo \"Failed to find shovel directory\"",
                "nohup python3 shovelack.py > outputShovelAck.log 2>&1 &"
            ]' \
            --region "$AWS_REGION" \
            --query "Command.CommandId" \
            --output text)
        echo "Executing shovel script on $Instance"
        check_command_status "$AWS_REGION" "$CommandId"
    done
}

function runCanaryAckScript {
    local AWS_REGION="$1"
    local Instances=(
        "i-064b7b60c22f68885"
        "i-09f67bd435c4c6e4d"
    )
    for Instance in "${Instances[@]}"; do
        echo "Executing Canary Script on $Instance"
        
        # First, kill all nohup processes
        local KillCommand=$(aws ssm send-command \
            --instance-ids "$Instance" \
            --document-name "AWS-RunShellScript" \
            --comment "Kill all nohup processes" \
            --parameters 'commands=[
                "pkill -f nohup",
                "sleep 2"
            ]' \
            --region "$AWS_REGION" \
            --query "Command.CommandId" \
            --output text)
        
        # Wait for the kill command to complete
        check_command_status "$AWS_REGION" "$KillCommand"
        
        # Now run the new canaryack.py process
        local CommandId=$(aws ssm send-command \
            --instance-ids "$Instance" \
            --document-name "AWS-RunShellScript" \
            --comment "Debug and Run Python Script" \
            --parameters 'commands=[
                "ls -la /",
                "cd /shovel || cd ~/shovel || echo \"Failed to find shovel directory\"",
                "nohup python3 canaryack.py $AWS_REGION > outputcanaryAck.log 2>&1 &"
            ]' \
            --region "$AWS_REGION" \
            --query "Command.CommandId" \
            --output text)
        
        check_command_status "$AWS_REGION" "$CommandId"
    done
}

function updateEcsService {
    REGION="$1"
    ENV="$2"
    CLUSTER="$3"
    cluster_name_prefix="$ENV-etl-$CLUSTER-app-EcsCluster"
    serviceARN=$(aws ecs list-clusters --region "$REGION" --query "clusterArns[?contains(@, '$cluster_name_prefix')]" --output text | xargs -I{} aws ecs list-services --region "$REGION" --cluster {} --query 'serviceArns[*]' --output text)
    
    for arn in $serviceARN; do
        cluster_name=$(echo "$arn" | awk -F '/' '{print $2}')
        service_name=$(echo "$arn" | awk -F '/' '{print $3}')

        aws ecs update-service --cluster "$cluster_name" --region "$REGION" --service "$service_name" --force-new-deployment
        if [ $? -eq 0 ]; then
            echo "Service $service_name update triggered successfully. Waiting for deployment to complete..."
        else
            echo "Failed to trigger update for service $service_name."
            continue
        fi

        while true; do
            deployment_status=$(aws ecs describe-services --cluster "$cluster_name" --region "$REGION" --services "$service_name" --query 'services[0].deployments[?status==`PRIMARY`].rolloutState' --output text)
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
if [ "$function_name" == "restartAllServices" ]; then
    restartAllServices "$AWS_REGION" "$Instance"
elif [ "$function_name" == "updateEcsService" ]; then
    updateEcsService "$AWS_REGION" "$env" "$cluster_id"
elif [ "$function_name" == "runShovelAckScript" ]; then
    runShovelAckScript "$AWS_REGION" 
elif [ "$function_name" == "runCanaryAckScript" ]; then
    runCanaryAckScript "$AWS_REGION" 
else
    echo "Invalid function name provided."
fi