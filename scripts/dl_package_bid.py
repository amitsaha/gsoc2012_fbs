# For a given build ID, downloads all packages from Koji

# The big picture: Fedora on-demand build service
# Google Summer of code: 
# http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001
# Amit Saha <amitksaha@fedoraproject.org>
# May 12, 2012

# Prerequisites:

# Set up Koji: 
# http://fedoraproject.org/wiki/Using_the_Koji_build_system#Initial_Fedora_Setup

# Amit Saha
# May 12, 2012

import koji
import urllib

# globals
kojihub_url = 'http://koji.fedoraproject.org/kojihub'
koji_pkgurl = 'http://kojipkgs.fedoraproject.org/packages'
arches = ['x86_64', 'i386', 'i686', 'noarch']

# where to store the packages
repodir = '/home/gene/gsoc/packages'

# Koji connection object
conn=koji.ClientSession(kojihub_url)

# Download packages with build IDs
bids=[302811]

for bid in bids:
    
    # get the build information for this bid
    build=conn.getBuild(bid)
    
    # NVR
    package=build['nvr']

    # Retrieve information via NVR
    build=conn.getBuild(package)

    # get the RPMS available for a particular package
    rpms=conn.listRPMs(build['id'])
    rpms=filter(lambda r: not r['name'].endswith('-debuginfo') and r['arch'] in arches, rpms)
    
    # package name, since the RPM's do not have a package name
    # field
    pkg_name=build['package_name']

    # List Package URL's and Download them
    for rpm in rpms:

        baseurl = '/'.join((koji_pkgurl, pkg_name, rpm['version'],
                        rpm['release']))
        
        rpm['url'] = "%s/%s" % (baseurl, koji.pathinfo.rpm(rpm))
        
        filename = '/'.join([repodir, rpm['url'].split('/')[-1]])
        
        print 'Retrieving',rpm['url']
        urllib.urlretrieve(rpm['url'],filename)
