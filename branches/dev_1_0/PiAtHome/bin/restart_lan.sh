#!/bin/bash

# Freebox
SERVER=192.168.0.254

# Send only 2 ping
/bin/ping -c2 ${SERVER} > /dev/null

# Check return code of ping
if [ $? != 0 ]
then
    echo $(date --rfc-3339=seconds) Lan down detected
    # Restart the lan interface
    /sbin/ifdown --force eth0
    /sbin/ifup eth0
    echo $(date --rfc-3339=seconds) Lan restarted
fi

