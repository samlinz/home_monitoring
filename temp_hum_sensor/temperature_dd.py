import argparse
import datetime
import json
import os
import sched
import sys
import time

# 3rd party modules.
import Adafruit_DHT
import datadog

# Parse command line arguments.
parser = argparse.ArgumentParser(description='Measure values from DHT22 sensor and send them to cloud')
parser.add_argument('--nocloud', action='store_true', help='If present, don\'t forward to cloud')
parser.add_argument('--storefile', action='store_true', help='If present, save into file')
parser.add_argument('--path', help='The directory into which the measurements are also sent')
parser.add_argument('--credentials', help='The DD credentials file')
parser.add_argument('--interval', type=int, help='The interval in seconds at which measurements are recorded and sent')
parser.add_argument('--pin', type=int, required=True, help='BCM numbering scheme GPIO pin number to use')
parsed = parser.parse_args()

# Credentials file.
DEFAULT_CREDENTIALS_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'credentials.json'
)
cred_file = parsed.credentials if parsed.credentials is not None else DEFAULT_CREDENTIALS_FILE
# Flag of whether to use clod storage or not.
USE_CLOUD = not parsed.nocloud
# Flag whether to save to filesystem.
USE_FILE = parsed.storefile
# Meas files directory.
FILE_DIR = parsed.path if parsed.path is not None else '.'
# Interval.
INTERVAL_SECONDS = parsed.interval if parsed.interval is not None else 10
# Sensor pin number.
SENSOR_PIN_BCM = parsed.pin

FILE_DIRNAME = os.path.dirname(os.path.realpath(__file__))

if INTERVAL_SECONDS <= 0:
    raise ValueError('Interval is zero or below')

print('Using interval of {0} seconds'.format(INTERVAL_SECONDS))

if USE_FILE:
    print('Saving measurements to directory {0}'.format(
        os.path.realpath(FILE_DIR)
    ))

if not USE_CLOUD and not USE_FILE:
    print('You don\'t store the values anywhere! Specify either a cloud endpoint or file')
    sys.exit(1)

# Read credentials from file.
if not os.path.exists(cred_file):
    print('Credentials file {0} does not exists!'.format(cred_file))
    sys.exit(1)

try:
    with open(cred_file) as f:
        credentials_obj = json.load(f)
    DD_API_KEY = credentials_obj['api']
    DD_APP_KEY = credentials_obj['app']
    if len(DD_API_KEY) == 0:
        raise Exception()
    if len(DD_APP_KEY) == 0:
        raise Exception()
except:
    print('Invalid credentials file!')
    sys.exit(1)

# Settings
SENSOR_TYPE = Adafruit_DHT.DHT22

# Initialize datadog connection.
datadog.initialize(DD_API_KEY, DD_APP_KEY)

# Initialize task scheduler.
scheduler = sched.scheduler(time.time, time.sleep)


def get_filename(meas_name, extension='csv'):
    """
    Generate the daily rotating file name for the given measurement.
    """
    date_str = datetime.datetime.now().isoformat()[:10]
    return '{0}-{1}.{2}'.format(meas_name, date_str, extension)


def send_meas_cloud(**kwargs):
    """
    Send arbitrary float values to DD.
    """
    for meas_name, value in kwargs.items():
        if value is None:
            continue

        datadog.statsd.gauge(meas_name, float(value))


def send_meas_filesystem(**kwargs):
    """
    Save values to file system.
    """
    for meas_name, value in kwargs.items():
        if value is None:
            continue

        filename = get_filename(meas_name)
        full_path = os.path.join(FILE_DIR, filename)
        file_mode = 'a' if os.path.exists(full_path) else 'w'
        timestamp = int(time.time())

        with open(full_path, mode=file_mode) as f:
            f.write('{0},{1}\n'.format(timestamp, float(value)))


def get_readings_task():
    """
    Regular task which reads the sensor readings and forwards them
    to to cloud and/or filesystem CSV files.
    """

    print('Getting readings')

    try:
        humidity, temperature = \
            Adafruit_DHT.read_retry(SENSOR_TYPE, SENSOR_PIN_BCM)

        print('Humidity {0}, temperature {1}'.format(humidity,
                                                     temperature))

        if USE_CLOUD:
            send_meas_cloud(temperature=float(temperature)
                            , humidity=float(humidity))

        if USE_FILE:
            send_meas_filesystem(temperature=float(temperature)
                                 , humidity=float(humidity))

    except Exception as err:
        print('Exception while reading/sending measurements: {0}'.format(
            err
        ))

    # Reschedule.
    scheduler.enter(INTERVAL_SECONDS, 1, get_readings_task)


# Initial readings.
get_readings_task()

print('Entering main application loop')
scheduler.run()
