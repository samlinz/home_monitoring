#!/usr/bin/env bash

HOME_DIR=~

# Set the monitoring environment variables.
export MONITORING_ROOT="projektit/monitoring"
export MONITORING_LOGS_ROOT="$HOME_DIR/monitoring_logs"

DD_PROCESS=$(ps aux | grep "dogstatsd" | wc -l)
CAM_PROCESS=$(ps aux | grep "python3 temperature_dd.py" | wc -l)
TEMP_PROCESS=$(ps aux | grep "python3 s3_capture.py" | wc -l)

DD_OUTPUT_FILE="$MONITORING_LOGS_ROOT/datadog-$(date '+%y-%m-%d').log"
TEMP_OUTPUT_FILE="$MONITORING_LOGS_ROOT/temperature-$(date '+%y-%m-%d').log"
CAM_OUTPUT_FILE="$MONITORING_LOGS_ROOT/camera-$(date '+%y-%m-%d').log"

# PYTHONPATH has to be extended for some scripts that use in-package imports.
PYTHONPATH_PREFIX="PYTHONPATH=$HOME_DIR/$MONITORING_ROOT/"

# REDACTED PERSONAL CONFIGURATION
CAM_BUCKET_NAME=XXX
CAM_CAPTURE_FOLDER=XXX

DD_COMMAND="$HOME_DIR/.datadog-agent/bin/agent >> \"$DD_OUTPUT_FILE\" 2>&1 &"
CAM_COMMAND="$PYTHONPATH_PREFIX python3 -u $HOME_DIR/$MONITORING_ROOT/cloud_camera/camera_app.py --interval 10 --clean_interval 1800 --filesystem --filesystem_limit 2 --path $CAM_CAPTURE_FOLDER --s3 --s3_bucket $CAM_BUCKET_NAME --s3_interval 6 >> \"$CAM_OUTPUT_FILE\" 2>&1 &"
TEMP_COMMAND="python3 -u $HOME_DIR/$MONITORING_ROOT/temp_hum_sensor/temperature_dd.py --pin 17 >> \"$TEMP_OUTPUT_FILE\" 2>&1 &"

if [[ $DD_PROCESS -lt 2 ]]; then
    echo "Starting DataDog Agent"
    echo "================" >> "$DD_OUTPUT_FILE"
    echo "$DD_COMMAND"
    nohup sh -c "$DD_COMMAND" >/dev/null 2>&1
else
    echo "DataDog Agent is already running"
fi

if [[ $CAM_PROCESS -lt 2 ]]; then
    echo "Starting S3 WebCam"
    echo "================" >> "$CAM_OUTPUT_FILE"
    echo "$CAM_COMMAND"
    nohup sh -c "$CAM_COMMAND" >/dev/null 2>&1
else
    echo "S3 WebCam is already running"
fi

if [[ $TEMP_PROCESS -lt 2 ]]; then
    echo "Starting Temperature/Humidity monitoring"
    echo "================" >> "$TEMP_OUTPUT_FILE"
    echo "$TEMP_COMMAND"
    nohup sh -c "$TEMP_COMMAND" >/dev/null 2>&1
else
    echo "Temperature/Humidity monitoring already running"
fi

echo Done