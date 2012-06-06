# Command line interface to the image building code

from celery.execute import send_task
from tasks import build
import json

config=open('data/config/imagebuild.conf')
configstr=json.dumps(config.read())
config.close()


ks=open('data/config/kickstarts/fedora-install-fedora.ks')
ksstr=json.dumps(ks.read())
ks.close()

#send task to celery woker(s)
build.apply_async(args=[configstr,['fedora-install-fedora.ks',ksstr]],serializer="json")


