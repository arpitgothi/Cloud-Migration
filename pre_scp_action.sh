sft ssh $1 << EOF > out.txt
sudo su
cd /opt/splunk/tmp/
tar -czvf /home/$2/$1.tgz $3
chown $2:$2 /home/$2/$1.tgz
exit
exit
EOF 