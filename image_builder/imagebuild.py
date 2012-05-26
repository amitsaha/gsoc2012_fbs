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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
# 	 http://fedoraproject.org/wiki/User:Amitksaha

import sys
import os
import argparse
import ConfigParser
import subprocess
import koji
import yum
from image_builder.repo_create import RepoCreate
from image_builder.bootiso import Bootiso
from pykickstart.parser import *
from pykickstart.version import makeVersion

# globals
possible_types = ['boot','dvd','live']
possible_arches = ['i386','i686','x86_64']
possible_products = ['fedora']
possible_releases = ['17', 'rawhide']


#Install image specifications
build_config='config/imagebuild.conf'

boot_config = 'config/boot.conf'
#repository config
repo_config = 'config/repoinfo.conf'
pungi_config= 'config/pungi.conf'
live_config = 'config/live.conf'

# Koji
kojihub_url = 'http://koji.fedoraproject.org/kojihub'

# Koji connection object
conn=koji.ClientSession(kojihub_url)


# Add a repository to an existing KS file
def add_repo(ksfile,siderepo):
    # read
    ksparser = KickstartParser(makeVersion())
    ksparser.readKickstart(ksfile)

    #obtain the handler dump
    kshandlers=ksparser.handler

    # add a repository
    kshandlers.repo.repoList.extend(['repo --name="siderepo" --baseurl={0:s}\n'.format(siderepo)])

    # Write a new ks file
    outfile = open(ksfile, 'w')
    outfile.write(kshandlers.__str__())
    outfile.close()



# get NVR given build ID
def get_nvr(bids,arch):

    nvr=[]
    for bid in bids:
        # get the build information for this bid
        build=conn.getBuild(int(bid))
        # NVR
        package=build['nvr']
        
        nvr.append(package)
    
    return nvr

# prepare a side repository given extra packages
def prep_siderepo(workdir, packages, arch):
    arch = [arch]
    arch.append('noarch')


    repodir = '%s/siderepo' % workdir
    repo_create = RepoCreate(repodir,arch)
    repo_create.make_repo(packages)

    repo_url = 'file://%s' % repodir
    return repo_url


# Gather repository list from repoinfo.conf
def gather_repos(release, arch):
    # read repo configuration
    
    # The mirrorlist and repositories uses i386 as $arch, instead of
    # i686
    if arch=='i686':
        arch='i386'

    config = ConfigParser.SafeConfigParser({'arch':arch})
    config.read(repo_config)

    reponames = [ release ]

    updates=config.get('DEFAULT','updates')
    testing=config.get('DEFAULT','updates-testing')

    if updates=='1':
        reponames.append('%s-updates' % release)

    if testing=='1':
        reponames.append('%s-updates-testing' % release)

    repos = []
    mirrors = []
    for name in reponames:
        # repos
        repos.append(config.get(name, 'url'))
        # mirrorlist
        mirrors.append(config.get(name,'mirror'))

    return repos,mirrors
    

# Boot ISO
def build_bootiso():

    # Read pungi configuration
    config = ConfigParser.SafeConfigParser()
    config.read(boot_config)

    arch=config.get('DEFAULT','arch')
    outdir=config.get('DEFAULT','outdir')
    workdir=config.get('DEFAULT','workdir')
    product=config.get('DEFAULT','product')
    release=config.get('DEFAULT','release')
    version=config.get('DEFAULT','version')
    proxy=config.get('DEFAULT','proxy')
    
    if proxy=='':
        proxy=None

    if not arch in possible_arches:
        print "ISOs for arch %s are not supported" % arch
        sys.exit(1)

    if not product in possible_products:
        print "Product %s is not supported" % product

    if not release in possible_releases:
        print "Release %s is not supported" % release
        sys.exit(1)


    # gather repos and mirrors
    repos,mirrors = gather_repos(release,arch)

    # Create the side repository if needed
    nvr=config.get('DEFAULT','nvr')
    bid=config.get('DEFAULT','bid')

    rpms_nvr=[]
    if nvr!='':
        for rpm in nvr.split(';'):
            rpms_nvr.append(rpm)

    bids=[]
    if bid!='':
        for rpm in bid.split(';'):
            bids.extend(str(rpm))
    
    if len(bids)>0:
        rpms_bid = get_nvr(bids,arch)
        rpms_nvr.extend(rpms_bid)
    
    # prepare side repository
    rpms = rpms_nvr

    if len(rpms) > 0:
        siderepo = prep_siderepo(workdir, rpms, arch)
        repos.append(siderepo)

    boot_builder = Bootiso(arch, release, version, repos, mirrors, proxy, outdir,product)
    boot_builder.make_iso()


