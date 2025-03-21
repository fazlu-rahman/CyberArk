import requests
import time
import base64
import urllib3
import sys
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

username = "ACCOUNT_NAME_FOR_APPROVING_2nd_LEVEL_HERE"
approve2_password = ''  #Best practice is not to hardcode the password. use any secret management solutions such as Hashicorp Vault apis to get the password in real time.
req_id = sys.argv[1]
sender = sys.argv[2]

url = "https://PVWA_LB_HERE/PasswordVault/API/auth/LDAP/Logon"

headers = { 'Content-Type': 'application/json', 'Connection': 'keep-alive', 'Cache-Control': 'max-age=300'}
data = '{ "username":"'+username+'","password":"'+approve2_password+'", "useRadiusAuthentication":"false", "connectionNumber":"1"}'

response = requests.request("POST",url, headers=headers, data=data, verify=False)

login_response = response.status_code
output_response = response.json()
auth_token = output_response

if login_response == 200:
	print("Logon completed successfully with status_code: {}".format(login_response))
else:
	print("Logon failed with status_code: {}".format(login_response))
	
url_conf_req = "https://PVWA_LB_HERE/PasswordVault/API/IncomingRequests/%s/Confirm" %req_id
conf_data = ' { "Reason":"Valid Request. Approving on behalf of %s" }' %sender

headers = { 'Content-Type': 'application/json', 'Connection': 'keep-alive', 'Authorization':auth_token}
response = requests.request("POST",URL_conf_req, headers=headers, data=conf_data, verify=False)

statusCode=response.status_code

if statusCode == 200:
	print("Confirmed the approval request successfully with status_code: {}".format(statusCode))
else:
	print("Failed to confirm approval request with status_code: {}".format(statusCode))

url = "https://PVWA_LB_HERE/PasswordVault/WebServices/auth/Shared/RestfulAuthenticationService.svc/Logoff"
headers = { 'Content-Type': 'application/json', 'Authorization':auth_token}
try:
	response = requests.request("POST",url, headers=headers, verify=False)
	logoff_response=response.status_code
	
	if logoff_response == 200:
		print("Logoff completed successfully with status_code: {}".format(logoff_response))
	else:
		print("Logoff failed with status_code: {}".format(logoff_response))
except:
	pass