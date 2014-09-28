import unittest
import random
import string

import responses

from django_boto.s3.storage import S3Storage
from django.core.files.storage import default_storage


def get_string(lngth):
    strn = ''

    for i in range(lngth):
        strn += random.choice(string.ascii_letters)

    return strn


class TestStorageBasic(unittest.TestCase):

    def test_repr(self):
        self.assertEqual(repr(S3Storage(bucket_name='test')),
                         'S3 Bucket Storage test')

    def test_get_auth_from_settings(self):
        self.assertIsInstance(default_storage, S3Storage)
        self.assertEqual(default_storage.bucket_name, 'test_name')
        self.assertEqual(default_storage.key, 'test_key')
        self.assertEqual(default_storage.secret, 'test_secret')
        self.assertEqual(default_storage.location, 'ap-southeast-2')

    @responses.activate
    def test_exists(self):
        bucket = default_storage.exists('some_name')
