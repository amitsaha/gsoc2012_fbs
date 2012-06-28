import subprocess
from celery.task import task
import json
import os
import shutil
import ConfigParser

@task
def build(config,kickstart=[]):
    
    # Check for /etc/imagebuild
    if not os.path.exists('/etc/imagebuild'):
        os.makedirs('/etc/imagebuild')
    else:
        shutil.rmtree('/etc/imagebuild')
        os.makedirs('/etc/imagebuild')

    # recreate .conf file from config 
    # and copy it to /etc/imagebuild/imagebuild.conf

    configstr=json.loads(config)
    with open('/etc/imagebuild/imagebuild.conf','w') as f:
        f.write(configstr)

    if kickstart:
        fname=kickstart[0]
        ks=json.loads(kickstart[1])
        with open('/etc/imagebuild/{0:s}'.format(fname),'w') as f:
            f.write(ks)

    from image_builder.imagebuilder import ImageBuilder
    build = ImageBuilder()
    build.build()

    return
