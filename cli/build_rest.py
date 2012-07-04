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

""" Simple client to access the Build Service via the Rest API
at /rest. See HOWTO for setup and usage instructions.
"""

# Uses requests library
# http://docs.python-requests.org/en/latest/
import requests 

import ConfigParser
import json
import os

# Set these appropriately
CONFIG_FILE = 'imagebuild_boot.conf'
API_URL = 'http://127.0.0.1:5000/rest'

def build_rest():
    
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
            ks_fname = None
            ksstr = None

    if ks:
        if not ks.startswith(('http','ftp')):
            with open(ks) as ks_fp:
                ksstr = json.dumps(ks_fp.read())
            head, ks_fname = os.path.split(ks)
        else:
            ks_fname = ks
            ksstr = []

    # build and send POST request (as JSON)
    headers = {'Content-Type': 'application/json'}
    payload={'config':buildconf_str, 'ksfname':ks_fname, 'ks':ksstr}
    r = requests.post(API_URL, data = json.dumps(payload), headers = headers)
    print r.json

if __name__=='__main__':

    if not os.path.exists(CONFIG_FILE):
        print 'You should have a configuration file at {0:s}. Exiting'.format(CONFIG_FILE)
        sys.exit(1)
    else:
        build_rest()
