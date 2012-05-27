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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
#          http://fedoraproject.org/wiki/User:Amitksaha

import sys
import os
import subprocess
import ConfigParser

from image_builder.worker import Worker



class ImageBuild():

    def __init__(self):

        self.build_config='/etc/imagebuild/imagebuild.conf'
        self.possible_types = ['boot','dvd','live']

        # Read configuration
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(self.build_config)

        self.iso_type=self.config.get('DEFAULT','type')
        self.staging=self.config.get('DEFAULT','staging')
        self.email=self.config.get('DEFAULT','email')

        if not self.iso_type in self.possible_types:
            print 'ISOs of type {0:s} are not supported'.format(iso_type)
            sys.exit(1)

        # boot
        if self.iso_type == 'boot':
            print 'Building Boot ISO'
            worker=Worker()
            self.imgloc=worker.build_bootiso()
            self.transfer()

        # DVD
        if self.iso_type == 'dvd':
            print'Building DVD'
            worker=Worker()
            self.imgloc=worker.build_dvd()
            self.transfer()
        
        #Live image
        if self.iso_type == 'live':
            print 'Building Live Image'
            worker=Worker()
            self.imgloc=worker.build_live()
            self.transfer()

        
    #transfer to staging
    # uses SCP
    # use a Python module?
    # such as http://www.lag.net/paramiko/
    def transfer(self):

        for img in self.imgloc:
            args=[img,self.staging]

            # setup 'scp' and fire
            process_call = ['scp']
            process_call.extend(args)

            print 'Transfering {0:s} to {1:s}'.format(img,self.staging)
            subprocess.call(process_call)   

        return


    # email notification
    # TBD
