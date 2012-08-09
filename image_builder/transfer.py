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

import os
import logging
import subprocess
import time

class Transfer:
    """ Image transfer module """
    def __init__(self, buildconfig, imgloc, logfile):
        self.buildconfig = buildconfig
        self.staging = buildconfig['default']['staging']
        self.imgloc = imgloc
        self.logfile = logfile
        self.logger = logging.getLogger('imagebuilder')

    def transfer_local(self, staging):
        ''' Local file system copy '''

        if not os.path.exists(os.path.abspath(staging)):
            os.mkdir(os.path.abspath(staging))
            
        if self.imgloc:
            self.logger.info('Initiating local transfer of image(s) to {0:s}'.format(staging))
            for img in self.imgloc:
                subprocess.call(['cp', img, os.path.abspath(staging)+"/"])

        # transfer the log
        self.logger.info('Initiating local transfer of logs to {0:s}'.format(staging))
        subprocess.call(['cp', self.logfile, os.path.abspath(staging)+"/"])

        #live-cd creator's log file
        if self.buildconfig['default']['type'] == 'live':
            if self.buildconfig['live'].has_key('logfile'):
                live_log = self.buildconfig['live']['logfile']
                if os.path.exists(live_log):
                    subprocess.call(['cp', live_log, os.path.abspath(staging)+"/"])
        
        return 0
    
    def transfer_ftp(self):
        """ FTP image transfer """
        from ftplib import FTP
        try:
            ftp = FTP(self.staging)
        except Exception as e:
            self.logger.error('Connection to FTP server refused')
            return -1

        # anonymous
        try:
            ftp.login()
        except Exception as e:
            self.logger.error('Error logging into the FTP server. Check connectivity/anonymous login.')
            ftp.close()
            return -1
        else:                          
            # assumes a 'pub' directory where the files are to be 
            # put
            try:
                ftp.cwd('pub')
            except Exception as e:
                self.logger.error('No pub/ sub-dir found on FTP server')
                return -1
            
            # transfer the files
            if self.imgloc:
                self.logger.info('Initiating FTP transfer of image(s)')
                for img in self.imgloc:
                    self.logger.info('Copying {0:s}'.format(img))
                    with open(img) as f:
                        # extract the filename from 'img'
                        head, fname = os.path.split(img)
                        time_now = str(time.time()).split('.')
                        # get a filename of the form imgname_timestamp.<ext>
                        if len(fname.split('.')) == 2:
                            fname = fname.split('.')[0] + '-{0:s}'.format(self.buildconfig['default']['arch']) + '-{0:s}.'.format(time_now[0]+time_now[1]) + fname.split('.')[1]
                        # if no extension of the file (such as CHECKSUM)
                        else:
                            fname = fname.split('.')[0] + '-{0:s}'.format(self.buildconfig['default']['arch']) + '-{0:s}.'.format(time_now[0]+time_now[1])
                            
                        try:
                            ftp.storbinary('STOR {0:s}'.format(fname), f)
                        except Exception as e:
                            self.logger.error('Could not store file on remote server')
                            return -1
                    
            # transfer the log
            self.logger.info('Initiating FTP transfer of logs')

            # image builder log file
            with open(self.logfile) as f:
                # extract the filename from logfile
                head, fname = os.path.split(self.logfile)
                self.logger.info('Copying {0:s}'.format(fname))
                try:
                    ftp.storbinary('STOR {0:s}'.format(fname), f)
                except Exception as e:
                    self.logger.error('Could not store file on remote server')
                    return -1

            #live-cd creator's log file
            if self.buildconfig['default']['type'] == 'live':
                if self.buildconfig['live'].has_key('logfile'):
                    live_log = self.buildconfig['live']['logfile']
                    with open(live_log) as f:
                        # extract the filename from logfile
                        head, fname = os.path.split(live_log)
                        self.logger.info('Copying {0:s}'.format(fname))
                        try:
                            ftp.storbinary('STOR {0:s}'.format(fname), f)
                        except Exception as e:
                            self.logger.error('Could not store file on remote server')
                            return -1
                        
            ftp.close()
            return 0

    def transfer(self):
        if self.staging.startswith('file:///'):
            # bad hack to remove the prefix file:///
            status = self.transfer_local(self.staging.split('//')[1])
        else:
            status = self.transfer_ftp()

        return status
