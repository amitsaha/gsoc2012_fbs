# For a given package nvr, downloads it from Koji
# Creates a local repository with these packages

# The big picture: Fedora on-demand build service
# Google Summer of code: 
# http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001
# Amit Saha <amitksaha@fedoraproject.org>
# May 2, 2012

# Code adopted from Tim Flink's code 
# communicated personally

# Prerequisites:

# Set up Koji: 
# http://fedoraproject.org/wiki/Using_the_Koji_build_system#Initial_Fedora_Setup

# Amit Saha
# April 30, 2012

import koji
import urllib
import subprocess

# globals
kojihub_url = 'http://koji.fedoraproject.org/kojihub'
koji_pkgurl = 'http://kojipkgs.fedoraproject.org/packages'
arches = ['x86_64', 'i386', 'i686', 'noarch']

# where to store the packages
repodir = '/home/gene/gsoc/packages'

# Koji connection object
conn=koji.ClientSession(kojihub_url)

# package list with nvr
packages=['pykickstart-1.99.7-1.fc17','anaconda-17.23-1.fc17']


for package in packages:
    
    build=conn.getBuild(package)

    # get the RPMS available for a particular package
    rpms=conn.listRPMs(build['id'])
    rpms=filter(lambda r: not r['name'].endswith('-debuginfo') and r['arch'] in arches, rpms)

    baseurl = '/'.join((koji_pkgurl, build['package_name'], build['version'],
                    build['release']))

    # List Package URL's and Download them
    for rpm in rpms:
        rpm['url'] = "%s/%s" % (baseurl, koji.pathinfo.rpm(rpm))

        print rpm['url']
        
        filename = '/'.join([repodir, rpm['url'].split('/')[-1]])
        urllib.urlretrieve(rpm['url'],filename)
    
# Create a local repository
subprocess.call(['createrepo', repodir])
