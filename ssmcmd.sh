AWS_REGION="$1"
Instance="$2"

outputSendCommand=$(aws ssm send-command --instance-ids "$Instance" --document-name "AWS-RunShellScript" --comment "Run echo command" --parameters commands='sudo /usr/local/bin/supervisorctl restart all> ScriptExecLog.txt'  --region $AWS_REGION --output text --query "Command.CommandId")
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
        sleep 5
    fi
done