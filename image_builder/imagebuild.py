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
import koji
import subprocess
from image_builder.repo_create import RepoCreate
from image_builder.bootiso import Bootiso
from pykickstart.parser import *
from pykickstart.version import makeVersion


possible_types = ['boot','live','dvd']
possible_arches = ['x86_64', 'i386','i686']
possible_products = ['fedora']
possible_releases = ['16', '17', 'rawhide']

#configuration files
repo_config = 'repoinfo.conf'
pungi_config = 'pungi.conf'

# Koji
kojihub_url = 'http://koji.fedoraproject.org/kojihub'

# Koji connection object
conn=koji.ClientSession(kojihub_url)

def main_func():
    pass

# Boot ISO
def build_bootiso(arch, release, version, repos, mirrors, proxy, outputdir,product):
    boot_builder = Bootiso(arch, release, version, repos, mirrors, proxy, outputdir,product)
    boot_builder.make_iso()

# Live Image
def build_live(arch, release, version, repos, proxy, outputdir,product):
    live_builder = Live(arch, release, version, repos, proxy, outputdir,product)
    live_builder.make_live()


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


# DVD Image
def build_dvd():
# See: https://fedorahosted.org/pungi/wiki/PungiDocs/RunningPungi
# TODO: Architecture - if the desired architecture sought is different from the
# host arch, use 'mock'

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

    rpms_nvr=[]
    
    for rpm in nvr.split(';'):
        rpms_nvr.extend(rpm)

    bids=[]
    for rpm in bid.split(';'):
        bids.append(str(rpm))
    
    arch=config.get('DEFAULT','arch')
    rpms_bid = get_nvr(bids,arch)
    rpms_nvr.extend(rpms_bid)
    
    # prepare side repository
    workdir=config.get('DEFAULT','workdir')
    rpms = rpms_nvr
    if len(rpms) > 0:
        siderepo = prep_siderepo(workdir, rpms, arch)
        # Add side repo to the existing KS file
        add_repo(ks,siderepo)
    
    # fire pungi
    process_call = ['pungi']
    process_call.extend(args)

    print process_call

    subprocess.call(process_call)

def get_nvr(bids,arch):

    nvr=[]
    for bid in bids:
        # get the build information for this bid
        build=conn.getBuild(int(bid))
        # NVR
        package=build['nvr']
        
        nvr.append(package)
    
    return nvr

def prep_siderepo(workdir, packages, arch):
    arch = [arch]
    arch.append('noarch')


    repodir = '%s/siderepo' % workdir
    repo_create = RepoCreate(repodir,arch)
    repo_create.make_repo(packages)

    repo_url = 'file://%s' % repodir
    return repo_url


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
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Build Test ISOs for Fedora')
    parser.add_argument('-t', metavar = 'type', type = str, nargs = 1,
                        default = 'boot',  help = 'Type of ISO to build: boot live DVD')
    parser.add_argument('-a', metavar = 'arch', type = str, nargs = 1,
                        default = 'x86_64', help = 'Arch of image: x86_64 i386')
    parser.add_argument('-o', metavar = 'output_dir', type = str, nargs = 1,
                        default = './images', help = 'Output directory')
    parser.add_argument('-w', metavar = 'work_dir', type = str, nargs = 1,
                        default = './work', help = 'Work directory for image building')
    parser.add_argument('-p', metavar = 'product', type = str, nargs = 1,
                        default = 'Fedora', help = 'Product to build')
    parser.add_argument('-r', metavar = 'release', type = str, nargs = 1,
                        help = 'Release of product to build')
    parser.add_argument('-v', metavar = 'version', type = str, nargs = 1,
                        help = 'Version of ISO to build')
    parser.add_argument('--nvr', metavar = 'nvr', type = str, nargs = '+', default=[],
                        help = 'Specify packages via NVR to download from Koji') 
    parser.add_argument('--bid', metavar = 'bid', type = str, nargs = '+', default=[],
                        help = 'Specify packages via buildids to be downloaded from Koji') 
    
    # parse
    args = parser.parse_args()

    iso_type = args.t[0]


    if not iso_type in possible_types:
        print "ISOs of type %s are not supported" % iso_type
        
        sys.exit(1)

    # boot
    if iso_type=='boot':
        workdir = os.path.abspath(args.w[0])
        if not os.path.exists(workdir):
            os.makedirs(workdir)

        outputdir = os.path.abspath(args.o[0])
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

            
        arch = args.a[0]
        if not arch in possible_arches:
            print "ISOs for arch %s are not supported" % arch
            sys.exit(1)

    #product = args.p[0].lowercase()
        product = args.p[0]
        if not product in possible_products:
            print "Product %s is not supported" % product

        release = args.r[0]
        if not release in possible_releases:
            print "Release %s is not supported" % release
            sys.exit(1)

        version = args.v[0]

        repos,mirrors = gather_repos(release,arch)
    
         #RPMs by NVR
        rpms_nvr=[]
        if len(args.nvr)>0:
            rpms_nvr = args.nvr

         #RPMs by Build IDs
            if len(args.bid)>0:
                # get the NVR from the bids so that we can use the same code to 
                # download the packages
                rpms_bid = get_nvr(args.bid,arch)
                # all rpms' NVR
                rpms_nvr.extend(rpms_bid)
    
            # prepare side repository
            rpms = rpms_nvr
            if len(rpms) > 0:
                siderepo = prep_siderepo(workdir, rpms, arch)
                repos.append(siderepo)

            print('Building Boot ISO')
            build_bootiso(arch, release, version, repos, mirrors, None, outputdir, product)


    # DVD
    if iso_type == 'dvd':
        print('Building DVD')
        build_dvd()

    # if iso_type == 'live':
    #     print('Building Live Image')
    #     #build_live(arch, release, version, repos, None, outputdir, product)

