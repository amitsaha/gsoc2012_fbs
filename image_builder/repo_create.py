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
# 	 http://fedoraproject.org/wiki/User:Amitksaha

import os
import koji
import urllib
import subprocess

class RepoCreate(object):
    """ Create side repository with additional packages """

    def __init__(self, repodir,arch):
        self.repodir = repodir
        self.arch = arch
        self.koji_connection = self.get_koji_connection()
        self.kojiurl = 'http://koji.fedoraproject.org/kojihub'
        self.pkgurl = 'http://koji.fedoraproject.org/packages'

    def get_koji_connection(self):
        """ Return a Connection to Koji hub """
        return koji.ClientSession(self.kojiurl)

    def make_repo(self, packages):
        """ Create the side repository after downloading
        the extra packages 
        """
        self.prep_repo_dir()
        self.download_packages(packages)
        self.make_repo_metadata()

    def prep_repo_dir(self):
        if not os.path.exists(self.repodir):
            os.makedirs(self.repodir)

    def make_repo_metadata(self):
        subprocess.call(['createrepo', self.repodir])

    def download_packages(self, packages):
        """ Download the packages """
        rpms = []

        for package in packages:
            rpms.extend(self.get_rpm_urls(package))
        
        for rpm in rpms:
            filename = '/'.join([self.repodir, rpm['url'].split('/')[-1]])
            urllib.urlretrieve(rpm['url'], filename)

    def get_build(self, nvr):
        return self.koji_connection.getBuild(nvr)

    def get_rpms(self, build_id):
        rpms = self.koji_connection.listRPMs(build_id)
        return filter(lambda r: not r['name'].endswith('-debuginfo') and r['arch'] in self.arch, rpms)

    def get_rpm_urls(self, nvr):
        """ Get the download URLs of the RPMs from 
        NVR string
        """

        # get build info
        build = self.get_build(nvr)
        pkg_name = build['package_name']

        # list rpms per build
        rpms = self.get_rpms(build['id'])
        
        # generate list of urls
        for rpm in rpms:
            baseurl = '/'.join((self.pkgurl, pkg_name,  build['version'],
                            build['release']))
            rpm['url'] = "%s/%s" % (baseurl, koji.pathinfo.rpm(rpm))
            
        return rpms
