# Image Builder: Facilitate Custom Image Building for Fedora
# Copyright (C) 2012  Tim Flink Amit Saha

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  
# 02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
#          http://fedoraproject.org/wiki/User:Amitksaha

import traceback
import sys
import tempfile
import time
import logging
import os

from image_builder.worker import Worker
from image_builder.transfer import Transfer
from image_builder.notification import Notification

""" Kickstarts the Image Building process.
"""
class ImageBuilder:
    # Read Image Build configuration

    def __init__(self, buildconfig, kickstart = None):

        self.buildconfig = buildconfig
        self.kickstart = kickstart
        self.iso_type = self.buildconfig['default']['type']
        self.staging = self.buildconfig['default']['staging']
        self.email = self.buildconfig['default']['email']
        self.logger = logging.getLogger('imagebuilder')

        self.logger.info('Registered a new Image Build request from {0:s}'.format(self.email))
        self.logger.info('Image type:: {0:s}'.format(self.iso_type))

        # if running in distributed mode, the logger
        # is initiated via tasks.py
        # the environment variable is set by the command line
        # client
        if not os.environ.has_key('LOCAL_MODE'):
            self.logfile = self.logger.handlers[0].getlogfile()
        # if running in local mode
        else:
            self.logfile = self.initlog()

        self.monitor = self.checkmonitor()
        self.notify_email_init()

    def initlog(self):
        """ Initiate the logging in local mode"""
        
        time_now = str(time.time()).split('.')
        logfile = tempfile.gettempdir() + '/imagebuild_{0:s}.log'.format(time_now[0]+time_now[1])
        handler = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        if not self.logger.handlers:
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.propagate = 0
            self.logger.setLevel(logging.DEBUG)
            self.logger.info('Registered a new Image Build request from {0:s}'.format(self.email))
            self.logger.info('Image type:: {0:s}'.format(self.iso_type))

        return logfile

    def getlogfile(self):
        """ Return the log file """

        return self.logfile

    def checkmonitor(self):
        ''' Check if build monitor is running '''

        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:                         
            s.connect(('localhost', 5100))
        except:
            return False
        else:
            return True

    def notify_email_init(self):
        ''' Send a notification email upon build initiation with
        the monitor access URL: <ip>:/log/tmp/imagebuild_xxx.log
        '''
        if os.environ.has_key('LOCAL_MODE'):
            if os.environ['LOCAL_MODE'] == '1':
                return

        message = 'Your Image Building Request have been submitted. '
        ipaddr = self.getip()

        if self.monitor:
            message = message + 'You may monitor the progress by going to '
            message = message + 'http://' + ipaddr + ':5100/log{0:s}. '.format(self.logfile)
            message = message + 'You will also recieve an email upon completion.'
        else:
            message = message + 'You will recieve an email upon completion.'
        
        recipient = self.email
        subject = 'Your Image Build Request'

        headers = ["From: " + 'Fedora Build Service',
                   "Subject: " + subject,
                   "To: " + recipient,
                   "MIME-Version: 1.0",
                   "Content-Type: text/html"]
        headers = "\r\n".join(headers)
            
        
        notify = Notification()
        notify.send_email(recipient, headers, message)

        return

    def notify_email_final(self):
        ''' Send a final notification email upon build completion '''

        if os.environ.has_key('LOCAL_MODE'):
            if os.environ['LOCAL_MODE'] == '1':
                return

        message = 'Your Image Building Request have been completed.'
        ipaddr = self.getip()
        message = '<p>The build was completed by worker:: {0:s}. Detailed log: '.format(ipaddr)

        with open(self.logfile) as f:
            for line in f:
                message = message + '<p>' + line

        recipient = self.email
        subject = 'Your Image Build Request'

        headers = ["From: " + 'Fedora Build Service',
                   "Subject: " + subject,
                   "To: " + recipient,
                   "MIME-Version: 1.0",
                   "Content-Type: text/html"]
        headers = "\r\n".join(headers)
            
        notify = Notification()
        notify.send_email(recipient, headers, message)

        return

    def getip(self):
        ''' Get the public facing IP address'''

        # Recipe: http://stackoverflow.com/a/166589/59634
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("gmail.com",80))
        ipaddr = s.getsockname()[0]
        s.close()

        return ipaddr
    
    def build(self):
        # Worker object
        worker = Worker(self.buildconfig)

        # boot
        if self.iso_type == 'boot':
            self.logger.info('Starting the Image Build Process')
            self.imgloc = worker.build_bootiso()

        # DVD
        if self.iso_type == 'dvd':
            self.logger.info('Starting the Image Build Process')
            self.imgloc = worker.build_dvd(self.kickstart)

        #Live image
        if self.iso_type == 'live':
            self.logger.info('Starting the Image Build Process')
            self.imgloc = worker.build_live(self.kickstart)
        
        self.logger.info('Image building process complete')

        #transfer image(s) and logs
        if self.imgloc:
            self.logger.info('Image successfully created. Transferring to staging.')

            t = Transfer(self.buildconfig, self.imgloc, self.logfile)
            status = t.transfer()

            if status == 0:
                self.logger.info('Image(s) and logs available at {0:s}'.format(self.staging))
                #build completion notification email
                self.notify_email_final()
                return 0 

            if status == -1:
                self.logger.info('Error in transfering image(s)/logs')
                dirname, temp = os.path.split(os.path.abspath(self.imgloc[0]))
                self.logger.info('Image(s) available in {0:s} on {1:s}'.format(dirname,os.uname()[1]))
                #build completion notification email
                self.notify_email_final()
                return -1
        else:
            self.logger.info('Error creating image. Transferring Logs.')
            t = Transfer(self.buildconfig, self.imgloc, self.logfile)
            status = t.transfer()

            if status == 0:
                self.logger.info('Logs available at {0:s}'.format(self.staging))
                #build completion notification email
                self.notify_email_final()
                return 0

            if status == -1:
                self.logger.info('Error in transfering logs to staging.')
                #build completion notification email
                self.notify_email_final()
                return -1
