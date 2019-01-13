import re
import os
import shutil
from datetime import datetime, timedelta

DATE_FORMAT = '%Y-%m-%d'
DIR_PREFIX = 'captures'


class Filesystem_Uploader:
    def __init__(self, target_directory, date_limit):
        if target_directory is None or not os.path.exists(target_directory) or not os.path.isdir(target_directory):
            raise ValueError('Invalid target_directory')
        if date_limit is None or not isinstance(date_limit, int) or date_limit < 0:
            raise ValueError('Invalid date_limit')

        self.target_directory = target_directory
        self.date_limit = date_limit

        print('Filesystem_Uploader initialized with target_directory:{0}, date_limit:{1}'.format(
            self.target_directory,
            self.date_limit,
        ))

    def purge_irrelevant(self):
        # This is not needed with file system at the moment.
        pass

    def purge_old(self):
        """
        Remove directories of captures that exceed the max age passed in to
        the constructor.
        """
        files = os.listdir(self.target_directory)

        if len(files) == 0:
            return

        print('Removing old captures from file system')

        today = datetime.today().date()
        purge_older_than = today - timedelta(days=self.date_limit)

        for filename in files:
            full_filename = os.path.join(self.target_directory, filename)
            if not os.path.isdir(full_filename):
                continue

            file_date = self._get_date_from_directory_filename(filename)
            if file_date is None:
                continue

            if file_date < purge_older_than:
                dir_file_count = len(os.listdir(full_filename))

                print('Removing {0} files from old directory {1}'.format(
                    dir_file_count,
                    full_filename
                ))
                shutil.rmtree(full_filename)

    def upload(self, file_path, target_filename):
        """
        Copy or 'upload' the temporary capture file into the target
        directory with other captures from today.
        """

        if not os.path.exists(file_path):
            raise ValueError('Capture file {0} does not exists'.format(
                file_path
            ))

        # Get name and full path for directory of today's files.
        dirname = self._get_current_directory_name()
        full_target_directory = os.path.join(self.target_directory, dirname)

        # Create the capture directory if it doesn't exists.
        if not os.path.exists(full_target_directory):
            print('Creating directory {0}'.format(
                full_target_directory
            ))
            os.mkdir(full_target_directory)

        # Get full path for target file.
        full_target_filename = os.path.join(full_target_directory, target_filename)

        # Copy temp capture into permanent storage.
        print('Copying capture {0} to {1}'.format(
            file_path,
            full_target_filename
        ))
        shutil.copyfile(file_path, full_target_filename)

    def _get_current_directory_name(self):
        """
        Get directory name for today's files.
        """

        return '{0}-{1}'.format(
            DIR_PREFIX,
            datetime.today().strftime(DATE_FORMAT)
        )

    def _get_date_from_directory_filename(self, filename):
        """
        Extract date object from directory's name.
        Returns None if not relevant name.
        """

        matches = re.search('^{0}-([\d-]+)$'.format(DIR_PREFIX), filename)

        if matches is None:
            return None

        try:
            return datetime \
                .strptime(matches.group(1), DATE_FORMAT) \
                .date()
        except:
            return None
