AWS_REGION="$1"
Instance="$2"
max_attempts=9  
attempt_counter=0

outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Run echo command" --parameters commands='sudo /usr/local/bin/supervisorctl restart all> ScriptExecLog.txt & systemctl restart  cassandra.service > ScriptExecLog1.txt' --region $AWS_REGION --output text --query "Command.CommandId")

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
        attempt_counter=$((attempt_counter+1))
        if [ "$attempt_counter" -ge "$max_attempts" ]; then
            echo "Maximum attempts reached. Exiting with failure."
            break
        fi
        sleep 5
    fi
done