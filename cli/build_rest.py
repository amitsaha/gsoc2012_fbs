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
at /rest. See docs for setup and usage instructions.
"""


import ConfigParser
import json
import os
import sys

try:
    import requests 
except ImportError, e:
    print 'The client uses the Requests library (http://docs.python-requests.org/en/latest/index.html'
    sys.exit(1)
    


class RestCli:

    def __init__(self, config, endpoint):
        self.config = config
        self.endpoint = endpoint

    def build_rest(self):
        
        with open(self.config) as buildconf:
            buildconf_str = json.dumps(buildconf.read())

        config = ConfigParser.RawConfigParser()
        config.read(self.config)

        if config.has_section('dvd'):
            ks_fname = config.get('dvd','config')
        else:
            if config.has_section('live'):
                ks_fname = config.get('live','config')
            else:
                ks_fname = None

        if ks_fname:
            # if its a remote KS file
            if ks_fname.startswith(('http', 'https', 'ftp')):
                # download and then JSON dump
                import urllib2
                try:
                    ksstr = json.dumps(urllib2.urlopen(ks_fname).read())
                except Exception as e:
                    ksstr = None
            else:
                try:
                    with open(os.path.abspath(ks_fname)) as ks:
                        ksstr = json.dumps(ks.read())
                except Exception as e:
                    ksstr = None
        else:
            ksstr = None

        # build and send POST request (as JSON)
        headers = {'Content-Type': 'application/json'}
        payload={'config':buildconf_str, 'ksfname':ks_fname, 'ks':ksstr}
        r = requests.post(API_URL, data = json.dumps(payload), headers = headers)
        print r.json

if __name__=='__main__':

    # change this to suit your needs

    API_URL = 'http://127.0.0.1:5000/rest'

    if len(sys.argv) == 1:
        print 'Must provide the path to the config file as the argument'
        sys.exit(1)


    cli = RestCli(sys.argv[1], API_URL)
    cli.build_rest()
