#!/bin/bash

# Try reconnecting to wifi and syncing data with remote server
connected=$(hostname -I)
disconnect_when_done=0
retry_count=0

echo -e "\n=== Uploading data to file server ===\n"
if [ -z "$connected" ]; then
    nmcli radio wifi on
    disconnect_when_done=1
    while [ -z "$connected" ]; do
        if (( retry_count > 12 )); then
            echo -e "Network connection timed out (12 sec), aborting...\n"
            break
        fi
        sleep 1
        (( retry_count++ ))
        connected=$(hostname -I)
    done
fi

# If network connection active, rsync data to server
err=1
if [ -n "$connected" ]; then
    rsync -av $2 $1
    err=$?
    # If wifi was originally off, turn off again when done
    if (( disconnect_when_done == 1 )); then
        nmcli radio wifi off
    fi
fi

if (( err == 0 )); then
    echo -e "\n=== Data uploaded successfully! ===\n"
else
    echo -e "\n=== Error encountered uploading data ===\n"
fi
