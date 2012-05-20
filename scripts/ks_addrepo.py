# Adds a repository to a Kickstart file
# and save it back
# Perhaps can be used similarly to modify other attributes as well
# Amit Saha (amitksaha@fedoraproject.org)

from pykickstart.parser import *
from pykickstart.version import makeVersion

# KS file to modify
ksfile='/usr/share/spin-kickstarts/fedora-live-desktop.ks'
newksfile='new_ks.ks'

# read
ksparser = KickstartParser(makeVersion())
ksparser.readKickstart(ksfile)

#obtain the handler dump
kshandlers=ksparser.handler

# add a repository
kshandlers.repo.repoList.extend(['repo --name="siderepo" --baseurl="file:///tmp/siderepo"\n'])

# Write back the ks file
outfile = open(newksfile, 'w')
outfile.write(kshandlers.__str__())
outfile.close()
