'''
This script will do below checks before approving a request
1.	The user who forwarded the approval request mail is the same person who raised the requst in CyberArk or not. Script will not approve if the user is same.
2.	The user who forwarded the approval request is part of PAMapproval group. Script will not approve if user is not part of PAMapproval groups.
3.	If the approval mail contains "Requestor email/Safe name/Request ID" or not. If any of those details not present, script will not approve the request.

Below Scripts are invoked by this script based on checks.
1.	/FULL/PATHS/TO/first_level_approve.py            --> Script for approving first level of approval
2.	/FULL/PATHS/TO/second_level_approve.py           --> Script for approving second level of approval
3.	/FULL/PATHS/TO/get_inco_req.py                   --> Script to check the current status of approval request if either 1st level or 2nd level failed. For example who and when approved the request

Each team who uses CyberArk should have their own PAMapprover AD group. For example, group name for DB team is DB_PAMapprover. Infra team has Infra_PAMapprover etc. The LDAP account which is using here to approve the request should be part of PAMapprover groups.
The linux server in which this script runs should be mapped to domain and able to get user group details from AD. sssd package in linux can be used for this.

'''


from exchangelib import Credentials, Account, Configuration
from exchangelib import Message, Mailbox, DELEGATE
from datetime import datetime
import time
import sys
import os

a = ''
try:
	email_password = ''      #Best practice is not to hardcode the password. use any secret management solutions such as Hashicorp Vault apis to get the password in real time.
	
	## login to exchange mailbox account
	credentials = Credentials('EMAIL_ADDRESS_HERE', email_password)
	config = Configuration(server = 'MAIL_SERVER_NAME_HERE', credentials=credentials)
	a = Account('EMAIL_ADDRESS_HERE', config=config, autodiscover=False, access_type=DELEGATE)
except:
	now = datetime.now()
	dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
	print('Connection ERROR occured at: %s\n%s' %(dt_string, a))
	sys.exit()
	
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
f = open("/FULL/PATH/TO/logs/approval_request.log", "a+")

