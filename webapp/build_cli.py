""" Command line interface to the image building code.
First, deploy the workers and setup nodes.conf using the 
deployment script:
$ fab -f /path/to/deploy.py install_packages_worker 
install_packages_master copy_files_worker deploy_workers

Setup /etc/imagebuild/imagebuild.conf and copy the kicksart
file, if any to /etc/imagebuild/

"""
from celery.execute import send_task
from tasks import build

import json
import ConfigParser

# Read the imagebuild.conf file to find the 
# architecture of the image sought
config = ConfigParser.SafeConfigParser()
config.read('data/config/imagebuild.conf')
arch = config.get('DEFAULT','arch')
    
#find an appropriate build node from nodes.conf
#based on the arch
config = ConfigParser.SafeConfigParser()
config.read('nodes.conf')
broker_url = config.get(arch,'broker_url')

#now create the celeryconfig.py using this broker_url
with open('celeryconfig.py','w') as f:
    f.write('BROKER_URL = {0:s}\n'.format(broker_url))
    f.write('CELERY_RESULT_BACKEND = "amqp"\n')
    
# task delegation
buildconf=open('data/config/imagebuild.conf')
buildconf_str=json.dumps(buildconf.read())
buildconf.close()
        
# retrieve the kickstart file name if any    
config = ConfigParser.RawConfigParser()
config.read('data/config/imagebuild.conf')
if config.has_section('dvd'):
    head,ks_fname = os.path.split(config.get('dvd','config'))
else:
    if config.has_section('live'):
        head,ks_fname = os.path.split(config.get('live','config'))
    else:
        ks_fname = None

if ks_fname:
    ks=open('data/kickstarts/{0:s}'.format(ks_fname))
    ksstr=json.dumps(ks.read())
    ks.close()

#send task to celery woker(s)
if ks_fname:
    build.apply_async(args=[buildconf_str,[ks_fname,ksstr]],serializer="json")
else:
    build.apply_async(args=[buildconf_str,None],serializer="json")
    
