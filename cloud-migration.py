####################################
#                                  #
#   Author : Arpit Gothi           #
#                                  #
####################################

import argparse
from datetime import date
import http
import json
import os
import sys
from unicodedata import name
import warnings
from getpass import getpass, getuser
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from jira.client import JIRA
from shared.pre_req import co2_login, get_co2_instnaces, is_stack_valid
from shared.operations import batch_connectivity_check, check_disk_space, cm_specfic_backup, app_specific_backup, user_specific_backup, pre_scp_operation, scp_operation_backup, query_yes_no, scp_operation_restore, post_scp_operation, app_specific_restore, user_specific_restore

warnings.filterwarnings(action="ignore", category=ResourceWarning)
warnings.filterwarnings(action='ignore', message='Unverified HTTPS request')

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--stack',
                    help='Stack name',
                    required=True)

parser.add_argument('-j', '--jira',
                    help='Jira ticket (Example: TO-16301)',
                    required=True)
parser.add_argument("--skip_connection_check", help='skip the batch connectivity check', action='store_false', default=True)

AD_USER = getuser()
SHELL_PATH = os.environ['PATH']
HOME_PATH = os.environ['HOME']


try:
    #check_vault_login(VAULT_ADDR,OKTA_PASSWORD)
    co2_login()
except Exception as e:
    print(e)
    quit()
    
print("Your username is " + AD_USER)


JIRA_SERVER = "https://splunk.atlassian.net"
args = parser.parse_args()

# Arguments
STACK = args.stack
skip_connection_check = args.skip_connection_check

# Strings
JIRA_ID = "ARPIT"

# Dictionaries
co2_instances = {}
source_instance_dict = {}
dest_instance_dict = {}


if args.jira is not None:
    JIRA_ID = args.jira

# read JIRA_TOKEN from ~/.jira/token file
JIRA_TOKEN = ""
try:
    with open('/Users/' + AD_USER + '/.jira/token', "r") as jira_token_read:
        JIRA_TOKEN = jira_token_read.read().strip()
except FileNotFoundError as fe:
    JIRA_TOKEN = getpass(prompt='Enter your JIRA_TOKEN: ', stream=None)
    if ".jira" not in os.listdir('/Users/' + AD_USER):
        os.mkdir('/Users/' + AD_USER + '/.jira/')
    with open('/Users/' + AD_USER + '/.jira/token', "w") as jira_token_write:
        jira_token_write.write(JIRA_TOKEN)

EMAIL_ID = (AD_USER + '@splunk.com')



input_statement = (f"Options:\n1. Take backup on {STACK} \n2. Retrive Backup of {STACK} to local machine\n3. Copy Backup of {STACK} to destination stack\n4. Restore backup of {STACK} to Destination Stack\n5. Verify Checksum\n6. EXIT")
choice = input(input_statement)
try:
    while int(choice) not in [1,2,3,4,5,6]:
        print("Please choose valid options ....\n")
        choice = input(input_statement)
except ValueError as ve:
     print("Please enter valid integer number")
     exit()



def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except http.client.IncompleteRead as e:
            return e.partial

    return inner

http.client.HTTPResponse.read = patch_http_response_read(
    http.client.HTTPResponse.read)

def instance_management(stack):
    
    urls=[]
    results = {}
    instance_dict = {}
    results = get_co2_instnaces(stack)#co2_instances
    print(type(results))
    if 'inputs_data_managers' in results:
        for idm in results["inputs_data_managers"]:
            for ids in idm["urls"]:
                idm_name = idm["name"]
                ids = ids.split('.')[0]
                instance_dict[idm_name]=ids

    if 'cluster_master' in results:
        # for cm in results["cluster_master"]:
            for cms in range(1):
                cm_name =results["cluster_master"]["name"]
                cm_fqdn=results["cluster_master"]["urls"][-1]
                cm_fqdn = cm_fqdn.split('.')[0]
                instance_dict[cm_name]= cm_fqdn

    if 'search_heads' in results:
        for sh in results["search_heads"]:
            for ids in sh["urls"]:
                if(sh["name"] == 'shc1'):
                    pass
                else:
                    sh_name = sh["name"]
                    ids = ids.split('.')[0]
                    instance_dict[sh_name]=ids

    if 'search_head_clusters' in results:
        for sh in results["search_head_clusters"]:
            for shcs in sh["instances"]:
                for ids in shcs["urls"]:
                    ids = ids.split('.')[0]
                    urls.append(ids)
                    shc_name = sh["name"]
                    instance_dict[shc_name]=urls
                    
    #if 'indexers' in results:
    #    for idx in results["indexers"]:
    #        for ids in idx["urls"]:
    #            idxs = 'indexer'
    #            source_instance_dict[idxs]=ids


    # if 'indexers' in results:
    #     for idx in results["indexers"]:
    #         for ids in idx["urls"]:
    #             print(ids)
    
    return instance_dict

