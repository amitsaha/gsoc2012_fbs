# For a given package name, downloads the latest package of each of
# the tags specified

# The big picture: Fedora on-demand build service
# Google Summer of code: 
# http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001
# Amit Saha <amitksaha@fedoraproject.org>
# May 2, 2012

# Uses autoqa's koji_utils module
# http://git.fedorahosted.org/git/?p=autoqa.git
# RPM downloading code snippet borrowed from Tim Flink's code 
# communicated personally

# Prerequisites:

# Install Autoqa 
# koji_utils.py at an importable location
# Set up Koji: 
# http://fedoraproject.org/wiki/Using_the_Koji_build_system#Initial_Fedora_Setup


import urllib
from koji_utils import *


kojihub_url = 'http://koji.fedoraproject.org/kojihub'
koji_pkgurl = 'http://kojipkgs.fedoraproject.org/packages'

# package names
packages=['pykickstart','anaconda','lorax']

# koji tags
tags=['f17','f17-updates-testing','f17-updates-candidate','rawhide'];

arches = ['x86_64', 'i386', 'i686', 'noarch']

repodir='/home/gene/gsoc/packages'

# connection object
conn=SimpleKojiClientSession()

# retrieve package information
for package in packages:
    print 'Package:: {0:s}'.format(package)
    for tag in tags:
        print 'Tag:: {0:s}'.format(tag)

        # key method defined in koji_utils.py
        build=conn.latest_by_tag(tag,package)

        if build!=None:
            # download the RPMs
            # get the RPMS available for a particular package
            rpms=conn.listRPMs(build['id'])
            rpms=filter(lambda r: not r['name'].endswith('-debuginfo') and r['arch'] in arches, rpms)

            baseurl = '/'.join((koji_pkgurl, build['package_name'], build['version'], build['release']))

            # List Package URL's and Download them
            for rpm in rpms:
                rpm['url'] = "%s/%s" % (baseurl, koji.pathinfo.rpm(rpm))

            print 'Downloading:: ',rpm['url']
        
            filename = '/'.join([repodir, rpm['url'].split('/')[-1]])
            filename=filename + '-'+tag
            
            urllib.urlretrieve(rpm['url'],filename)
        else:
            print 'No package available'
