from __future__ import absolute_import
import json
import os

from celery.task import task
from image_builder.imagebuilder import ImageBuilder

@task
def build(buildconfig, kickstart):

    builder = ImageBuilder(json.loads(buildconfig), kickstart)
    status = builder.build()

    # JSON dump of the log file
    logfile = builder.getlogfile()
    with open(logfile,'r') as f:
        logfile_str = json.dumps(f.read())

    return [status, logfile_str]