for item in a.inbox.all():
	f_re = 0
	f_sa = 0
	f_ri = 0
	if "Notification: Password access request" in item.subject and "Automatic reply:" not in item.subject:
		sender = str(item.sender).split("email_address='")[1].split("'")[0]
		bodys = item.text_body
		body = str(bodys).split('\n')
		l = len(body)
		for i in range(0, l):
			if "Requester email:" in body[i]:
				user_id = body[i].split(': ')[1].split('@EMAIL_DOMAIN_NAME')[0].strip()  ## to get userid
				req_mail = user_id + '@EMAIL_DOMAIN_NAME' ## to get email address
				f_re = 1
			if "Safe: " in body[i]:
				Safe = body[i].split(': ')[1].strip()
				f_sa = 1
			if "Request Id: " in body[i]:
				Request_Id = body[i].split(': ')[1].strip()
				f_ri = 1
			if "Account name: " in body[i] or "Object: " in body[i]:
				acc_name = body[i]
			if "Device User Name: " in body[i]:
				dev_uname = body[i].split(': ')[1].strip()
			if "Reason: " in body[i]:
				reason = body[i]
			if "Issued on: " in body[i]:
				issu_on = body[i].split(': ')[1].strip()
			if "Request start date: " in body[i]:
				req_start = body[i].split(': ')[1].strip()
			if "Request end date: " in body[i]:
				req_end = body[i].split(': ')[1].strip()
				
		
		inc_req = ''
		flag = 0
		if f_re == 1 and f_sa == 1 and f_ri == 1:
			req_id = Safe + "_" + str(Request_Id)
			logg = "Approval email was forwarded by %s. The request was rasied at %s by %s to login as %s under safe %s for a period from %s to %s. Below are more details regarding this request. \n%s \n%s" %(sender,issu_on,req_mail,dev_uname,Safe,req_start,req_end,acc_name,reason)
			if req_mail != sender:
				check_usr = os.popen("id %s" %sender).read()  ## to get group of user
				if "2ndLEVEL_pamapprover_GROUPNAME_HERE" in check_usr:  ## check for 2nd level approval AD group.
					appr_lvl = 2
				elif "pamapprov" in check_usr and "2ndLEVEL_pamapprover_GROUPNAME_HERE" not in check_usr:  ## instead of "pamapprov", you can provide all your 1st level approval groups
					appr_lvl = 1
				else:
					f.write("%s: Failed to Approve: Sender is not part of PAMapproval group.\n%s \n" %(dt_string,logg))
					m = Message(account=a, folder=a.sent, subject='Failed to Approve: Sender is not part of PAMapproval group', body='Failed to Approve the request. Escalating to CYBERARK_TEAM_NAME_HERE team. \n Below is the complete mail body \n \n %s' %(item.text_body), to_recipients=[sender], cc_recipients=['EMAIL_ADDRESS_OF_CYBERARK_TEAM'])
					m.send_and_save()
					item.move_to_trash()
					flag = 1
					exit()
				if flag != 1:
					timeout = time.time() + 10
					while True:
						cmd = os.popen("python /FULL/PATH/TO/first_level_approve.py %s %s 2>&1" %(req_id,sender) ).read()
						if "Traceback" not in cmd or "status_code: 401" in cmd or time.time() > timeout:
							break
				else:
					timeout = time.time() + 10
					while True:
						cmd = os.popen("python /FULL/PATH/TO/second_level_approve.py %s %s 2>&1" %(req_id,sender) ).read()
						if "Traceback" not in cmd or "status_code: 401" in cmd or time.time() > timeout:
							break
				if "Confirmed the approval request " in cmd:
					f.write("%s: Successfully confirmed the request %s.\n%s \n%s\n" %(dt_string,req_id,logg,cmd))
					m = Message(account=a, folder=a.sent, subject='Successfully confirmed', body='Successfully processed the approval request.  \n Below is the complete mail body \n \n%s' %(item.text_body), to_recipients=[sender] )
					m.send_and_save()
					item.move_to_trash()
				elif "Failed to confirm approval request with status_code: 500" in cmd:
					inc_req = os.popen("python /FULL/PATH/TO/get_inco_req.py %s 2>&1" %(req_id) ).read()  
					f.write("%s: Failed to Approve the request. The request either already approved or expired %s.\n%s \n%s %s\n" %(dt_string,req_id,logg,inc_req,cmd))
					m = Message(account=a, folder=a.sent, subject='Failed to Approve', body='The request either already approved or expired. Please check CyberArk portal for more details. Escalating to CYBERARK_TEAM_NAME_HERE team.\n \n%s Below is the complete mail body \n \n %s' %(inc_req,item.text_body), to_recipients=[sender], cc_recipients=['EMAIL_ADDRESS_OF_CYBERARK_TEAM'])
					m.send_and_save()
					item.move_to_trash()
				else:
					f.write("%s: Failed to Approve the request %s.\n%s \n%s \n" %(dt_string,req_id,logg,cmd))
					m = Message(account=a, folder=a.sent, subject='Failed to Approve', body='Failed to Approve the request, Please check CyberArk portal for more details. Escalating to CYBERARK_TEAM_NAME_HERE team. \n Below is the complete mail body \n \n %s' %(item.text_body), to_recipients=[sender], cc_recipients=['EMAIL_ADDRESS_OF_CYBERARK_TEAM'])
					m.send_and_save()
					item.move_to_trash()
			else:
				req_id = Safe + "_" + str(Request_Id)
				data = "Sender email id (%s) is same as that of Requestor email id (%s). Hence not approving the request: %s" %(sender,req_mail,req_id)
				f.write("%s: Failed to approve the request %s.\n%s \n%s \n\n" %(dt_string,req_id,data,logg))
				m = Message(account=a, folder=a.sent, subject='Failed to Approve', body='Failed to Approve the request. Escalating to CYBERARK_TEAM_NAME_HERE team.\n \n%s Below is the complete mail body \n \n %s' %(data,item.text_body), to_recipients=[sender], cc_recipients=['EMAIL_ADDRESS_OF_CYBERARK_TEAM'])
				m.send_and_save()
				item.move_to_trash()
		else:
			f.write("%s: Failed to Approve the request. Request mail missing details(Requester email/Safe name/Request ID).\n\n" %(dt_string))
			m = Message(account=a, folder=a.sent, subject='Failed to Approve', body='Request mail missing details. Please make sure to forward request mail without deleting the contents. Failed to approve the request, Escalating to CYBERARK_TEAM_NAME_HERE team.\n Below is the complete mail body \n \n %s' %(item.text_body), to_recipients=[sender], cc_recipients=['EMAIL_ADDRESS_OF_CYBERARK_TEAM'])
				m.send_and_save()
				item.move_to_trash()
		else:
			item.move_to_trash()
			
f.close()