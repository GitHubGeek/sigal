# -*- coding: utf-8 -*-

"""Plugin to upload generated files to Amazon S3.

This plugin requires boto_. All generated files are uploaded to a specified S3 bucket.
When using this plugin you have to make sure that the bucket already exists and the 
you have access to the S3 bucket. The access credentials are managed by boto_ and
can be given as environment variables, configuration files etc. More information
can be found on the boto_ documentation.

.. _boto: https://pypi.python.org/pypi/boto

Settings (all settings are wrapped in ``upload_s3_options`` dict):

- ``bucket``: The to-be-used bucket for uploading.
- ``policy``: Specifying access control to the uploaded files. Possible values:
              private, public-read, public-read-write, authenticated-read
- ``overwrite``: Boolean indicating if all files should be uploaded and overwritten
                 or if already uploaded files should be skipped.

"""

import logging
import os
from sigal import signals
import boto
from boto.s3.key import Key
from click import progressbar

logger = logging.getLogger(__name__)


def upload_s3(gallery, settings=None):
    upload_files = []

    # Get local files
    for root, dirs, files in os.walk(gallery.settings['destination']):
        for f in files:
            path = os.path.join(root[len(gallery.settings['destination'])+1:], f)
            size = os.path.getsize(os.path.join(root, f))
            upload_files += [ (path, size) ]

    # Connect to specified bucket
    conn = boto.connect_s3()
    bucket = conn.get_bucket(gallery.settings['upload_s3_options']['bucket'])

    # Upload the files
    with progressbar(upload_files, label="Uploading files to S3") as progress_upload:
        for (f, size) in progress_upload:
            if gallery.settings['upload_s3_options']['overwrite'] == False:
                # Check if file was uploaded before
                key = bucket.get_key(f)
                if key != None and key.size == size:
                    logger.debug("Skipping file %s" % (f))
                else:
                    upload_file(gallery, bucket, f)
            else:
                # File is not available on S3 yet
                upload_file(gallery, bucket, f)

def upload_file(gallery, bucket, f):
    logger.debug("Uploading file %s" % (f))
    key = Key(bucket)
    key.key = f
    key.set_contents_from_filename(
        os.path.join(gallery.settings['destination'], f), 
        policy = gallery.settings['upload_s3_options']['policy'])

def register(settings):
    if settings.get('upload_s3_options'):
        signals.gallery_build.connect(upload_s3)
    else:
        logger.warning('Upload to S3 is not configured.')