def main():
    global JIRA_ID
    global choice
    try:
        #co2_instances = get_co2_instnaces()
        source_instance_dict = instance_management(STACK)
        print(source_instance_dict)
        print(source_instance_dict.keys())
        
        os.makedirs(os.path.expanduser(f"~/{JIRA_ID}/"), exist_ok=True)
        with open(os.path.expanduser(f"~/{JIRA_ID}/source_instance_details.json"), 'w') as fp:
            json.dump(source_instance_dict, fp)
            
        print(skip_connection_check)
        if skip_connection_check:
            for instnace_label, instance in source_instance_dict.items():
                if isinstance(instance, list):
                    for instance in source_instance_dict[instnace_label]:
                        batch_connectivity_check(instance)
                else:
                    batch_connectivity_check(instance)
        
        
        JIRA_CMT_STR = "h2. Took backup:\n"


        while(choice!='6'):
            if choice == '1':
                for instnace_label in source_instance_dict.keys():
                    if instnace_label.startswith('shc'):
                        for instance in source_instance_dict[instnace_label]:
                            JIRA_CMT_STR = app_specific_backup(JIRA_CMT_STR,instance,JIRA_ID,instnace_label)
                            JIRA_CMT_STR = user_specific_backup(JIRA_CMT_STR,instance,JIRA_ID,instnace_label)
                            JIRA_CMT_STR = pre_scp_operation(JIRA_CMT_STR,instance,JIRA_ID)

                    elif instnace_label.startswith('c0m1'):
                        #JIRA_CMT_STR = cm_specfic_backup(JIRA_CMT_STR,source_instance_dict[instnace_label],JIRA_ID,instnace_label)
                        JIRA_CMT_STR = user_specific_backup(JIRA_CMT_STR,source_instance_dict[instnace_label],JIRA_ID,instnace_label)
                        JIRA_CMT_STR = pre_scp_operation(JIRA_CMT_STR,source_instance_dict[instnace_label],JIRA_ID)
                
                    else:
                        JIRA_CMT_STR = app_specific_backup(JIRA_CMT_STR,source_instance_dict[instnace_label],JIRA_ID,instnace_label)
                        JIRA_CMT_STR = user_specific_backup(JIRA_CMT_STR,source_instance_dict[instnace_label],JIRA_ID,instnace_label)
                        JIRA_CMT_STR = pre_scp_operation(JIRA_CMT_STR,source_instance_dict[instnace_label],JIRA_ID)
    
                #node_fqdn = str(source_instance_dict[instnace_label]).split('.')[0]
                #if choice == '1':
                #    # Checking Disk Space 
                #    if instnace_label != "indexer":
                #        disk_space=check_disk_space(node_fqdn)
                #        if int(disk_space) > 75:
                #            JIRA_CMT_STR+="*on "+node_fqdn+"*\n"
                #            JIRA_CMT_STR+="*{color:red}Enough Disk space is not available on this node. Please take app-specific backup{color}*\n"
                #            continue

            if choice =='2':
                # Retrive Backup o local instance
                if not os.path.exists(f"~/{JIRA_ID}"):os.makedirs(f"~/{JIRA_ID}")
                for instnace_label, instance in source_instance_dict.items():
                    print(instance)
                    if isinstance(instance, list):
                        for instance in source_instance_dict[instnace_label]:
                            JIRA_CMT_STR = scp_operation_backup(JIRA_CMT_STR,instance,JIRA_ID,instnace_label)
                    else:
                        JIRA_CMT_STR = scp_operation_backup(JIRA_CMT_STR,instance,JIRA_ID,instnace_label)
                        
                    
            if choice =='3':
                # Copy to Destination
                #dest_stack  = "to-115679-test"#input("Please Enter Destination Stack: ")
                dest_stack  = "nmshc1test"#input("Please Enter Destination Stack: ")
                
                if not is_stack_valid(dest_stack):
                    raise Exception("##### Destination Stack is not valid! Please Enter valid Stack ###########")
                dest_instance_dict = instance_management(dest_stack)
                print(dest_instance_dict)
                
                os.makedirs(os.path.expanduser(f"~/{JIRA_ID}/"), exist_ok=True)
                with open(os.path.expanduser(f"~/{JIRA_ID}/destination_instance_details.json"), 'w') as fp:
                    json.dump(dest_instance_dict, fp)
                
                
                print(list(set(dest_instance_dict.keys()).intersection(source_instance_dict.keys())))
                
                source_keys = set(dest_instance_dict.keys())
                dest_keys = set(source_instance_dict.keys())
                
                complement_keys = source_keys.difference(dest_keys)
                missing_keys_from = STACK
                if not complement_keys:
                    missing_keys_from = dest_stack
                    complement_keys = dest_keys.difference(source_keys)
                print(complement_keys, "is missing in", missing_keys_from)
                if len(complement_keys):
                    if not query_yes_no("Do you want to continue??") :
                        raise Exception(f"###### {missing_keys_from} is not having {complement_keys} closing script as per your wish!! ######")
                for instnace_label in source_instance_dict.keys():
                    if instnace_label in dest_instance_dict:
                        if isinstance(dest_instance_dict[instnace_label], list):
                            for index, instance in enumerate(dest_instance_dict[instnace_label]):
                                JIRA_CMT_STR = scp_operation_restore(JIRA_CMT_STR, JIRA_ID, source_instance_dict[instnace_label][index], instance, instnace_label)
                                JIRA_CMT_STR = post_scp_operation(JIRA_CMT_STR, JIRA_ID, instance)
                        else:
                            JIRA_CMT_STR = scp_operation_restore(JIRA_CMT_STR, JIRA_ID, source_instance_dict[instnace_label], dest_instance_dict[instnace_label], instnace_label)
                            JIRA_CMT_STR = post_scp_operation(JIRA_CMT_STR, JIRA_ID, dest_instance_dict[instnace_label])


            if choice =='4':
                # Restore backup to orignal location
                for instnace_label in source_instance_dict.keys():
                    
                    if instnace_label.startswith('shc'):
                        for instance in dest_instance_dict[instnace_label]:
                            JIRA_CMT_STR = app_specific_restore(JIRA_CMT_STR,instance,JIRA_ID,instnace_label)
                            JIRA_CMT_STR = user_specific_restore(JIRA_CMT_STR,instance,JIRA_ID,instnace_label)

                    elif instnace_label.startswith('c0m1'):
                        #JIRA_CMT_STR = cm_specific_backup(JIRA_CMT_STR,dest_instance_dict[instnace_label],JIRA_ID,instnace_label)
                        JIRA_CMT_STR = user_specific_restore(JIRA_CMT_STR,dest_instance_dict[instnace_label],JIRA_ID,instnace_label)

                    else:
                        JIRA_CMT_STR = app_specific_restore(JIRA_CMT_STR,dest_instance_dict[instnace_label],JIRA_ID,instnace_label)
                        JIRA_CMT_STR = user_specific_restore(JIRA_CMT_STR,dest_instance_dict[instnace_label],JIRA_ID,instnace_label)

                

                        
            
            choice = input(input_statement)
            try:    
                while int(choice) not in [1,2,3,4,5,6]:
                    print("Please choose valid options ....")
                    choice = input(input_statement)
            except ValueError as ve:
                print("Make a Jira comment manually for previous run")
                print("Please enter valid integer number")
                print(JIRA_CMT_STR)
                exit()

        print(JIRA_CMT_STR)
        if query_yes_no("\n\nDo you want to add JIRA comment?", "yes"):     
        
            if JIRA_ID == "ARPIT":
                sys.stdout.write(
                    "\nEnter the app install JIRA issue id (CO-123456):")
                JIRA_ID = input()

            options = {'server': JIRA_SERVER}
            jira = JIRA(options=options, basic_auth=(EMAIL_ID, JIRA_TOKEN))
            issue = jira.issue(JIRA_ID)
            remove_lable=['auto_precheck_general','auto_precheck_review','auto_precheck_failed','auto_precheck_complete','auto_precheck_in_progress']
            issue.fields.labels=[issue.fields.labels[i] for i in range(len(issue.fields.labels)) if issue.fields.labels[i] not in remove_lable]
            issue.fields.labels.append(u'auto_precheck_general')
            issue.update(fields={"labels": issue.fields.labels})
            jira.add_comment(issue, JIRA_CMT_STR)
            print("Comment added successfully: " + JIRA_SERVER + "/browse/" + JIRA_ID)           

        print("\n")
        print("v1.0 @copyright Arpit Gothi")
        print("\n")
    except Exception as e:
        print(e)
        quit()


if __name__ == "__main__":
    if is_stack_valid(STACK):
        main()
    else:
        print("Source Stack is Invalid!!")