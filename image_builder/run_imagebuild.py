#!/usr/bin/python
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

import os
import glob
import shutil

from imagebuild import ImageBuild

def main():
    
    #copy the config files
    #to /etc/imagebuild/
    
    if not os.path.exists('/etc/imagebuild'):
        os.makedirs('/etc/imagebuild')

    #copy the .conf files
    for config in glob.glob( os.path.join('config', '*.conf') ):
        shutil.copy2(config,'/etc/imagebuild')

    #copy the kickstart files
    for ks in glob.glob( os.path.join('kickstarts', '*.ks') ):
        shutil.copy2(ks,'/etc/imagebuild')

    # Build and Transfer
    imagebuild = ImageBuild()

if __name__=='__main__':
    main()
