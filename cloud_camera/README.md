# Cloud camera

Periodically takes photos with webcam and saves them into filesystem.
Optionally can also forward every n-th photo to AWS S3 bucket.

Organizes photos into subfolders and periodically removes subfolders over n-days
old. Periodically iterates S3 bucket and removes oldest entries from the bucket, only allowing
specified amount (default 1000) images in bucket.

## Dependencies

Install following library that is used for AWS interfacing.
```
pip install boto3
```

The program uses another program called _fswebcam_ to take photos.

```
sudo apt update
sudo apt install fswebcam -y
```

## Usage

Decide how often you want to take pictures (seconds) and how often clean the system (seconds).
Bucket and filesystem directory can be cleaned quite sparsely, something around 1 hour (3600sec)
should be fine.

Decide which fraction of pictures saved to file system you want to send to S3, that's the
--s3_interval argument. If you want to send each, use 1.

Create a base directory for captures and get the absolute path if using filesystem.

Create AWS account, create S3 bucket, give account access to bucket and get the keys if using S3.
Save the keys into _credentials.json_ as {"aws_key_id": "XXX", "aws_access_key": "XXX"}.

```
For S3:
python3 camera_app.py --interval NUMBER --clean_interval NUMBER --s3 --s3_bucket BUCKET_NAME --credentials CREDENTIALS_FILE --s3_interval NUMBER 
 
For filesystem:
python3 camera_app.py --interval NUMBER --clean_interval NUMBER --filesystem --filesystem_limit NUMBER --path PATH

Or both combined.
```

Arguments
```
--s3                If present, use S3
--s3_bucket         S3 bucket name
--s3_limit          Max count of files in bucket (default 1000)
--s3_interval       Positive integer, every n-th capture which is sent to S3
--credentials       Credentials file
--filesystem        If present, save captures to file system
--filesystem_limit  Limit in DAYS how old subdirectories are kept in filesystem
--path              Path to capture root, under which subdirectories are created
--interval          Interval in seconds, how often to capture image
--clean_interval    Interval in seconds, how often to clean directory and S3 bucket
```