# DVD Image
def build_dvd():
# See: https://fedorahosted.org/pungi/wiki/PungiDocs/RunningPungi
# TODO: Architecture - if the desired architecture sought is different from the
# host arch, use 'mock (?)'

    # Read pungi configuration
    config = ConfigParser.SafeConfigParser()
    config.read(pungi_config)

    args=[]

    name=config.get('DEFAULT','name')    
    args.extend(['--name', name])

    ver=config.get('DEFAULT','ver')    
    args.extend(['--ver', ver])

    flavor=config.get('DEFAULT','flavor')    
    args.extend(['--flavor', flavor])

    destdir=config.get('DEFAULT','destdir')    
    args.extend(['--destdir', destdir])
    
    cachedir=config.get('DEFAULT','cachedir')    
    args.extend(['--cachedir',  cachedir])

    bugurl=config.get('DEFAULT','bugurl') 
    args.extend(['--bugurl',  bugurl])

    nosource=config.get('DEFAULT','nosource')
    if nosource=='1':
        args.extend(['--nosource'])
    
    sourceisos=config.get('DEFAULT','sourceisos')
    if sourceisos=='1':
        args.extend(['--sourceisos'])

    force=config.get('DEFAULT','force')
    if force=='1':
        args.extend(['--force'])

    stage=config.get('DEFAULT','stage')
    allowed_stages=['all','-G','-C','-B','-I']

    if stage in allowed_stages:
        if stage=='all':
            args.extend(['--all-stages'])
        else:
            args.extend([stage])
    else:
        print 'Invalid stage entered'
                        
    ks=config.get('DEFAULT','config')
    #args.extend(['--config=', ks])
    args.extend(['-c', ks])

    # Create the side repository if needed
    nvr=config.get('DEFAULT','nvr')
    bid=config.get('DEFAULT','bid')

    arch=config.get('DEFAULT','arch')
    workdir=config.get('DEFAULT','workdir')

    rpms_nvr=[]
    if nvr!='':
        for rpm in nvr.split(';'):
            rpms_nvr.append(rpm)

    bids=[]
    if bid!='':
        for rpm in bid.split(';'):
            bids.extend(str(rpm))
    
    if len(bids)>0:
        rpms_bid = get_nvr(bids,arch)
        rpms_nvr.extend(rpms_bid)
    
    # prepare side repository
    rpms = rpms_nvr
    if len(rpms) > 0:
        siderepo = prep_siderepo(workdir, rpms, arch)
        # Add side repo to the existing KS file
        add_repo(ks,siderepo)
    
    # fire pungi
    process_call = ['pungi']
    process_call.extend(args)

    subprocess.call(process_call)


# Live Image
def build_live():

    # Currently using livecd-creator
    # as the forward moving livemedia-creator is not yet
    # quite usable

    # Read pungi configuration
    config = ConfigParser.SafeConfigParser()
    config.read(live_config)

    args=[]

    ks=config.get('DEFAULT','config')
    args.extend(['-c', ks])

    label=config.get('DEFAULT','label')
    args.extend(['-f', label])

    title=config.get('DEFAULT','title')
    args.extend(['--title', title])
    
    product=config.get('DEFAULT','product')
    args.extend(['--product', product])

    releasever=config.get('DEFAULT','releasever')
    args.extend(['--releasever', releasever])

    arch=config.get('DEFAULT','arch')
    yb = yum.YumBase()
    
    if arch!=yb.arch.canonarch:
        print 'Live image arch should be the same as the build arch'
        sys.exit(1)
    
    tmpdir=config.get('DEFAULT','tmpdir')
    args.extend(['-t', tmpdir])

    cachedir=config.get('DEFAULT','cachedir')
    args.extend(['--cache', cachedir])

    logfile=config.get('DEFAULT','logfile')
    args.extend(['--logfile', logfile])


    # Create the side repository if needed
    nvr=config.get('DEFAULT','nvr')
    bid=config.get('DEFAULT','bid')

    rpms_nvr=[]
    if nvr!='':
        for rpm in nvr.split(';'):
            rpms_nvr.append(rpm)

    bids=[]
    if bid!='':
        for rpm in bid.split(';'):
            bids.extend(str(rpm))
    
    if len(bids)>0:
        rpms_bid = get_nvr(bids,arch)
        rpms_nvr.extend(rpms_bid)
    
    # prepare side repository
    rpms = rpms_nvr
    arch=config.get('DEFAULT','arch')
    tmpdir=config.get('DEFAULT','tmpdir')

    if len(rpms) > 0:
        siderepo = prep_siderepo(tmpdir, rpms, arch)
        # Add side repo to the existing KS file
        add_repo(ks,siderepo)
    
    # fire pungi
    process_call = ['livecd-creator']
    process_call.extend(args)

    subprocess.call(process_call)


if __name__ == '__main__':

    # Read configuration
    config = ConfigParser.SafeConfigParser()
    config.read(build_config)

    iso_type=config.get('DEFAULT','type')

    if not iso_type in possible_types:
        print 'ISOs of type {0:s} are not supported'.format(iso_type)
        sys.exit(1)

    # boot
    if iso_type=='boot':
        print 'Building Boot ISO'
        build_bootiso()

    # DVD
    if iso_type == 'dvd':
        print'Building DVD'
        build_dvd()
        
    #Live image
    if iso_type == 'live':
        print 'Building Live Image'
        build_live()
