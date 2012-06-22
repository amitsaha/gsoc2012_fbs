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

import ConfigParser
import subprocess
import koji
import yum
import sys
import os

from pykickstart.parser import KickstartParser
from pykickstart.version import makeVersion

from image_builder.repo_create import RepoCreate
from image_builder.bootiso import Bootiso

class Worker():
    """ Worker class is responsible for the actual creation
    of the images
    """

    def __init__(self, buildconfig):

        self.possible_arches = ['i686', 'x86_64']
        self.possible_products = ['fedora']
        self.possible_releases = ['17', '18','rawhide']
        self.imageconfig = buildconfig
        self.kojihub_url = 'http://koji.fedoraproject.org/kojihub'
        self.conn = koji.ClientSession(self.kojihub_url)

        return

    def add_repo(self, ksfile, siderepo):
        """ Add a repository to an existing KS file """

        # read
        ksparser = KickstartParser(makeVersion())
        ksparser.readKickstart(ksfile)
        
        #obtain the handler dump
        kshandlers = ksparser.handler

        # add a repository
        kshandlers.repo.repoList.extend(['repo --name="siderepo" --baseurl={0:s}\n'.format(siderepo)])

        # Write a new ks file
        outfile = open(ksfile, 'w')
        outfile.write(kshandlers.__str__())
        outfile.close()

        return

    def get_nvr(self, bids):
        """ get NVR given build ID """

        nvr = []
        for bid in bids:
            # get the build information for this bid
            build = self.conn.getBuild(int(bid))
            # NVR
            package = build['nvr']
            nvr.append(package)
    
        return nvr

    def prep_siderepo(self, workdir, packages, arch):
        """ prepare a side repository given extra packages """

        arch = [arch]
        arch.append('noarch')
        repodir = '{0:s}/siderepo'.format(workdir)
        repo_create = RepoCreate(repodir, arch)
        repo_create.make_repo(packages)

        repo_url = 'file://{0:s}'.format(repodir)
        return repo_url

    def gather_repos(self, release):
        """ Build repository list using data from the configuration
        file 
        """
        config = ConfigParser.SafeConfigParser()
        config.read(self.imageconfig)
        reponames = [ release ]
        updates = config.get('boot', 'updates')
        testing = config.get('boot', 'updates-testing')

        if updates == '1':
            reponames.append('{0:s}-updates'.format(release))
        if testing == '1':
            reponames.append('{0:s}-updates-testing'.format(release))

        repos = []
        mirrors = []
        for name in reponames:
            # repos
            repos.append(config.get('boot', '{0:s}_url'.format(name)))
            # mirrorlist
            mirrors.append(config.get('boot', '{0:s}_mirror'.format(name)))

        return repos, mirrors

    
    def build_bootiso(self):
        """ Build boot iso """

        # Read pungi configuration
        config = ConfigParser.SafeConfigParser()
        config.read(self.imageconfig)

        arch = config.get('DEFAULT', 'arch')
        outdir = config.get('boot', 'outdir')
        workdir = config.get('boot', 'workdir')
        product = config.get('boot', 'product')
        release = config.get('boot', 'release')
        version = config.get('boot', 'version')
        proxy = config.get('boot', 'proxy')
    
        if proxy == '':
            proxy = None

        if not arch in self.possible_arches:
            print "ISOs for arch {0:s} are not supported".format(arch)
            sys.exit(1)

        if not product in self.possible_products:
            print "Product {0:s} is not supported".format(product)

        if not release in self.possible_releases:
            print "Release {0:s} is not supported".format(release)
            sys.exit(1)

        # gather repos and mirrors
        repos, mirrors = self.gather_repos(release)

        # Create the side repository if needed
        nvr = config.get('boot', 'nvr')
        bid = config.get('boot', 'bid')

        rpms_nvr = []
        if nvr:
            for rpm in nvr.split(';'):
                rpms_nvr.append(rpm)

        bids = []        
        if bid:
            for rpm in bid.split(';'):
                bids.extend(str(rpm))
            
            rpms_bid = self.get_nvr(bids, arch)
            rpms_nvr.extend(rpms_bid)
    
        # prepare side repository
        rpms = rpms_nvr

        if rpms:
            siderepo = self.prep_siderepo(workdir, rpms, arch)
            repos.append(siderepo)

        boot_builder = Bootiso(arch, release, version, repos, mirrors, proxy, outdir, product)
        boot_builder.make_iso()

        # boot image location
        imgloc = [os.path.abspath(outdir)+'/images/boot.iso']

        return imgloc
    
    def build_dvd(self):
        """ Builds DVD image """

        config = ConfigParser.SafeConfigParser()
        config.read(self.imageconfig)

        args = []

        name = config.get('dvd', 'name')    
        args.extend(['--name', name])

        ver = config.get('dvd', 'version')    
        args.extend(['--ver', ver])

        flavor = config.get('dvd', 'flavor')    
        args.extend(['--flavor', flavor])

        destdir = config.get('dvd', 'destdir')    
        args.extend(['--destdir', destdir])
    
        cachedir = config.get('dvd', 'cachedir')    
        args.extend(['--cachedir',  cachedir])

        bugurl = config.get('dvd', 'bugurl') 
        args.extend(['--bugurl',  bugurl])

        nosource = config.get('dvd', 'nosource')
        if nosource == '1':
            args.extend(['--nosource'])
    
        sourceisos = config.get('dvd', 'sourceisos')
        if sourceisos == '1':
            args.extend(['--sourceisos'])

        force = config.get('dvd','force')
        if force == '1':
            args.extend(['--force'])

        stage = config.get('dvd', 'stage')
        allowed_stages = ['all', '-G', '-C', '-B', '-I']

        if stage in allowed_stages:
            if stage == 'all':
                args.extend(['--all-stages'])
            else:
                args.extend([stage])
        else:
            print 'Invalid stage entered'
                        
        ks = config.get('dvd', 'config')
        args.extend(['-c', ks])

        # Create the side repository if needed
        nvr = config.get('dvd', 'nvr')
        bid = config.get('dvd', 'bid')

        arch = config.get('DEFAULT', 'arch')
        workdir = config.get('dvd', 'workdir')
    
        rpms_nvr = []
        if nvr:
            for rpm in nvr.split(';'):
                rpms_nvr.append(rpm)

        bids = []
        if bid:
            for rpm in bid.split(';'):
                bids.extend(str(rpm))
    
            if bids:
                rpms_bid = self.get_nvr(bids, arch)
                rpms_nvr.extend(rpms_bid)
    
        # prepare side repository
        rpms = rpms_nvr
        if len(rpms) > 0:
            siderepo = self.prep_siderepo(workdir, rpms, arch)
            # Add side repo to the existing KS file
            self.add_repo(ks, siderepo)
    
        # fire pungi
        process_call = ['pungi']
        process_call.extend(args)
        subprocess.call(process_call)

        # DVD image and other files location
        if arch == 'i686':
            arch = 'i386'

        # for DVD iso
        imgloc = ['{0:s}/{1:s}/{2:s}/{3:s}/iso/{4:s}-{1:s}-{3:s}-DVD.iso'.format(os.path.abspath(destdir), ver, flavor, arch, name)]
        # for Netinstall ISO
        imgloc.extend(['{0:s}/{1:s}/{2:s}/{3:s}/iso/{4:s}-{1:s}-{3:s}-netinst.iso'.format(os.path.abspath(destdir), ver, flavor, arch, name)])
        # for checksum
        imgloc.extend(['{0:s}/{1:s}/{2:s}/{3:s}/iso/{4:s}-{1:s}-{3:s}-CHECKSUM'.format(os.path.abspath(destdir), ver, flavor, arch, name)])

        return imgloc

    def build_live(self):
        """ Live Image"""

        # Currently using livecd-creator
        # as the forward moving livemedia-creator is not yet
        # quite usable

        # Read pungi configuration
        config = ConfigParser.SafeConfigParser()
        config.read(self.imageconfig)

        args = []

        ks = config.get('live', 'config')
        args.extend(['-c', ks])

        label = config.get('live', 'label')
        args.extend(['-f', label])

        title = config.get('live','title')
        args.extend(['--title', title])
    
        product = config.get('live', 'product')
        args.extend(['--product', product])
    
        releasever = config.get('live', 'releasever')
        args.extend(['--releasever', releasever])
        
        arch = config.get('live', 'arch')
        yb = yum.YumBase()
    
        if arch != yb.arch.canonarch:
            print 'Live image arch should be the same as the build arch'
            sys.exit(1)
    
        tmpdir = config.get('live', 'tmpdir')
        args.extend(['-t', tmpdir])

        cachedir = config.get('live', 'cachedir')
        args.extend(['--cache', cachedir])

        logfile = config.get('live', 'logfile')
        args.extend(['--logfile', logfile])

        # Create the side repository if needed
        nvr = config.get('live', 'nvr')
        bid = config.get('live', 'bid')

        rpms_nvr = []
        if nvr != '':
            for rpm in nvr.split(';'):
                rpms_nvr.append(rpm)

        bids = []
        if bid:
            for rpm in bid.split(';'):
                bids.extend(str(rpm))
    
        if bids:
            rpms_bid = self.get_nvr(bids)
            rpms_nvr.extend(rpms_bid)
    
        # prepare side repository
        rpms = rpms_nvr
        arch = config.get('DEFAULT', 'arch')
        tmpdir = config.get('live', 'tmpdir')

        if rpms:
            siderepo = self.prep_siderepo(tmpdir, rpms, arch)
            # Add side repo to the existing KS file
            self.add_repo(ks, siderepo)
    
        # fire livecd-creator
        process_call = ['livecd-creator']
        process_call.extend(args)
        subprocess.call(process_call)

        # live image location
        imgloc = ['{0:s}.iso'.format(label)]

        return imgloc
