# -*- coding: utf-8 -*-
import logging
from dateutil.parser import parse as parse_date
from tempfile import TemporaryFile

from django.core.files.storage import Storage
from django.utils import timezone
from django.conf import settings as _settings

from boto import connect_s3
from boto.s3.connection import Location
from boto.exception import S3CreateError, S3ResponseError

from django_boto.utils import setting


logger = logging.getLogger(__name__)


class S3Storage(Storage):

    """
    Storage class.
    """

    def __init__(self, bucket_name=None, key=None, secret=None, location=None,
                 host=None, policy=None, replace=True, force_http_url=False):

        self.bucket_name = bucket_name if bucket_name else setting(
            'BOTO_S3_BUCKET')
        self.key = key if key else setting('AWS_ACCESS_KEY_ID')
        self.secret = secret if secret else setting('AWS_SECRET_ACCESS_KEY')
        self.host = host if host else setting('BOTO_S3_HOST')
        self.policy = policy if policy else setting('AWS_ACL_POLICY')
        self.force_http = force_http_url if force_http_url else setting(
            'AWS_S3_FORCE_HTTP_URL')
        self.replace = replace
        self._set_location(
            location if location else setting('BOTO_BUCKET_LOCATION'))
        self._bucket = None

    def __repr__(self):
        return 'S3 Bucket Storage {}'.format(self.bucket_name)

    def _set_location(self, location):
        if location is not None:
            self.location = getattr(Location, location)

    @property
    def bucket(self):
        if not self._bucket:
            self.s3 = connect_s3(
                aws_access_key_id=self.key,
                aws_secret_access_key=self.secret,
                host=self.host)
            try:
                self._bucket = self.s3.create_bucket(
                    self.bucket_name, location=self.location,
                    policy=self.policy)
            except (S3CreateError, S3ResponseError):
                self._bucket = self.s3.get_bucket(self.bucket_name)
        return self._bucket

    def delete(self, name):
        """
        Delete file.
        """
        self.bucket.new_key(name).delete()

    def exists(self, name):
        """
        Existing check.
        """
        return self.bucket.new_key(name).exists()

    def _list(self, path):
        result_list = self.bucket.list(path, '/')

        for key in result_list:
            yield key.name

    def listdir(self, path):
        """
        Catalog file list.
        """
        return [], self._list(path)

    def size(self, name):
        """
        File size.
        """
        return self.bucket.lookup(name).size

    def url(self, name, expires=30, query_auth=False, force_http=None):
        """
        URL for file downloading.
        """
        if not force_http:
            force_http = self.force_http
        if name == 'admin/':
            # https://code.djangoproject.com/ticket/19538
            return _settings.S3_URL + 'admin/'
        key = self.bucket.get_key(name)
        return key.generate_url(expires, query_auth=query_auth,
                                force_http=force_http)

    def _open(self, name, mode='rb'):
        """
        Open file.
        """
        result = TemporaryFile()
        self.bucket.get_key(name).get_file(result)

        return result

    def _save(self, name, content):
        """
        Save file.
        """
        key = self.bucket.new_key(name)
        content.seek(0)

        if self.replace:
            try:
                key.set_contents_from_file(content, replace=True)
            except Exception as e:
                raise IOError('Error during uploading file - %s' % e)
        else:
            if key.exists():
                raise IOError(
                    'File already exists and can\'t be replaced - %s' % name)
            else:
                try:
                    key.set_contents_from_file(content, replace=False)
                except Exception as e:
                    raise IOError('Error during uploading file - %s' % e)

        content.seek(0, 2)
        orig_size = content.tell()
        saved_size = key.size

        if saved_size == orig_size:
            key.set_acl(self.policy)
        else:
            key.delete()

            raise IOError('Error during saving file %s - saved %s of %s bytes'
                          % (name, saved_size, orig_size))

        return name

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        Handled by Boto itself.
        """

        return name

    def modified_time(self, name):
        """
        Last modification time.
        """
        return timezone.make_naive(
            parse_date(self.bucket.lookup(name).last_modified),
            timezone.get_default_timezone())

    created_time = accessed_time = modified_time
