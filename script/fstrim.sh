#!/bin/bash
log=/data/log.txt
sleep 5
echo "=====================" >> $log
date >> $log
/sbin/fstrim -v /media/sd >> $log
devicelist=$(/usr/bin/lsblk -dn -I8 -oNAME)
echo $devicelist
for dev in $devicelist; do
    echo do $dev
    rotational=$(cat /sys/block/$dev/queue/rotational)
    echo rotational: $rotational
    if [ "x$rotational" = "x0" ]; then
        echo /dev/${dev}1
        if [ -e /dev/${dev}1 ]; then
            fstype=$(/usr/bin/lsblk /dev/${dev}1 -rn -oFSTYPE,DISC-ZERO)
            echo fstype $fstype
            if [ "x$fstype" = "xext4 1" ]; then
                mountpoint=$(/usr/bin/lsblk /dev/${dev}1 -n -oMOUNTPOINT)
                echo mountpoint: $mountpoint
                if [ -n $mountpoint ]; then
                    /sbin/fstrim -v $mountpoint >> $log
                fi
            fi
        fi 
    fi
done
