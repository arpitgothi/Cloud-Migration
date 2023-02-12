sft ssh $1 << EOF > out.txt
sudo su
[ -d /opt/splunk/tmp/$3 ] && [ "$(ls -A /opt/splunk/tmp/$3)" ] && mv /opt/splunk/tmp/$3 /opt/splunk/tmp/$3.old_$RANDOM
[ -f /opt/splunk/tmp/$1.tgz ] && [ "$(ls -A /opt/splunk/tmp/$1.tgz)" ] && mv /opt/splunk/tmp/$1.tgz /opt/splunk/tmp/$1.tgz.old_$RANDOM
chown $2:$2 $1.tgz
mv $1.tgz /opt/splunk/tmp/$1.tgz
cd /opt/splunk/tmp/
touch pass.1
tar -xvzf $1.tgz
touch pass.2
exit
exit
EOF 