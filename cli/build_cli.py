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
See HOWTO for setup and usage instructions.
"""

from tasks import build

import json
import ConfigParser
import os
import sys

CONFIG_FILE = 'imagebuild.conf'

def build_cli():
    config = ConfigParser.SafeConfigParser()
    config.read(CONFIG_FILE)
    arch = config.get('DEFAULT','arch')
    
    config = ConfigParser.SafeConfigParser()
    config.read('nodes.conf')
    broker_url = config.get(arch,'broker_url')

    with open('celeryconfig.py','w') as f:
        f.write('BROKER_URL = {0:s}\n'.format(broker_url))
        f.write('CELERY_RESULT_BACKEND = "amqp"\n')
    
    buildconf = open(CONFIG_FILE)
    buildconf_str = json.dumps(buildconf.read())
    buildconf.close()
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)

    if config.has_section('dvd'):
        ks = config.get('dvd','config')
    else:
        if config.has_section('live'):
            ks = config.get('live','config')
        else:
            ks = None

    if ks:
        # if its a remote KS file
        if ks.startswith(('http','ftp')):
            # download and then JSON dump
            import urllib2
            ksstr = json.dumps(urllib2.urlopen(ks).read())
            head, ks_fname = os.path.split(ks)
        else:
            with open(ks) as ks_fp:
                ksstr = json.dumps(ks_fp.read())
            head, ks_fname = os.path.split(ks)

        #send task to celery woker(s)
        build.apply_async(args=[buildconf_str,[ks_fname,ksstr]],serializer="json")
    else:
        build.apply_async(args=[buildconf_str,None],serializer="json")

    print 'Build task submitted'
    
    return

if __name__ == '__main__':
    if not os.path.exists(CONFIG_FILE):
        print 'You should have a configuration file at {0:s}. Exiting'.format(CONFIG_FILE)
        sys.exit(1)
    else:
        build_cli()
    

