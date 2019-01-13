import os

import boto3

from cloud_camera.cam_utils import *


class S3_Uploader:
    def __init__(self, key_id, key, bucket_name, file_count_limit, take_nth=1):
        if key_id is None or len(key_id) == 0:
            raise ValueError('Invalid key_id')
        if key is None or len(key) == 0:
            raise ValueError('Invalid key')
        if bucket_name is None or len(bucket_name) == 0:
            raise ValueError('Invalid bucket_name')
        if file_count_limit is None or not isinstance(file_count_limit, int):
            raise ValueError('Invalid file_count_limit')
        if take_nth is None or not isinstance(take_nth, int):
            raise ValueError('Invalid take_nth')

        self.bucket_name = bucket_name
        self.key_id = key_id
        self.key = key
        self.file_count_limit = file_count_limit
        self.take_nth = take_nth
        self.connected = False
        self.count_since_sending = 0

        print('S3 uploader initialized with bucket_name:{0}, file_count_limit:{1}, take_nth:{2}'.format(
            self.bucket_name,
            self.file_count_limit,
            self.take_nth
        ))

    def connect(self):
        """
        Connect to AWS.
        """

        print('Connecting to S3 bucket {0}'.format(self.bucket_name))
        self.session = boto3.Session(
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.key,
        )

        print('Fetching bucket {0}'.format(self.bucket_name))

        s3 = self.session.resource('s3')
        self.s3_bucket = s3.Bucket(self.bucket_name)
        self.s3_bucket.load()

        if self.s3_bucket.creation_date is None:
            raise Exception('Could not fetch bucket {0}. Verify that the name is correct and '
                            'your user has access to the bucket.'.format(self.bucket_name))

        print('Got bucket')

        self.connected = True

    def purge_irrelevant(self):
        """
            Delete all irrelevant files from the bucket.
            Irrelevant file is any that cannot be parsed.
        """

        if not self.connected: raise Exception('Not connected')

        files = self._get_all_files_in_bucket(self.s3_bucket)

        files_to_delete = []
        for file in files:
            if get_datetime_from_name(file) is None:
                files_to_delete.append({
                    'Key': file
                })
                print('Found irrelevant file {0}'.format(file))

        if len(files_to_delete) == 0:
            return

        print('Deleting {0} irrelevant files from bucket'.format(len(files_to_delete)))

        self.s3_bucket.delete_objects(Delete={
            'Objects': files_to_delete
        })

    def purge_old(self):
        """
            Maintain the max count of files in bucket.
            Sort the file names and delete old entries so that the
            max list size is maintained.
        """
        if not self.connected: raise Exception('Not connected')

        print('Checking for old files..')

        files = self._get_all_files_in_bucket(self.s3_bucket)

        file_dict = dict()
        dt_list = []

        # Get the count of files to delete.
        file_count = len(list(files))

        print('Total files in bucket: {0}'.format(file_count))

        delete_count = file_count - self.file_count_limit
        if delete_count <= 0:
            print('The file count in bucket does not exceed the threshold {}'.format(
                self.file_count_limit
            ))
            return

        for file in files:
            dt = get_datetime_from_name(file)
            if dt is None:
                continue

            file_dict[str(dt)] = file
            dt_list.append(dt)

        # Sort the datetimes and delete oldest entries.
        dt_list.sort()
        files_deleted = 0
        filenames_to_delete = []

        for dt_to_delete in dt_list:
            filename_to_delete = file_dict[str(dt_to_delete)]
            filenames_to_delete.append({
                'Key': filename_to_delete
            })

            print('Marking file {0} to be deleted from bucket'
                  .format(filename_to_delete))

            files_deleted = files_deleted + 1
            if files_deleted >= delete_count:
                break

        if len(filenames_to_delete) == 0:
            return

        print('Deleting {0} old files'.format(len(filenames_to_delete)))

        self.s3_bucket.delete_objects(Delete={
            'Objects': filenames_to_delete
        })

    def upload(self, file_path, target_name):
        """
        Upload a file into S3 bucket.
        """
        if not self.connected: raise Exception('Not connected')

        if not os.path.exists(file_path):
            print('Cannot upload file {0}, it doesn\'t exist!'.format(file_path))
            return

        # Send only the take_nth of captures, so that one can for example
        # save every capture to file system and only send some to S3 to reduce
        # costs.
        self.count_since_sending = self.count_since_sending + 1
        if self.count_since_sending < self.take_nth:
            return

        # Reset counter.
        self.count_since_sending = 0

        print('Uploading file {0} as {1}'.format(file_path, target_name))
        self.s3_bucket.upload_file(file_path, target_name)

    def _get_all_files_in_bucket(self, bucket):
        """
        Get file names for all objects in the bucket as list.
        """
        if not self.connected: raise Exception('Not connected')

        all_objects = list(bucket.objects.all())

        return list(
            map(
                lambda x: x.key, all_objects
            )
        )
