import hashlib
import subprocess
import os
import re
import sys
import time
from getpass import getuser

USER_NAME = getuser()

def query_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(
                "Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def check_disk_space(node_fqdn):
    print("Checking Disk Space ... ")
    cmd =  "sft ssh "+ node_fqdn + " --command 'sudo su  - splunk -c \"df -h | grep \'/opt/splunk\' \"'"
    op= os.popen(cmd).read()
    disk_space=(op.split()[-2]).split("%")[0]

    return disk_space

def batch_connectivity_check(instance):
    print("You may be prompted to accept SSH host keys for each server, please answer yes")
    rc = subprocess.Popen(["sft", "ssh", instance, "--command", 'echo "Connected to `hostname`"']).wait()
    if rc != 0:
        raise ConnectionError(f"SSH connection to {instance} failed!")

def app_specific_backup(JIRA_CMT_STR, node_fqdn, JIRA_ID, label) -> str:
    print("Taking App Specific Backup ... ")
    JIRA_CMT_STR+="*on "+node_fqdn+" ("+label+")*\n"
    op=""
    JIRA_CMT_STR+="{code:java}\n"

    #cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/;cd;cd /opt/splunk/etc/;cp -pR "+location+"/ /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
    cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/; cd;cd /opt/splunk/etc/;find apps \( -name 'local' -or -name 'lookups' \) -type d -print0 | xargs -0 -I {} cp -r --parents {} /opt/splunk/tmp/"+JIRA_ID+"/\"'"
    op= os.popen(cmd).read()
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  cp -pR users/ /opt/splunk/tmp/"+JIRA_ID+"/\n"

    with open('tempf.txt', 'w') as f:
        print(op, file=f)
    with open("tempf.txt","r") as file_one:
        patrn1="No such file or directory"
        for line in file_one:
            if re.search(patrn1, line):
                JIRA_CMT_STR+=f"\n------>    /etc/users/ not found   <------\n\n"             
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"   
    with open("tempf.txt","r") as file_one:
        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_CMT_STR+=line
    
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ date\n"
    JIRA_CMT_STR+=DATE
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ \n"
    JIRA_CMT_STR+="{code}\n"
        
    return JIRA_CMT_STR

def cm_specfic_backup(JIRA_CMT_STR, node_fqdn, JIRA_ID, label) -> str:
    print("Taking App Specific Backup ... ")
    JIRA_CMT_STR+="*on "+node_fqdn+" ("+label+")*\n"
    JIRA_CMT_STR+="{code:java}\n"
    op=""

    cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/; cd;cd /opt/splunk/etc/;cp -pR users/ /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
    op= os.popen(cmd).read()
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  cp -pR users/ /opt/splunk/tmp/"+JIRA_ID+"/\n"

    with open('tempf.txt', 'w') as f:
        print(op, file=f)

    with open("tempf.txt","r") as file_one:
        patrn1="No such file or directory"
        for line in file_one:
            if re.search(patrn1, line):
                JIRA_CMT_STR+=f"\n------>    etc/users not found    <------\n\n"
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"
    with open("tempf.txt","r") as file_one:
        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_CMT_STR+=line
                    
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ date\n"
    JIRA_CMT_STR+=DATE
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ \n"
    JIRA_CMT_STR+="{code}\n"

    return JIRA_CMT_STR

def user_specific_backup(JIRA_CMT_STR, node_fqdn, JIRA_ID, label) -> str:
    print("Taking users Backup ... ")
    JIRA_CMT_STR+="*on "+node_fqdn+" ("+label+")*\n"
    JIRA_CMT_STR+="{code:java}\n"
    op=""
    cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/; cd;cd /opt/splunk/etc/;cp -pR users/ /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"
    op= os.popen(cmd).read()
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  cp -pR users/ /opt/splunk/tmp/"+JIRA_ID+"/\n"

    with open('tempf.txt', 'w') as f:
        print(op, file=f)

    with open("tempf.txt","r") as file_one:
        patrn1="No such file or directory"
        for line in file_one:
            if re.search(patrn1, line):
                JIRA_CMT_STR+=f"\n------>    etc/users not found    <------\n\n"
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"
    with open("tempf.txt","r") as file_one:
        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_CMT_STR+=line
                    
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ date\n"
    JIRA_CMT_STR+=DATE
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ \n"
    JIRA_CMT_STR+="{code}\n"

    return JIRA_CMT_STR

def pre_scp_operation(JIRA_CMT_STR, node_fqdn, JIRA_ID) -> str:
    print(f"converting backup to tgz on /home/{USER_NAME}/ ... ")
    try:
        subprocess.call(['sh', './scp_pre-req.sh',node_fqdn,USER_NAME,JIRA_ID])
    except Exception as e:
        print("An error occurred:", e)
        
    JIRA_CMT_STR+="*Creating tgz file and changing ownership :*\n"
    JIRA_CMT_STR+="{code:java}\n"
    #JIRA_SCK_STR+=f"[STD-LVE]06:22:30 root@{node_fqdn} /opt/splunk/tmp # \n"
    with open('out.txt', 'r') as f:
        for line in f:
            JIRA_CMT_STR+=line
    JIRA_CMT_STR+="{code}\n"
    
    return JIRA_CMT_STR

def base_path(JIRA_ID, label) -> str:
    if label == "c0m1":
        base_dir = "cluster_master"
    elif label.startswith('sh'):
        base_dir = f"search_head/{label}"
    elif label.startswith('idm'):
        base_dir = f"inputs_data_manager/{label}"
    else:
        raise ValueError(f"Invalid label: {label}")
        
    base_path = os.path.expanduser(f"~/{JIRA_ID}/{base_dir}")
    return base_path

def scp_operation_backup(JIRA_CMT_STR, node_fqdn, JIRA_ID, label) -> str:
    print("Copying backup to your local machine")
    scp_path = base_path(JIRA_ID, label)

    if not os.path.exists(scp_path):
        os.makedirs(scp_path)
    print(scp_path)

    try:
        scp_command = ["scp", f"@{node_fqdn}:{node_fqdn}.tgz", scp_path]
        result = subprocess.run(scp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode() + result.stderr.decode()
        print(output)
        JIRA_CMT_STR += f"scp tgz file to local from {label} - {node_fqdn}\n" + output
        pass
    except Exception as e:
        print(f"Error copying file from {node_fqdn}:", e)
    
    check_integrity(JIRA_CMT_STR, get_md5sum(node_fqdn, scp_path, True), get_md5_local(scp_path+"/"+node_fqdn), node_fqdn, label)
    return JIRA_CMT_STR

def get_md5sum(node_fqdn, scp_path, store=False) -> str:
    print(f"Getting md5sum for {node_fqdn}.tgz on {node_fqdn} ... ")
    op=""
    cmd = "sft ssh " + node_fqdn + f" --command 'md5sum {node_fqdn}.tgz'"
    print(cmd)
    op= os.popen(cmd).read().split()[0].strip()
    if store:
        with open(f'{scp_path}/{node_fqdn}.md5', 'w') as hash_file:
            print(f'{scp_path}/{node_fqdn}.md5')
            hash_file.write(op)
    return op

def get_md5_local(file_base_path) -> str:
    hasher = hashlib.md5()
    with open(f"{file_base_path}.tgz", 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            return hasher.update(chunk)
    
def check_integrity(JIRA_CMT_STR, source_stack_md5, destination_md5, node_fqdn, label) -> str:
    print(f"Checking integrity for {node_fqdn}.tgz ... ")
    JIRA_CMT_STR+="*Checking integrity for "+node_fqdn+" ("+label+")*\n"
    JIRA_CMT_STR+="{code:java}\n"
    JIRA_CMT_STR+=f"md5 matched for {node_fqdn}, file integrity maintained"
    if source_stack_md5 == destination_md5:
        print("md5 matched, file integrity maintained! ")
    else:
        print("Not matched someting went wrong")
    JIRA_CMT_STR+="{code}\n"
    
    return JIRA_CMT_STR

def read_md5_file(md5_path) -> str:
    with open(md5_path, "r") as file:
        md5 = file.read().strip()
    return md5

def scp_operation_restore(JIRA_CMT_STR, JIRA_ID, source_file_name, node_fqdn, label) -> str:
    print("Copying backup to instance")
    scp_path = base_path(JIRA_ID, label)

    if not os.path.exists(scp_path):
        os.makedirs(scp_path)
    print(scp_path)

    try:
        
        scp_command = ["scp", f"{scp_path}/{source_file_name}.tgz", f"@{node_fqdn}:{node_fqdn}.tgz"]
        result = subprocess.run(scp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode() + result.stderr.decode()
        JIRA_CMT_STR += f"scp tgz file to {label} - {node_fqdn}\n" + output
        
    except Exception as e:
        print(f"Error copying file to {node_fqdn}:", e)
    
    JIRA_CMT_STR = check_integrity(JIRA_CMT_STR, read_md5_file(f"{scp_path}/{source_file_name}.md5"), get_md5sum(node_fqdn, scp_path), node_fqdn, label)
    
    return JIRA_CMT_STR
    
def app_specific_restore(JIRA_CMT_STR, JIRA_ID, node_fqdn, label) -> str:
    print("Restoring Backup ... ")
    JIRA_CMT_STR+="*on "+node_fqdn+" ("+label+")*\n"
    op=""
    JIRA_CMT_STR+="{code:java}\n"

    #cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+"/;cd;cd /opt/splunk/etc/;cp -pR "+location+"/ /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
    cmd = "sft ssh " + node_fqdn + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;cd /opt/splunk/tmp/"+JIRA_ID+"/; cp -pR apps/ /opt/splunk/etc/\"'"
    op= os.popen(cmd).read()
    JIRA_CMT_STR+=f"splunk@{node_fqdn}:~/tmp/{JIRA_ID}$  cp -pR apps/ /opt/splunk/etc/\n"

    with open('tempf.txt', 'w') as f:
        print(op, file=f)
    with open("tempf.txt","r") as file_one:
        patrn1="No such file or directory"
        for line in file_one:
            if re.search(patrn1, line):
                JIRA_CMT_STR+=f"\n------>    /etc/users/ not found   <------\n\n"             
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
        
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"   
    with open("tempf.txt","r") as file_one:
        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_CMT_STR+=line
    
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ date\n"
    JIRA_CMT_STR+=DATE
    JIRA_CMT_STR+="splunk@"+node_fqdn+":~/etc$ \n"
    JIRA_CMT_STR+="{code}\n"
        
    return JIRA_CMT_STR

def user_specific_restore(JIRA_CMT_STR, node_fqdn, JIRA_ID, label):
    pass
def post_scp_operation(JIRA_CMT_STR, JIRA_ID, node_fqdn) -> str:
    print(f"Changing ownership and move to /opt/splunk/tmp ... ")
    try:
        subprocess.call(['sh', './post_scp_action.sh',node_fqdn,"splunk",JIRA_ID])
    except Exception as e:
        print("An error occurred:", e)
        
    JIRA_CMT_STR+=f"*Changing ownership of {node_fqdn}.tgz and moving olderfile to .old files if exist and move {node_fqdn}.tgz to /opt/splunk/tmp/:*\n"
    JIRA_CMT_STR+="{code:java}\n"
    #JIRA_SCK_STR+=f"[STD-LVE]06:22:30 root@{node_fqdn} /opt/splunk/tmp # \n"
    with open('out.txt', 'r') as f:
        for line in f:
            JIRA_CMT_STR+=line
    JIRA_CMT_STR+="{code}\n"
    
    return JIRA_CMT_STR









def kvstore_backup(JIRA_KV_STR,node,PASS,JIRA_ID,package,backup_type):
    print("Taking KVStore Backup ... ")
    back = package
    if backup_type == "full":
        subprocess.call(['sh', './kv_back.sh',node,PASS,JIRA_ID])
        JIRA_KV_STR+="h2. *KVStore Backup*\n"
        JIRA_KV_STR+="*on "+node+"*\n"
        JIRA_KV_STR+="{code:java}\n"
        JIRA_KV_STR+="splunk@"+node+":~$ splunk backup kvstore -archiveName backup-"+JIRA_ID+"\n"
        JIRA_KV_STR+="splunk@"+node+":~$ \n"
        JIRA_KV_STR+="{code}\n"
        JIRA_KV_STR=kv_jira_commnet(JIRA_KV_STR,node,JIRA_ID,JIRA_ID)

    if backup_type == "app":
        JIRA_KV_STR+="h2. *KVStore Backup*\n"
        JIRA_KV_STR+="*on "+node+"*\n"
        JIRA_KV_STR+="{code:java}\n"
        for i in package:
            package=str(package).strip()
            subprocess.call(['sh', './kv_back_app.sh',node,PASS,i])
            print("Backup is in progress wait for 60 secounds ...")
            time.sleep(60)    
            move_next = False            
            JIRA_KV_STR+="splunk@"+node+":~$ splunk backup kvstore -archiveName backup-"+i+" -appName "+i+"\n"
            if query_yes_no("\n\nCheck KV Store status is ready on not ?", "yes"):
                pass
            else:
                while not move_next:
                    print("Again sleep for 60 secounds Backup is in progress ...")
                    time.sleep(60)   
                    move_next=query_yes_no("\n\nCheck KV Store status is ready on not ?", "no") 
                    time.sleep(60)
        JIRA_KV_STR+="splunk@"+node+":~$ \n"
        JIRA_KV_STR+="{code}\n"
        JIRA_KV_STR=kv_jira_commnet(JIRA_KV_STR,node,JIRA_ID,back)

    return JIRA_KV_STR


def kv_jira_commnet(JIRA_KV_STR,node,JIRA_ID,package_name):
    JIRA_KV_STR+="{code:java}\n"
    if package_name == JIRA_ID:
        cmd = "sft ssh " + node + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+";cd;cd /opt/splunk/var/lib/splunk/kvstorebackup/;cp -pR backup-"+package_name+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"  
        op= os.popen(cmd).read()
        JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  cp -pR backup-"+package_name+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/\n"
        JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n"
    else:
        for i in range(len(package_name)):
            cmd = "sft ssh " + node + " --command 'sudo su  - splunk -c \"date;cd /opt/splunk/;mkdir /opt/splunk/tmp/"+JIRA_ID+";cd;cd /opt/splunk/var/lib/splunk/kvstorebackup/;cp -pR backup-"+str(package_name[i])+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/;ls -la /opt/splunk/tmp/"+JIRA_ID+"/\"'"
            op= os.popen(cmd).read()
            JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  cp -pR backup-"+str(package_name[i])+".tar.gz /opt/splunk/tmp/"+JIRA_ID+"/\n"

            with open('tempf.txt', 'w') as f:
                print(op, file=f)

            with open("tempf.txt","r") as file_one:
                patrn1="No such file or directory"
                for line in file_one:
                    if re.search(patrn1, line):
                        JIRA_KV_STR+="\n------>    Package not found - ("+str(package_name[i])+")    <------\n\n"
                        break     
                    
    with open('tempf.txt', 'w') as f:
        print(op, file=f)
    JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$  ls -la /opt/splunk/tmp/"+JIRA_ID+"/\n" 
    
    with open("tempf.txt","r") as file_one:

        patrn = "Tab-completion"
        patrn4 = "closed"
        patrn1="No such file or directory"
        patrn3="mkdir: cannot create directory"
        patrn5="UTC"
        for line in file_one:
            if re.search(patrn, line):
                pass
            elif re.search(patrn3, line):
                pass
            elif re.search(patrn4, line):
                pass
            elif re.search(patrn5, line):
                DATE = line
            elif re.search(patrn1, line):
                pass
            else:
                JIRA_KV_STR+=line
    JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$ date\n"
    JIRA_KV_STR+=DATE
    JIRA_KV_STR+="splunk@"+node+":~/var/lib/splunk/kvstorebackup$ \n"
    JIRA_KV_STR+="{code}\n"
    
    return JIRA_KV_STR