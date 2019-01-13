import argparse
import json
import os
import sched
import subprocess
import sys
import time

from cloud_camera.cam_utils import get_current_filename
from cloud_camera.uploaders import s3_uploader, filesystem_uploader

parser = argparse.ArgumentParser()
parser.add_argument('--s3', action='store_true', help='Upload to AWS S3 bucket')
parser.add_argument('--s3_bucket', help='S3 bucket name')
parser.add_argument('--s3_limit', help='Limit of files in S3 bucket')
parser.add_argument('--s3_interval', type=int, help='If present, upload only the n-th image to cloud')
parser.add_argument('--credentials', help='Credentials file')
parser.add_argument('--filesystem', action='store_true', help='Save to file system')
parser.add_argument('--filesystem_limit', type=int, help='Max days the captures are retained in file system')
parser.add_argument('--path', help='Path of directory into which to save the images')
parser.add_argument('--interval', type=int, required=True, help='Interval on which to take pictures')
parser.add_argument('--clean_interval', type=int, required=True, help='Interval on which to clean the old pictures')
parsed = parser.parse_args()

# List of uploaders which get passed the created file name.
# Uploaders pass the file wherever they want to, to cloud or file system etc.
uploaders = []

# File name as which the latest image is saved and passed to uploaders.
TEMP_FILE_NAME = 'capture.jpg'

# Interval at which pictures are taken.
CAPTURE_INTERVAL_SECONDS = parsed.interval
# Interval at which files are iterated and old captures removed.
CLEAN_INTERVAL_SECONDS = parsed.clean_interval

if CAPTURE_INTERVAL_SECONDS < 1:
    print('Invalid interval {0}'.format(CAPTURE_INTERVAL_SECONDS))
    sys.exit(1)

DEFAULT_CREDENTIALS_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'credentials.json'
)
CREDENTIALS_FILE = parsed.credentials if parsed.credentials is not None else DEFAULT_CREDENTIALS_FILE
if not os.path.exists(CREDENTIALS_FILE):
    print('Credentials file does not exists')
    sys.exit(1)

if not parsed.s3 and not parsed.filesystem:
    print('You specified no target for files, specify cloud provider and/or file system')
    sys.exit(1)

if parsed.s3:
    # Set up S3 uploader.
    print('Initializing S3 uploader')
    try:
        with open(CREDENTIALS_FILE) as f:
            credentials_file = json.load(f)

        AWS_ACCESS_KEY_ID = credentials_file['aws_key_id']
        AWS_SECRET_ACCESS_KEY = credentials_file['aws_access_key']

        if AWS_SECRET_ACCESS_KEY is None or len(AWS_SECRET_ACCESS_KEY) == 0:
            raise Exception()
        if AWS_ACCESS_KEY_ID is None or len(AWS_ACCESS_KEY_ID) == 0:
            raise Exception()
    except:
        print('Failed to read credentials')
        sys.exit(1)

    try:
        _uploader = s3_uploader.S3_Uploader(AWS_ACCESS_KEY_ID
                                            , AWS_SECRET_ACCESS_KEY
                                            , bucket_name=parsed.s3_bucket
                                            , file_count_limit=parsed.s3_limit if parsed.s3_limit is not None else 1000
                                            , take_nth=parsed.s3_interval if parsed.s3_interval is not None else 5)
        _uploader.connect()
        uploaders.append(_uploader)
    except Exception as err:
        print('Failed to connect to AWS S3: {0}'.format(err))
        sys.exit(1)

if parsed.filesystem:
    # Set up file system uploader.
    print('Initializing filesystem uploader')
    try:
        if not os.path.exists(parsed.path) or not os.path.isdir(parsed.path):
            raise ValueError('Path {0} does not exist'.format(parsed.path))

        _uploader = filesystem_uploader.Filesystem_Uploader(target_directory=parsed.path,
                                                            date_limit=parsed.filesystem_limit)
        uploaders.append(_uploader)
    except Exception as err:
        print('Failed to set up file system uploader: {0}'.format(
            err
        ))
        sys.exit(1)

# Flag which indicates if capturing image or upload is in progress,
# so another task doesn't start.
in_progress = False


def take_photo():
    """
    Take a photo and return boolean value indicating the success.
    """

    print('Taking a photo')

    # Run web cam program and create capture.
    command = ['fswebcam', '--no-banner', '--jpeg', '95', TEMP_FILE_NAME]

    try:
        process_result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        code = process_result.returncode
        stdout = process_result.stdout
        stderr = process_result.stdout

        if code != 0:
            print('Non-ok return code {0} from capture subprocess')
            print('STDOUT: {0}'.format(stdout))
            print('STDERR: {0}'.format(stderr))
            return False
    except Exception as err:
        print('Exception while running capture subprocess: {0}'.format(err))

    return True


def capture_task():
    """
    Run photo capturing task.
    """

    global in_progress

    if in_progress:
        print('Deferring capture, in_progress=True')
        return

    in_progress = True

    print('Running capture/upload sequence, timestamp {0}'.format(time.time()))

    try:
        photo_success = take_photo()
        if photo_success:
            target_file_name = get_current_filename()

            for uploader in uploaders:
                # Iterate the uploaders and send the capture to each.
                print('Passing the capture to uploader {0}'.format(
                    uploader.__class__.__name__
                ))
                uploader.upload(TEMP_FILE_NAME, target_file_name)
    except Exception as err:
        print('Exception while running capture/upload sequence: {0}'.format(err))

    in_progress = False


# Create scheduler
scheduler = sched.scheduler(time.time, time.sleep)


def schedule_capture_task():
    print('Running capture task')
    try:
        capture_task()
    except Exception as err:
        print('Exception while running capture_task: {0}'.format(err))

    # Reschedule the same task.
    scheduler.enter(CAPTURE_INTERVAL_SECONDS, 1, schedule_capture_task)


def schedule_cleanup_task(rethrow=False):
    print('Running cleanup task')

    for uploader in uploaders:
        try:
            uploader.purge_old()
        except Exception as err:
            print('Exception while running purge_old for {0}: {1}'.format(
                uploader.__class__.__name__,
                err
            ))

            if rethrow:
                # Rethrow the exception to stop execution flow when requested.
                raise

    # Reschedule the same task.
    scheduler.enter(CLEAN_INTERVAL_SECONDS, 1, schedule_cleanup_task)


print('Purging irrelevant files')
for uploader in uploaders:
    # Iterate uploaders, order all to purge irrelevant files.
    # Do this only once at startup.
    try:
        uploader.purge_irrelevant()
    except Exception as err:
        print('Exception while running purge_irrelevant for {0}: {1}'.format(
            uploader.__class__.__name__,
            err
        ))
        sys.exit(1)

try:
    # Run the cleanup tasks for all uploaders for the first time.
    # This will schedule the task periodically and also verify that cleanup works.
    schedule_cleanup_task(rethrow=True)
except Exception as err:
    print('Exception while running initial cleanup tasks: {0}'.format(
        err
    ))
    sys.exit(1)

# Schedule the image capturing task.
scheduler.enter(CAPTURE_INTERVAL_SECONDS, 1, schedule_capture_task)

print('Starting main application loop')
scheduler.run()
