import os
import json
from pathlib import Path
import subprocess
import time
import jwt
from getpass import getuser, getpass
from urllib.parse import parse_qs, urlparse
import requests
import uuid

CO2_ENV = "prod"
AD_USER = getuser()
VAULT_ADDR = "https://vault.splunkcloud.systems"
VAULT_PATH = "/v1/cloud-sec-lve-ephemeral/creds/"
POST_DOMAIN = ".splunkcloud.com"
CO2_ENV = ""
VAULT_TOKEN = ""
ADMIN_VAULT_PASS = ""

AD_PASSWORD = getpass(prompt='Enter your AD_PASSWORD: ', stream=None)
OKTA_PASSWORD = getpass(prompt='OKTA_PASSWORD (If it is the same as AD_PASSWORD, just press Enter): ', stream=None)

if OKTA_PASSWORD == '':
    OKTA_PASSWORD = AD_PASSWORD
       
SHELL_PATH = os.environ['PATH']
HOME_PATH = os.environ['HOME']


if POST_DOMAIN == ".splunkcloud.com":
    CO2_ENV = "prod"
    CO2APIENDPOINT = "https://api.co2.lve.splunkcloud.systems"
    
try:
    setEnv = str(os.popen('cloudctl config use ' +
                    CO2_ENV + ' 2>&1').read())
except Exception as e:
    print(e)
    
print("CO2 Configuration:\n" + setEnv + "##########")

def get_token():
  f = open(str(Path.home())+"/.cloudctl/token_"+ CO2_ENV, "r")
  return f.read()

def co2_check_token():
    token_file = HOME_PATH + '/.cloudctl/token_' + CO2_ENV
    try:
        if os.path.exists(token_file):
            if os.path.getsize(token_file) > 0:
                with open(token_file, 'r') as content_file:
                    token = content_file.read()
                decodedToken = jwt.decode(
                    token, options={"verify_signature": False})
                jsonToken = json.dumps(decodedToken)
                tokenExpireTime = json.loads(jsonToken)["exp"]
                currentTime = int(time.strftime("%s"))
                difference = tokenExpireTime - currentTime
                if difference > 60:
                    return True

    except Exception as e:
        print(e)

    return False

def co2_login():
    while co2_check_token() is not True:
        token_file = HOME_PATH + '/.cloudctl/token_' + CO2_ENV 
        print("SplunkCloud: Logging into CO2")

        try:
            header = {'Accept': 'application/json',
                      'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
            login_url = "https://splunkcloud.okta.com/api/v1/authn"
            login_payload = {'username': AD_USER, 'password': AD_PASSWORD}

            login_response = requests.post(
                login_url, headers=header, json=login_payload)

            if login_response.status_code != 200:
                raise Exception()

            login_response_json = json.loads(login_response.text)
            stateToken = str(login_response_json['stateToken'])
            push_verification_link = str(
                login_response_json['_embedded']['factors'][0]['_links']['verify']['href'])

            push_url = push_verification_link
            push_payload = {'stateToken': stateToken}
            push_response_json = ''

            while True:
                push_response = requests.post(
                    push_url, headers=header, json=push_payload)

                if push_response.status_code != 200:
                    raise Exception()

                push_response_json = json.loads(push_response.text)
                auth_status = str(push_response_json['status'])

                if auth_status == "SUCCESS":
                    break

                time.sleep(0.5)

            session_token = str(push_response_json['sessionToken'])

            with open(HOME_PATH + "/.cloudctl/config.yaml", 'r') as cloudctl_config:
                configs = cloudctl_config.readlines()

            for config in configs:

                if "idpclientid" in config:
                    client_id = config.split(": ")[1].rstrip('\n')

                if "idpserverid" in config:
                    server_id = config.split(": ")[1].rstrip('\n')

            access_token_url = "https://splunkcloud.okta.com/oauth2/" + server_id + "/v1/authorize?client_id=" + client_id + "&nonce=" + str(uuid.uuid4()) + \
                "&prompt=none&redirect_uri=https%3A%2F%2Fdoes.not.resolve%2F&response_type=token&scope=&sessionToken=" + \
                session_token + "&state=not.used"
            access_token_response = requests.get(
                access_token_url, allow_redirects=False)

            if access_token_response.status_code != 302:
                raise Exception()

            parsed_access_token_header = urlparse(
                access_token_response.headers['location'])
            access_token = parse_qs(parsed_access_token_header.fragment)[
                'access_token'][0]

            with open(token_file, 'w') as token_f:
                token_f.write(access_token)

        except Exception as e:
            print("\nSplunkCloud: Failed to log into CO2\n" + e)

def get_co2_instnaces(stack_name):
    try:
        res = requests.get(CO2APIENDPOINT+"/v3/stacks/"+stack_name+"/instances", headers={"authorization": "Bearer "+get_token().strip()})	
        return res.json()	
    except Exception as e:
        print(e)
        quit()

def get_vault_token(VAULT_ADDR,OKTA_PASSWORD):
    """
    Function to get the vault API token
    """
    # will store token as global variable to reuse for all calls to vault
    global VAULT_TOKEN
    # URL to hit the vault auth okta endpoint
    url = VAULT_ADDR + '/v1/auth/okta/login/' + AD_USER
    payload = '{"password": "' + OKTA_PASSWORD + '"}'

    try:
        print("Vault: Sending 2FA prompt to your phone now...")
        vault_token_json = requests.post(url, data=payload)
        print("Vault: Verification received. Checking Status")

        if vault_token_json.status_code != 200:
            raise Exception(
                'Failed to get Vault Token. Check for your password and try again.')

    except Exception as e:
        print(e)
        print(' ...Exiting... ')
        quit()

    vault_token_json = json.loads(vault_token_json.text)
    VAULT_TOKEN = str(vault_token_json['auth']['client_token'])
    with open("/Users/" + AD_USER + "/.vault-token", "w") as fvault:
        fvault.write(VAULT_TOKEN)

    print("Vault: Authenticated!\n##########")
    
def check_vault_login(VAULT_ADDR,OKTA_PASSWORD):
    now = time.time()
    current = Path.home()
    token_path = current.joinpath(".vault-token")
    print(token_path)
    try:
        mod_time = os.stat(token_path).st_mtime
        file_size = os.stat(token_path).st_size
    except Exception as e:
        print("unable to get token time and size.", e)
        mod_time = 0
        file_size = 0
    file_age = now - mod_time
    if file_size != 0 and file_age < 28800:
        global VAULT_TOKEN
        f = open(str(token_path), "r")
        VAULT_TOKEN = f.read()
        f.close()
        print("Vault: Already Authenticated!\n##########")
    else:
        try:
            print("Vault login")
            get_vault_token(VAULT_ADDR,OKTA_PASSWORD)
        except Exception as e:
            raise RuntimeError(f'Unable to logged in into "Vault" ({e})')
        
        
def is_stack_valid(stack):
    try:
        cloudctl_response = subprocess.run(["cloudctl", "stacks", "get", stack, "-o", "json"], stdout=subprocess.PIPE)
        if cloudctl_response.returncode == 0:
            response_json = json.loads(cloudctl_response.stdout.decode("utf-8"))
            if response_json.get("code") == 404 and response_json.get("message") == "no stack found with that name/version: not found":
                return False
            else:
                return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred while checking for the splunk stack: {e}")
        return False
