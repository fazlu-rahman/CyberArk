#!/bin/bash

##This script will call "check_approval_request.py" to check the mailbox every 15 seconds for new approval mails for approving requests. This script is added as a cronjob to check and run if its not running. Below is the crontab entry

##* * * * * ps -elf | grep check_approval_request.sh | grep -v "grep" ; [ $? -ne 0 ] && nohup /FULL/PATH/TO/check_approval_request.sh &

while :
do
/usr/local/bin/python3.7 /FULL/PATH/TO/check_approval_request.py
sleep 15
done