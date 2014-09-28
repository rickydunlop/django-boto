import unittest
from django_boto.s3.storage import S3Storage


class TestStorageBasic(unittest.TestCase):

    def test_repr(self):
        self.assertEqual(repr(S3Storage(bucket_name='test')),
                         'S3 Bucket Storage test')
