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

import tempfile
import pylorax
import os
import ConfigParser
import yum
import shutil
import sys
import logging
import subprocess

class Bootiso():
    """ Create Boot ISO via lorax """

    def __init__(self, arch, release, version, repos, mirrors, proxy, outputdir, product):
        self.arch = arch
        self.release = release
        self.version = version
        self.repos = repos
        self.mirrors = mirrors
        self.proxy = proxy
        self.outputdir = outputdir
        self.product = product
        self.logger = logging.getLogger('imagebuilder')

    def get_yum_base_object(self, installroot, repositories, mirrors, proxy, tempdir="/tmp"):
        """ with help from  
        http://git.fedorahosted.org/git/?p=lorax.git;a=blob_plain;f=src/sbin/lorax;hb=HEAD
        """

        def sanitize_repo(repo):
            if repo.startswith("/"):
                return "file://{0}".format(repo)
            elif (repo.startswith("http://") or repo.startswith("https://")
                  or repo.startswith("ftp://") or repo.startswith("file://")):
                return repo
            else:
                return None

        # sanitize the repositories
        repositories = map(sanitize_repo, repositories)
        mirrors = map(sanitize_repo, mirrors)
        
        # remove invalid repositories
        repositories = filter(bool, repositories)
        mirrors = filter(bool, mirrors)

        cachedir = os.path.join(tempdir, "yum.cache")
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)

        yumconf = os.path.join(tempdir, "yum.conf")
        c = ConfigParser.ConfigParser()

        # add the main section
        section = "main"
        data = {"cachedir": cachedir,
                "keepcache": 0,
                "gpgcheck": 0,
                "plugins": 0,
                "reposdir": "",
                "tsflags": "nodocs"}

        if proxy:
            data["proxy"] = proxy

        # if excludepkgs:
        #     data["exclude"] = " ".join(excludepkgs)

        c.add_section(section)
        map(lambda (key, value): c.set(section, key, value), data.items())

        # add the main repository
        section = "lorax-repo"
        data = {"name": "lorax repo",
                "#baseurl": repositories[0],
                "mirrorlist": mirrors[0],
                "enabled": 1}

        c.add_section(section)
        map(lambda (key, value): c.set(section, key, value), data.items())

        # append a blank mirror so as to account for the side repository
        mirrors.append('')

        # add the extra repositories and mirrors
        for n, (repo, mirror) in enumerate(zip(repositories[1:], mirrors[1:])):
            section = "lorax-extra-repo-{0:d}".format(n)
            # side repo
            if n == len(mirrors)-2:
                data = {"name": "lorax extra repo {0:d}".format(n),
                        "baseurl": repo,
                        "enabled": 1}
            # other repos
            else:
                data = {"name": "lorax extra repo {0:d}".format(n),
                        "mirrorlist":mirror,
                        "#baseurl": repo,
                        "enabled": 1}

            c.add_section(section)
            map(lambda (key, value): c.set(section, key, value), data.items())

        # write the yum configuration file
        with open(yumconf, "w") as f:
            c.write(f)

        # create the yum base object
        yb = yum.YumBase()
        yb.preconf.fn = yumconf
        yb.preconf.root = installroot
    #yb.repos.setCacheDir(cachedir)

        return yb

    def make_iso(self):
        """ Create yum base object and fire the ISO build 
        process
        """
        # create the temporary directory for lorax
        tempdir = tempfile.mkdtemp(prefix="lorax.", dir=tempfile.gettempdir())

        # create the yumbase object
        installtree = os.path.join(tempdir, "installtree")
        os.mkdir(installtree)
        yumtempdir = os.path.join(tempdir, "yum")
        os.mkdir(yumtempdir)

        yb = self.get_yum_base_object(installtree, self.repos, self.mirrors, self.proxy, yumtempdir)        
        if yb is None:
            self.logger.error('Unable to create the yumbase object for creating boot ISO')
            shutil.rmtree(tempdir)
            raise Exception 

        lorax = pylorax.Lorax()
        # uses the default configuration file
        lorax.configure()
        #fire
        self.logger.info('All set. Spawning boot iso creation using lorax.')
        #lorax.run(yb, self.product, self.version, self.release, None, None, False, tempdir, self.outputdir, self.arch, None, False)

        # spawn lorax using subprocess.check_call
        # lorax.run() seems to cause some unexplained 
        # problems with celery
        args=[]

        args.extend(['-p',self.product])
        args.extend(['-v',self.version])
        args.extend(['-r',self.release])
        
        for repo in self.repos:
            args.extend(['-s',repo])

        args.extend([self.outputdir])

        for mirror in self.mirrors:
            args.extend(['-m',mirror])

        args.extend(['--buildarch=',self.arch])
        
        process_call = ['lorax']
        process_call.extend(args)

        subprocess.check_call(process_call)
