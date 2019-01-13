#!/usr/bin/env bash

echo "Stopping monitoring processes"

DD_PROCESS_PID=$(pgrep supervisord -a | grep datadog | cut -d ' ' -f 1)
DD_PROCESS_PID2=$(pgrep sh -a | grep bin/agent | cut -d ' ' -f 1)
DD_PROCESS_PID3=$(pgrep python -a | grep agent/dogstatsd.py | cut -d ' ' -f 1)
DD_PROCESS_PID4=$(pgrep python -a | grep agent/jmxfetch.py | cut -d ' ' -f 1)

TEMP_PROCESS_PID=$(pgrep python3 -a | grep "temperature_dd.py" | cut -d ' ' -f 1)
CAM_PROCESS_PID=$(pgrep python3 -a | grep "camera_app.py" | cut -d ' ' -f 1)

# Datadog processes.

if [[ "$DD_PROCESS_PID" ]]; then
    echo "Stopping DataDog process $DD_PROCESS_PID"
    kill -9 $DD_PROCESS_PID
fi

if [[ "$DD_PROCESS_PID2" ]]; then
    echo "Stopping DataDog process $DD_PROCESS_PID2"
    kill -9 $DD_PROCESS_PID2
fi

if [[ "$DD_PROCESS_PID3" ]]; then
    echo "Stopping DataDog process $DD_PROCESS_PID3"
    kill -9 $DD_PROCESS_PID3
fi

if [[ "$DD_PROCESS_PID4" ]]; then
    echo "Stopping DataDog process $DD_PROCESS_PID4"
    kill -9 $DD_PROCESS_PID4
fi

# Other processes.

if [[ "$TEMP_PROCESS_PID" ]]; then
    echo "Stopping Temperature/Humidity process $TEMP_PROCESS_PID"
    kill -9 $TEMP_PROCESS_PID
fi

if [[ "$CAM_PROCESS_PID" ]]; then
    echo "Stopping S3 WebCam process $CAM_PROCESS_PID"
    kill -9 $CAM_PROCESS_PID
fi