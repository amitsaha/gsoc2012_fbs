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
Uses Celery for task distribution.
See HOWTO for setup and usage instructions.
"""
import json
import ConfigParser
import os
import sys
import time

from image_builder.util import Utilities

class Cli:

    def __init__(self, config):
        self.config = config

    def build(self):

        util = Utilities()

        buildconfig = util.get_dict(self.config)

        arch = buildconfig['default']['arch']
        #find an appropriate build node from nodes.conf
        #based on the arch
        config = ConfigParser.SafeConfigParser()
        config.read('nodes.conf')
        broker_url = config.get(arch,'broker_url')

        #now create the celeryconfig.py using this broker_url
        with open('celeryconfig.py','w') as f:
            f.write('BROKER_URL = {0:s}\n'.format(broker_url))
            f.write('CELERY_RESULT_BACKEND = "amqp"\n')
            f.write('\n')
    
        buildconfig_json = json.dumps(buildconfig)
        ksstr = util.get_kickstart(buildconfig)

        # task delegation
        from tasks import build

        try:
            result_obj = build.apply_async(args = [buildconfig_json, ksstr], serializer="json")
        except Exception as e:
            sys.exit('Error in communicating with Celery')
        else:
            result = result_obj.get()

        return result

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Must provide the path to the config file as the argument'
        sys.exit(1)
    
    cli = Cli(sys.argv[1])
    result = cli.build()

    status = result[0]

    if status == 0:
        print 'Image built and transferred successfully'

    if status == -1:
        print 'Image could not be built/tansferred successfully'

    logfile = result[1]
    with open('imagebuilder.log','w') as f:
        f.write(json.loads(logfile))

    print 'See imagebuilder.log for details'
