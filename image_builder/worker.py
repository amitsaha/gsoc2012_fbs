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

import subprocess
import koji
import yum
import sys
import os
import shutil
import tempfile
import traceback
import json
import platform
import logging

from pykickstart.parser import KickstartParser
from pykickstart.version import makeVersion

from image_builder.repo_create import RepoCreate
from image_builder.bootiso import Bootiso

class Worker():
    """ Worker class is responsible for the actual creation
    of the images
    """

    def __init__(self, buildconfig):
        self.buildconfig = buildconfig
        self.kojihub_url = 'http://koji.fedoraproject.org/kojihub'
        self.logger = logging.getLogger('imagebuilder')
        
    def get_koji_connection(self):
        """ Return a Connection to Koji hub """
        koji_conn = koji.ClientSession(self.kojihub_url)
        return koji_conn

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
        
        try:
            self.koji_conn = self.get_koji_connection()
        except Exception as e:
            self.logger.error('Error connecting to Koji hub')
            return None
        
        for bid in bids:
            # get the build information for this bid
            try:
                build = self.koji_conn.getBuild(int(bid))
            except Exception as e:
                self.logger.error('Error getting build information for package with Build ID {0:s}'.format(bid))
                return None
            else:
                # NVR
                package = build['nvr']
                nvr.append(package)
        
        return nvr

    def get_rpms_nvr(self, nvr, bid):
        """ Take the NVRs and BIDs and return the list
        of all NVR's

        """
        rpms_nvr = []
        arch = self.buildconfig['default']['arch']

        if nvr:
            for rpm in nvr.split(';'):
                rpms_nvr.append(rpm)

        bids = []        
        if bid:
            for rpm in bid.split(';'):
                bids.append(rpm)
            
            rpms_bid = self.get_nvr(bids)
            if rpms_bid:
                rpms_nvr.extend(rpms_bid)
            else:
                return None
    
        return rpms_nvr

    def prep_siderepo(self, workdir, packages, arch):
        """ prepare a side repository given extra packages """

        arch = [arch]
        arch.append('noarch')
        repodir = '{0:s}/siderepo'.format(workdir)
        repo_create = RepoCreate(repodir, arch)

        try:
            repo_create.make_repo(packages)
        except Exception as e:
            self.logger.error('Error creating side repository')
            self.logger.error(traceback.format_exception(*sys.exc_info()))
            repo_url = None
        else:
            repo_url = 'file://{0:s}'.format(repodir)
        return repo_url

    def gather_repos(self, release):
        """ Build repository list using data from the configuration
        file 
        """
        reponames = [ release ]
        updates = self.buildconfig['boot']['updates']
        testing = self.buildconfig['boot']['updates-testing']

        if updates == '1':
            reponames.append('{0:s}-updates'.format(release))
        if testing == '1':
            reponames.append('{0:s}-updates-testing'.format(release))

        repos = []
        mirrors = []
        for name in reponames:
            # repos
            repos.append(self.buildconfig['boot']['{0:s}_url'.format(name)])
            # mirrorlist
            mirrors.append(self.buildconfig['boot']['{0:s}_mirror'.format(name)])

        return repos, mirrors

    def build_bootiso(self):
        """ Build boot iso """

        arch = self.buildconfig['default']['arch']
        if arch != platform.machine():
            self.logger.info('Boot image arch requested should be the same as the build arch')
            return None

        outdir = self.buildconfig['boot']['outdir']
        workdir = self.buildconfig['boot']['workdir']
        product = self.buildconfig['boot']['product']
        release = self.buildconfig['boot']['release']
        version = self.buildconfig['boot']['version']
        proxy = self.buildconfig['boot']['proxy']
        
        #checks
        if proxy == '':
            proxy = None

        if os.path.exists(workdir):
            shutil.rmtree(workdir)
            os.mkdir(workdir)

        if os.path.exists(outdir):
            shutil.rmtree(outdir)
            os.mkdir(outdir)

        # gather repos and mirrors
        repos, mirrors = self.gather_repos(release)

        # Create the side repository if needed
        nvr = self.buildconfig['boot']['nvr']
        bid = self.buildconfig['boot']['bid']

        # prepare side repository
        if nvr or bid:
            rpms = self.get_rpms_nvr(nvr, bid)

            if rpms:
                self.logger.info('Creating side repository')
                siderepo = self.prep_siderepo(workdir, rpms, arch)

                if siderepo is None:
                    return None
                else:
                    self.logger.info('Side repository created')
                    repos.append(siderepo)
            else:
                return None

        boot_builder = Bootiso(arch, release, version, repos, mirrors, proxy, outdir, product)

        try:
            boot_builder.make_iso()
        except Exception as e:
            self.logger.error(traceback.format_exception(*sys.exc_info()))
            imgloc = None
        else:
            # boot image location
            self.logger.info('Boot ISO built succesfully')
            imgloc = [os.path.abspath(outdir)+'/images/boot.iso']

        return imgloc
    
    def build_dvd(self, kickstart):
        """ Builds DVD image """

        args = []

        arch = self.buildconfig['default']['arch']
        if arch != platform.machine():
            self.logger.error('DVD image arch requested should be the same as the build arch')
            return None

        name = self.buildconfig['dvd']['name']
        args.extend(['--name', name])

        ver = self.buildconfig['dvd']['version']
        args.extend(['--ver', ver])

        flavor = self.buildconfig['dvd']['flavor']
        args.extend(['--flavor', flavor])

        destdir = self.buildconfig['dvd']['destdir']
        args.extend(['--destdir', destdir])
    
        cachedir = self.buildconfig['dvd']['cachedir']
        args.extend(['--cachedir',  cachedir])

        bugurl = self.buildconfig['dvd']['bugurl']
        args.extend(['--bugurl',  bugurl])

        nosource = self.buildconfig['dvd']['nosource']
        if nosource == '1':
            args.extend(['--nosource'])
    
        sourceisos = self.buildconfig['dvd']['sourceisos']
        if sourceisos == '1':
            args.extend(['--sourceisos'])

        force = self.buildconfig['dvd']['force']
        if force == '1':
            args.extend(['--force'])

        stage = self.buildconfig['dvd']['stage']
        allowed_stages = ['all', '-G', '-C', '-B', '-I']

        if stage in allowed_stages:
            if stage == 'all':
                args.extend(['--all-stages'])
            else:
                args.extend([stage])
        else:
            self.logger.error('Invalid stage entered')
            return None
                        
        ksfname = tempfile.gettempdir() + '/' + 'dvd_kickstart.ks'
        args.extend(['-c', ksfname])

        with open(ksfname,'w') as fp:
            fp.write(json.loads(kickstart))

        # Create the side repository if needed
        nvr = self.buildconfig['dvd']['nvr']
        bid = self.buildconfig['dvd']['bid']
        workdir = self.buildconfig['dvd']['workdir']

        # prepare side repository
        if nvr or bid:
            rpms = self.get_rpms_nvr(nvr, bid)

            if rpms:
                self.logger.info('Creating side repository')
                siderepo = self.prep_siderepo(workdir, rpms, arch)

                if siderepo is None:
                    return None
                else:
                    self.logger.info('Side repository created')
                    # Add side repo to the existing KS file
                    self.add_repo(ksfname, siderepo)
            else:
                return None
    
        # fire pungi
        process_call = ['pungi']
        process_call.extend(args)

        try:
            self.logger.info('All set. Spawning DVD iso creation process.')
            subprocess.check_call(process_call)
        except subprocess.CalledProcessError:
            self.logger.error(traceback.format_exception(*sys.exc_info()))
            imgloc = None
        else:
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

    def build_live(self, kickstart):
        """ Live Image"""

        # Currently using livecd-creator
        # as the forward moving livemedia-creator is not yet
        # quite usable

        args = []

        ksfname = tempfile.gettempdir() + '/' + 'live_kickstart.ks'
        args.extend(['-c', ksfname])

        with open(ksfname,'w') as fp:
            fp.write(json.loads(kickstart))

        label = self.buildconfig['live']['label']
        args.extend(['-f', label])

        title = self.buildconfig['live']['title']
        args.extend(['--title', title])
    
        product = self.buildconfig['live']['product']
        args.extend(['--product', product])
    
        releasever = self.buildconfig['live']['releasever']
        args.extend(['--releasever', releasever])
        
        arch = self.buildconfig['live']['arch']
        if arch != platform.machine():
            self.logger.error('Live image arch requested should be the same as the build node arch')
            return None
    
        tmpdir = self.buildconfig['live']['tmpdir']
        args.extend(['-t', tmpdir])

        cachedir = self.buildconfig['live']['cachedir']
        args.extend(['--cache', cachedir])

        logfile = self.buildconfig['live']['logfile']
        args.extend(['--logfile', logfile])

        # Create the side repository if needed
        nvr = self.buildconfig['live']['nvr']
        bid = self.buildconfig['live']['bid']

        # prepare side repository
        if nvr or bid:
            rpms = self.get_rpms_nvr(nvr, bid)

            if rpms:
                self.logger.info('Creating side repository')
                siderepo = self.prep_siderepo(tmpdir, rpms, arch)

                if siderepo is None:
                    return None
                else:
                    self.logger.info('Side repository created')
                    # Add side repo to the existing KS file
                    self.add_repo(ksfname, siderepo)
            else:
                return None
    
        # fire livecd-creator
        process_call = ['livecd-creator']
        process_call.extend(args)

        try:
            self.logger.info('Calling livecd-creator')
            subprocess.check_call(process_call)
        except subprocess.CalledProcessError:
            self.logger.error(traceback.format_exception(*sys.exc_info()))
            imgloc = None
        else:
            # live image location
            imgloc = ['{0:s}.iso'.format(label)]

        return imgloc
