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

import ConfigParser

from image_builder.worker import Worker
from image_builder.transfer import Transfer

""" Kickstarts the Image Building process.
"""
class ImageBuilder:
    # Read Image Build configuration

    def __init__(self):
        self.build_config = '/etc/imagebuild/imagebuild.conf'
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(self.build_config)
        self.iso_type = self.config.get('DEFAULT', 'type')
        self.staging = self.config.get('DEFAULT', 'staging')
        self.email = self.config.get('DEFAULT', 'email')

    def build(self):
        
        # Worker object
        worker = Worker(self.build_config)

        # boot
        if self.iso_type == 'boot':
            self.imgloc = worker.build_bootiso()
        # DVD
        if self.iso_type == 'dvd':
            self.imgloc = worker.build_dvd()

        #Live image
        if self.iso_type == 'live':
            self.imgloc = worker.build_live()

        t = Transfer(self.staging, self.imgloc)
        t.transfer_ftp()
