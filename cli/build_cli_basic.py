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

""" Command line interface to the image building code.
Does not use Celery and hence has minimum setup requirements.
Simply install the image_builder package and use away.

"""
import ConfigParser
import sys
import os
import json
import glob
import shutil

# for local building mode
os.environ['LOCAL_MODE'] = '1'

from image_builder.imagebuilder import ImageBuilder
from image_builder.util import Utilities

class CliBasic:

    def __init__(self, buildconfig):
        self.buildconfig = buildconfig
        
    def build(self):

        util = Utilities()

        buildconfig = util.get_dict(self.buildconfig)
        isotype = buildconfig['default']['type']

        if isotype != 'boot':
            ksstr = util.get_kickstart(buildconfig)
            #copy all KS files in the specified directory 
            #of the KS file to /tmp
            dirname, fname = os.path.split(os.path.abspath(buildconfig[isotype]['config']))
            for ksfile in glob.glob('{0:s}/*.ks'.format(os.path.abspath(dirname))):
                shutil.copyfile(ksfile,'/tmp/{0:s}'.format(os.path.split(ksfile)[1]))
        else:
            ksstr = None

        build = ImageBuilder(buildconfig, ksstr)
        logfile = build.getlogfile()

        print 'Initiating Build Process. See {0:s} for progress'.format(logfile)

        status = build.build()

        return status

if __name__ == '__main__':

    if not os.geteuid() == 0:
        sys.exit('Script must be run as root')
    
    if len(sys.argv) == 1:
        print 'Must provide the path to the config file as the argument'
        sys.exit(1)

    clibasic = CliBasic(sys.argv[1])
    status = clibasic.build()

    print 'Build process complete.'
