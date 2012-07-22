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

""" Utility functions for the Command line clients

"""
import json
import os
import ConfigParser

class Utilities:
    
    def get_dict(self, buildconfig):
        # Get the dictionary dump from the config file

        config = ConfigParser.SafeConfigParser()
        config.read(buildconfig)
    
        sections_dict = {}

        # get all defaults
        defaults = config.defaults()
        temp_dict = {}
        for key in defaults.iterkeys():
            temp_dict[key] = defaults[key]

        sections_dict['default'] = temp_dict

        # get sections and iterate over each
        sections = config.sections()
        
        for section in sections:
            options = config.options(section)
            temp_dict = {}
            for option in options:
                temp_dict[option] = config.get(section,option)
            
            sections_dict[section] = temp_dict

        return sections_dict
    
    def get_kickstart(self, buildconfig):

        # retrieve the kickstart file name if any    
        if buildconfig.has_key('dvd'):
            if not buildconfig['dvd']['config'].startswith(('http', 'https', 'ftp')):
                head, ks_fname = os.path.split(buildconfig['dvd']['config'])
            else:
                ks_fname = buildconfig['dvd']['config']
        else:
            if buildconfig.has_key('live'):
                if not buildconfig['live']['config'].startswith(('http', 'https', 'ftp')):
                    head, ks_fname = os.path.split(buildconfig['live']['config'])
                else:
                    ks_fname = buildconfig['live']['config']
            else:
                ks_fname = None

        if ks_fname:
            # if its a remote KS file
            if ks_fname.startswith(('http', 'https', 'ftp')):
                # download and then JSON dump
                import urllib2
                try:
                    print 'Reading remote KS file'
                    ksstr = json.dumps(urllib2.urlopen(ks_fname).read())
                except Exception as e:
                    print 'Error retrieving remote KS file'
                    ksstr = None
            else:
                try:
                    print 'Reading KS file'
                    with open(ks_fname) as ks:
                        ksstr = json.dumps(ks.read())
                except Exception as e:
                    ksstr = None
                    print 'Error reading specified KS file'
        else:
            ksstr = None

        return ksstr
