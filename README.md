**Introduction**

The CyberArk Dual Control functionality let users raise connection/password access request which will then goes to approval from the approvers mentioned in the safe.

**Existing Scenario**

The approvers will get a notification mail from CyberArk that there is a pending request for their approval. The approvers then need to login to CyberArk manually to approve the request. There is no feature provided by CyberArk to approve the request from mail itself.

**Proposed Solution**

Instead of approving requests by login manually to CyberArk, the approvers need to forward the request mail to a mailbox dedicated to approval automation. This mailbox is continuously monitored by a script which will check for new emails every 15 seconds. Once a mail is forwarded to this mailbox, the script will process email and check for below conditions.

    1. The user who forwarded the approval request mail is the same person who raised the request in CyberArk or not. Script will not approve if the user is same.
    2. The user who forwarded the approval request is part of PAMapprover group. Script will not approve if user is not part of PAMapprover groups.
    3. If the approval mail contains “Requestor email/Safe name/Request ID” or not. If any of those details are not present, the script will not approve the request.

After validating all the above checks, script will then approve the request using the CyberArk Rest APIs. The script will use LDAP account to connect to CyberArk for approving request. Each Team who uses CyberArk should have their own PAMapprover AD group. Let’s assume, the approval group name for DB team is DB_PAMapprover. Infra team has Infra_PAMapprover etc. The LDAP account which is using here to approve the request should be part of the PAMapproval groups. 
Once the request mail is processed, Script will send a success or failure mail notification to the sender who forwarded the request to approval mailbox. Script will fail to approve the request if the request is expired or deleted by the end user, or someone else already approved it. If someone already approved the request before, then the failure notification mail shows the UserlD who approved the request along with the time 

**Workflow**

    • End users raise a connection request from CyberArk.
    • Approvers forward the Pending approval notification mail to approval mailbox once approvers receive it.
    • The script which monitors the approval mailbox will then perform the above-mentioned checks and approve 1st level or 2nd level based on the sender’s PAMapprover group.
    • After processing the request, approvers will get a notification mail saying whether its successful or failed

**Pre-requisites** 

    • A new mailbox created for approval automation.
    • PAMapprover AD groups created for each team for 1st level approvals and one group for 2nd level approvals.
    • Each team’s safe should have their own respective PAMapprover group as 1s level approvals to approve the 1st level of approvals and the common 2nd level approval group to approve the 2nd level approval as Safe Members with list.
    • Two AD accounts were created for approving 1st level approvals and 2nd level approvals. Also, those 2 accounts should be added to the respective PAMapprover groups. 
    • A Linux server which has necessary connectivity firewall rules to communicate with PVWA and mail exchange server.
    • Python3 and necessary libraries (exchangelib, requests) should be installed on the Linux server. Installing Anaconda will get most of the required libraries for this automation. 
    • All the scripts in this bundle should be saved in same path. Under the same path, a directory named “logs” should be created.
    • As per best practices, store password of mailbox account, 1st  level approval account and 2nd level approval accounts password in Hashicorp Vault and retrieve it using API calls. If there is no Hashicorp Vault in your environment, then can hardcode the password in script or use a simple encrypted shell script to echo the password and pass it to the main script as an argument. The “shc” command line tool in Linux can be used to encrypt/convert the shell script to a binary file. 

Below are the scripts in this bundle 

    • check_approval_request.sh -> This script will call “check_approval_request.py” to check the mailbox every 15 seconds for new approval mails for approving requests. This script is added as a cronjob to check and run if it’s not running. 

    • check_approval_request.py -> This script will check for new emails and process the approval by calling “first_level_approve.py” and “second_level approve.py” based on the mail senders group and get inco_req.py” if 1st level or 2nd level failed to get the status of request. Then will send a notification mail to the sender whether it’s approved or failed.

    • first_level_approve.py -> This script for approving 1st level approvals. Uses AD account created for 1st level approval to login using CyberArk APIs. While approving, it will add a comment that the request approved on behalf of the sender’s email address 

    • second_level_approve.py -> This script for approving 2nd level approvals. Uses AD account created for 2nd level approval to login using CyberArk APIs. While approving, it will add a comment that the request approved on behalf of the sender’s email address.

    • get_inco_req.py -> This script for checking the status of request when 1st level, or 2nd level approval fails. This will provide the details like who and when the request is approved. This script uses 2nd level approval AD account to check since 2nd Level AD group is a member of all Safes. 

All the scripts here are generic ones. Need to update the script based on organization. Below are the entities which need to be replaced

    • /FULL/PATH/TO/ -> The full path of script in which it is stored in server.
    • EMAIL ADDRESS_HERE -> Email address of the mailbox created for approval automation.
    • MAIL_SERVER_NAME_HERE -> Exchange mail server name. 
    • EMAIL_DOMAIN_NAME -> Organization email domain address
    • 2ndLEVEL_pamapprover_GROUPNAME_HERE -> AD group name which created for 2nd level approvers. 
    • CYBERARK_TEAM NAME HERE -> Name of team who manages CyberArk in the organization
    • EMAIL_ADDRESS_OF_CYBERARK_TEAM -> email address of team who manages CyberArk in the organization. 
    • PVWA_LB_HERE > CyberArk PVWA load balancer name in the organization 
    • ACCOUNT_NAME_FOR_APPROVING_1st_LEVEL_HERE -> AD account created for approving 1s level approvals 
    • ACCOUNT_NAME_FOR_APPROVING_2nd_LEVEL_HERE -> AD account created for approving 2nd level approvals.

**Implementation**

    • Once all the pre-requisites and above modifications are completed, copy all the scripts to Linux Server under the path specified path.
    • Create a cron job by running the command “crontab -e” and add below line. This will start the script and make sure script will be always running.
    • * * * * * ps -elf | grep  check_approval_request.sh | grep v “grep” ; [$?-ne 0] && nohup /FULL/PATH/TO/check_approval_request.sh &
    • The script will create logs and for auditing purpose, store the logs based on organization requirement. Enable log rotation by running the command as root “vi /etc/logrotate.d/auto_approve” and add below entries after replacing with the correct path of logs. This will rotate logs monthly and will have 6 months data.

/FULL/PATH/TO/logs/approval_request.log {

missing ok

monthly

copytruncate

dateext

rotate 5

compress

}
