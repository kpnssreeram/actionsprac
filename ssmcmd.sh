max_retries=1
retries=0

while [ $retries -le $max_retries ]; do
    outputSendCommand=$(aws ssm send-command \
        --instance-ids $Instance \
        --document-name "AWS-RunShellScript" \
        --comment "Restart services" \
        --parameters commands='sudo /usr/local/bin/supervisorctl restart all > ScriptExecLog.txt && sudo systemctl restart cassandra.service > ScriptExecLog1.txt' \
        --region $AWS_REGION\
        --output text \
        --max-concurrency "5" \
        --max-errors "2" \
        --query "Command.CommandId" 2>/dev/null)

    if [ -n "$outputSendCommand" ]; then
        executedOutput=$(aws ssm list-command-invocations --region $AWS_REGION --command-id "$outputSendCommand" --no-cli-pager --details --output text --query "CommandInvocations[].CommandPlugins[].{Output:Output}")

        while true; do
            STATUS=$(aws ssm list-command-invocations \
                --region "$AWS_REGION" \
                --command-id "$outputSendCommand" \
                --query 'CommandInvocations[0].Status' \
                --output text)

            if [ "$STATUS" == "Success" ]; then
                echo "Command execution successful"
                break 2
            elif [ "$STATUS" == "Failed" ]; then
                echo "Command execution failed"
                break 2
            else
                echo "Command status: $STATUS"
                sleep 5
            fi
        done
    else
        retries=$((retries + 1))
        echo "Provided region_name $AWS_REGION doesn't match a supported format."
    fi
done

if [ $retries -gt $max_retries ]; then
    echo "Maximum number of retries reached. Exiting."
fi