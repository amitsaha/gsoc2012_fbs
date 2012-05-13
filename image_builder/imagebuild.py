import sys
import os
import argparse
import ConfigParser
import koji
from image_builder.repo_create import RepoCreate
from image_builder.bootiso import Bootiso

possible_types = ['boot','live','dvd']
possible_arches = ['x86_64', 'i686']
possible_products = ['fedora']
possible_releases = ['16', '17', 'rawhide']

#repository configuration
repo_config = 'repoinfo.conf'

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

# DVD Image
def build_dvd(arch, release, version, repos, proxy, outputdir,product):
    dvd_builder = Live(arch, release, version, repos, proxy, outputdir,product)
    dvd_builder.make_dvd()

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
    repodir = '%s/siderepo' % workdir
    repo_create = RepoCreate(repodir,arch)
    repo_create.make_repo(packages)

    repo_url = 'file://%s' % repodir
    return repo_url


def gather_repos(release, arch):
    # read repo configuration
    config = ConfigParser.SafeConfigParser({'arch':arch})
    config.read(repo_config)

    reponames = [ release ]

    updates=config.get('DEFAULT','updates')
    testing=config.get('DEFAULT','updates-testing')

    if updates:
        reponames.append('%s-updates' % release)

    if testing:
        reponames.append('%s-updates-testing' % release)

    repos = []
    for name in reponames:
        repos.append(config.get(name, 'url'))

    
    # get mirrorlist for this release
    mirrors=config.get(release, 'mirror')
    
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
    parser.add_argument('-nvr', metavar = 'nvr', type = str, nargs = '+', default=[],
                        help = 'Specify packages via NVR to download from Koji') 
    parser.add_argument('-bid', metavar = 'bid', type = str, nargs = '+', default=[],
                        help = 'Specify packages via buildids to be downloaded from Koji') 
    
    # parse
    args = parser.parse_args()

    workdir = os.path.abspath(args.w[0])
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    outputdir = os.path.abspath(args.o[0])
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    #iso_type = args.t[0].lowercase()
    iso_type = args.t[0]
    if not iso_type in possible_types:
        print "ISOs of type %s are not supported" % iso_type
        sys.exit(1)

    #arch = args.a[0].lowercase()
    arch = args.a[0]
    if not arch in possible_arches:
        print "ISOs for arch %s are not supported" % arch
        sys.exit(1)
    arch=[arch,'noarch']

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

    # if iso_type == 'boot':
    #     print('Building Boot ISO')
    #     build_bootiso(arch, release, version, repos, mirrors, None, outputdir, product)

    # if iso_type == 'live':
    #     print('Building Live Image')
    #     #build_live(arch, release, version, repos, None, outputdir, product)

    # if iso_type == 'dvd':
    #     print('Building DVD')
    #     #build_dvd(arch, release, version, repos, None, outputdir, product)
