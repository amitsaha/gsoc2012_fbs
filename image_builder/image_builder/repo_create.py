import os
import koji
import urllib
import subprocess

kojiurl = 'http://koji.fedoraproject.org/kojihub'
pkgurl = 'http://koji.fedoraproject.org/packages'

class RepoCreate(object):
    def __init__(self, repodir,arch):
        self.repodir = repodir
        self.arch=arch
        self.koji_connection = self.get_koji_connection()

    def get_koji_connection(self, url=kojiurl):
        return koji.ClientSession(url)

    def make_repo(self, packages):
        self.prep_repo_dir()
        print 'Downloading Extra Packages'
        self.download_packages(packages)
        self.make_repo_metadata()

    def prep_repo_dir(self):
        if not os.path.exists(self.repodir):
            os.makedirs(self.repodir)


    def make_repo_metadata(self):
        subprocess.call(['createrepo', self.repodir])


    def download_packages(self, packages):
        rpms = []

        for package in packages:
            rpms.extend(self.get_rpm_urls(package))

        
        for rpm in rpms:
            filename = '/'.join([self.repodir, rpm['url'].split('/')[-1]])
            urllib.urlretrieve(rpm['url'], filename)


    def get_build(self, nvr):
        return self.koji_connection.getBuild(nvr)


    def get_rpms(self, build_id):
        rpms = self.koji_connection.listRPMs(build_id)
        return filter(lambda r: not r['name'].endswith('-debuginfo') and r['arch'] in self.arch, rpms)
    

    def get_rpm_urls(self, nvr):

        # get build info
        build = self.get_build(nvr)
        pkg_name=build['package_name']

        # list rpms per build
        rpms = self.get_rpms(build['id'])
        
        # generate list of urls
        for rpm in rpms:
            baseurl = '/'.join((pkgurl, pkg_name,  build['version'],
                            build['release']))
            rpm['url'] = "%s/%s" % (baseurl, koji.pathinfo.rpm(rpm))
            
        return rpms
