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

from worker import Worker
from transfer import Transfer

build_config='/etc/imagebuild/imagebuild.conf'
possible_types = ['boot','dvd','live']

# Read configuration
config = ConfigParser.SafeConfigParser()
config.read(build_config)

iso_type=config.get('DEFAULT','type')
staging=config.get('DEFAULT','staging')
email=config.get('DEFAULT','email')

if not iso_type in possible_types:
    print 'ISOs of type {0:s} are not supported'.format(iso_type)
    sys.exit(1)

    # boot
if iso_type == 'boot':
    print 'Building Boot ISO'
    worker=Worker(build_config)
    imgloc=worker.build_bootiso()
    t=Transfer(staging,imgloc)
    t.transfer_ftp()
        
    # DVD
if iso_type == 'dvd':
    print'Building DVD'
    worker=Worker(build_config)
    imgloc=worker.build_dvd()
    t=Transfer(staging,imgloc)
    t.transfer_ftp()
        
    #Live image
if iso_type == 'live':
    print 'Building Live Image'
    worker=Worker(build_config)
    imgloc=worker.build_live()
    t=Transfer(staging,imgloc)
    t.transfer_ftp()
    
