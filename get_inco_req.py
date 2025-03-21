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

url = "https://PVWA_LB_HERE/PasswordVault/API/auth/LDAP/Logon"

headers = { 'Content-Type': 'application/json', 'Connection': 'keep-alive', 'Cache-Control': 'max-age=300'}
data = '{ "username":"'+username+'","password":"'+approve2_password+'", "useRadiusAuthentication":"false", "connectionNumber":"1"}'

response = requests.request("POST",url, headers=headers, data=data, verify=False)

login_response = response.status_code
output_response = response.json()
auth_token = output_response

if login_response == 200:
	#print("Logon completed successfully with status_code: {}".format(login_response))
	pass
else:
	#print("Logon failed with status_code: {}".format(login_response))
	sys.exit()
	
url_inco_req = "https://PVWA_LB_HERE/PasswordVault/API/IncomingRequests/%s" %req_id

headers = { 'Content-Type': 'application/json', 'Connection': 'keep-alive', 'Authorization':auth_token}
response = requests.request("GET",URL_inco_req, headers=headers, verify=False)

statusCode=response.status_code

if statusCode == 200:
	try:
		output_response = response.json()
		for j in output_response["Confirmers"]:
			if j["ActionDate"] != 0:
				usr_nme = [ a['UserName'] for a in j["Members"] ]
				epo_time = j["ActionDate"]
				ht_time = time.ctime(int(epo_time))
				print("%s. Approved_Reason: '%s', Approved_Time: '%s', %s. " %(j["Name"],j["Reason"],ht_time,usr_nme))
	except:
		pass
else:
	#print("Failed to pull request with status_code: {}".format(statusCode))
	pass

url = "https://PVWA_LB_HERE/PasswordVault/WebServices/auth/Shared/RestfulAuthenticationService.svc/Logoff"
headers = { 'Content-Type': 'application/json', 'Authorization':auth_token}
try:
	response = requests.request("POST",url, headers=headers, verify=False)
	logoff_response=response.status_code
	
	if logoff_response == 200:
		#print("Logoff completed successfully with status_code: {}".format(logoff_response))
		pass
	else:
		#print("Logoff failed with status_code: {}".format(logoff_response))
		pass
except:
	pass