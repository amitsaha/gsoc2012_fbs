import sys
import os
import argparse
import ConfigParser
from repo_create import RepoCreate
from bootiso import Bootiso

possible_types = ['boot']
possible_arches = ['x86_64', 'i386']
possible_products = ['fedora']
possible_releases = ['f15', 'f16', 'f17', 'rawhide']

config_file = 'image_builder/repoinfo.conf'

def main_func():
    pass

def build_bootiso(product, release, version, repos, outputdir):
    boot_builder = Bootiso(version, release, repos, outputdir)
    boot_builder.make_iso()

def prep_siderepo(workdir, packages, arch):
    repodir = '%s/siderepo' % workdir
    repo_create = RepoCreate(repodir)
    repo_create.make_repo(packages, arches=[arch, 'noarch'])

    repo_url = 'file://%s' % repodir
    return repodir


def gather_repos(product, release, arch, updates=True, testing=False):
    config = ConfigParser.SafeConfigParser(defaults = {'arch':arch})
    config.read(config_file)

    print os.path.abspath(config_file)

    reponames = [ release ]
    if updates:
        reponames.append('%s-updates' % release)

    if testing:
        reponames.append('%s-updates-testing' % release)

    repos = []
    for name in reponames:
        repos.append((name, config.get(name, 'url')))

    return repos

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Build Test ISOs for Fedora')
    parser.add_argument('-t', metavar = 'type', type = str, nargs = '?',
                        default = 'boot',  help = 'Type of ISO to build: boot live DVD')
    parser.add_argument('-a', metavar = 'arch', type = str, nargs = 1,
                        default = 'x86_64', help = 'Arch of image: x86_64 i386')
    parser.add_argument('-o', metavar = 'output_dir', type = str, nargs = '?',
                        default = './images', help = 'Output directory')
    parser.add_argument('-w', metavar = 'work_dir', type = str, nargs = '?',
                        default = './work', help = 'Work directory for image building')
    parser.add_argument('-p', metavar = 'product', type = str, nargs = '?',
                        default = 'Fedora', help = 'Product to build')
    parser.add_argument('-r', metavar = 'release', type = str, nargs = 1,
                        help = 'Release of product to build')
    parser.add_argument('-v', metavar = 'version', type = str, nargs = 1,
                        help = 'Version of ISO to build')
    parser.add_argument('-e', metavar = 'nvr', type = str, nargs = '*',
                        help = 'Extra RPM to download from koji')
    args = parser.parse_args()

    workdir = os.path.abspath(args.w[0])
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    outputdir = os.path.abspath(args.o[0])
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    iso_type = args.t.lower()
    if not iso_type in possible_types:
        print "ISOs of type %s are not supported" % iso_type
        sys.exit(1)

    arch = args.a[0].lower()
    if not arch in possible_arches:
        print "ISOs for arch %s are not supported" % arch
        sys.exit(1)

    product = args.p.lower()
    if not product in possible_products:
        print "Product %s is not supported" % product
        sys.exit(1)

    release = args.r[0]
    if not release in possible_releases:
        print "Release %s is not supported" % release
        sys.exit(1)

    version = args.v[0]

    repos = gather_repos(product, release, arch)

    print "repos to use: %s" % str(repos)

    rpms = args.e
    if len(rpms) > 0:
        siderepo = prep_siderepo(workdir, rpms, arch)
        repos.append(('siderepo', siderepo))

    if iso_type == 'boot':
        build_bootiso(product, release, version, repos, outputdir)
