from __future__ import print_function

import tempfile
import subprocess
import pylorax
import os
import ConfigParser
import yum

# creates a boot ISO

class Bootiso():

    def __init__(self, arch, release, version, repos, mirrors, proxy, outputdir,product):
        self.arch = arch
        self.release = release
        self.version = version
        self.repos = repos
        self.mirrors = mirrors
        self.proxy = proxy
        self.outputdir = outputdir
        self.product = product


    # adapted from 
    # http://git.fedorahosted.org/git/?p=lorax.git;a=blob_plain;f=src/sbin/lorax;hb=HEAD
    def get_yum_base_object(self,installroot, repositories, mirrors, proxy, tempdir="/tmp"):
            
        def sanitize_repo(repo):
            if repo.startswith("/"):
                return "file://{0}".format(repo)
            elif (repo.startswith("http://") or repo.startswith("ftp://")
                  or repo.startswith("file://")):
                return repo
            else:
                return None

        # sanitize the repositories
        repositories = map(sanitize_repo, repositories)
        #mirrors = map(sanitize_repo, mirrors)
        
        # remove invalid repositories
        repositories = filter(bool, repositories)
        #mirrors = filter(bool, mirrors)

        cachedir = os.path.join(tempdir, "yum.cache")
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)

        yumconf = os.path.join(tempdir, "yum.conf")
        c = ConfigParser.ConfigParser()

        # add the main section
        section = "main"
        data = {"cachedir": cachedir,
                "keepcache": 0,
                "gpgcheck": 0,
                "plugins": 0,
                "reposdir": "",
                "tsflags": "nodocs"}

        if proxy:
            data["proxy"] = proxy

        # if excludepkgs:
        #     data["exclude"] = " ".join(excludepkgs)

        c.add_section(section)
        map(lambda (key, value): c.set(section, key, value), data.items())

        # add the main repository - the first repository from list
        section = "lorax-repo"
        data = {"name": "lorax repo",
                "baseurl": repositories[0],
                "enabled": 1}


        c.add_section(section)
        map(lambda (key, value): c.set(section, key, value), data.items())

        # add the extra repositories
        for n, extra in enumerate(repositories[1:], start=1):
            section = "lorax-extra-repo-{0:d}".format(n)
            data = {"name": "lorax extra repo {0:d}".format(n),
                    "baseurl": extra,
                    "enabled": 1}
        
            c.add_section(section)
            map(lambda (key, value): c.set(section, key, value), data.items())

        # # add the mirror
        # for n, mirror in enumerate(mirrors, start=1):
        #     section = "lorax-mirrors-{0:d}".format(n)
        #     data = {"name": "lorax mirror {0:d}".format(n),
        #             "mirrorlist": mirror,
        #             "enabled": 1 }

        #     c.add_section(section)
        #     map(lambda (key, value): c.set(section, key, value), data.items())


        # write the yum configuration file
        with open(yumconf, "w") as f:
            c.write(f)

        # create the yum base object
        yb = yum.YumBase()
            
        yb.preconf.fn = yumconf
        yb.preconf.root = installroot
    #yb.repos.setCacheDir(cachedir)

        return yb


    def make_iso(self):

        # create the temporary directory for lorax
        tempdir = tempfile.mkdtemp(prefix="lorax.", dir=tempfile.gettempdir())

        # create the yumbase object
        installtree = os.path.join(tempdir, "installtree")
        os.mkdir(installtree)
        yumtempdir = os.path.join(tempdir, "yum")
        os.mkdir(yumtempdir)

        yb = self.get_yum_base_object(installtree, self.repos, self.mirrors, self.proxy, yumtempdir)
        
        if yb is None:
            print("error: unable to create the yumbase object", file=sys.stderr)
            shutil.rmtree(tempdir)
            sys.exit(1)
            
        # run lorax
        lorax = pylorax.Lorax()

        # uses the default configuration file
        lorax.configure()

        #fire
        lorax.run(yb, self.product, self.version, self.release, None, None, False, tempdir, self.outputdir, self.arch, None, False)
