from __future__ import absolute_import
import json
import os
import logging
import time
import tempfile
from celery import Celery
from celery.signals import after_setup_task_logger

from image_builder.imagebuilder import ImageBuilder

class myFileHandler(logging.FileHandler):

    def __init__(self, logfile, mode):
        self.logfile = logfile 
        super(myFileHandler,self).__init__(self.logfile,mode)

    def getlogfile(self):
        return self.logfile


celery = Celery()
celery.config_from_object('celeryconfig')

# Return a filename of the form imagebuild_<timestamp>.log
def getfilename():
    time_now = str(time.time()).split('.')
    logfile = tempfile.gettempdir() + '/imagebuild_{0:s}.log'.format(time_now[0]+time_now[1])
    return logfile
    
@after_setup_task_logger.connect
def augment_celery_log(**kwargs):
    logger = logging.getLogger('imagebuilder')
    logfile = getfilename()
    handler = myFileHandler(logfile,'w')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
        
    if not logger.handlers:
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = 0

        logger.setLevel(logging.DEBUG)
    
@celery.task
def build(buildconfig, kickstart):

    logger = logging.getLogger('imagebuilder')
    logfile = getfilename()
    handler = myFileHandler(logfile,'w')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)    

    # replace the handler
    logger.handlers[0] = handler

    builder = ImageBuilder(json.loads(buildconfig), kickstart)

    # build task
    status = builder.build()

    # JSON dump of the log file
    logfile = builder.getlogfile()
    with open(logfile,'r') as f:
        logfile_str = json.dumps(f.read())

    return [status, logfile_str]
