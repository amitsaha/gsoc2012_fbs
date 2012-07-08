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

from image_builder.worker import Worker
from image_builder.transfer import Transfer

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

    def build(self):

        # Worker object
        worker = Worker(self.buildconfig)

        # boot
        if self.iso_type == 'boot':
            self.imgloc = worker.build_bootiso()

        # DVD
        if self.iso_type == 'dvd':
            self.imgloc = worker.build_dvd(self.kickstart)

        #Live image
        if self.iso_type == 'live':
            self.imgloc = worker.build_live(self.kickstart)

        #transfer
        if self.imgloc:    
            t = Transfer(self.staging, self.imgloc)
            try:
                t.transfer_ftp()
            except Exception as e:
                print traceback.format_exception(*sys.exc_info())
                return -1
            else:
                return 0
        else:
            return -1
