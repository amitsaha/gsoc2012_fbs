# Image Builder: Facilitate Custom Image Building for Fedora
# Copyright (C) 2012  Tim Flink Amit Saha

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
#          http://fedoraproject.org/wiki/User:Amitksaha

# This is a fabfile (http://docs.fabfile.org/en/1.4.2/index.html)
# to deploy image_builder

from fabric.api import task,run,hosts
import ConfigParser
import os

# config file
deploy_conf='conf/deploy.conf'

#workers
workers=[]

# Read configuration
config = ConfigParser.SafeConfigParser()
config.read(deploy_conf)

# Read broker config
i686_broker=config.get('broker','i686')
x86_64_broker=config.get('broker','x86_64')

# Read master config
master=config.get('master','host')
master_workdir=config.get('master','workdir')

# Read worker config
workers_i686=config.get('workers','i686')
workers_i686=workers_i686.split(';')
workers_x86_64=config.get('workers','x86_64')
workers_x86_64=workers_x86_64.split(';')
worker_workdir=config.get('workers','workdir')
workers.extend(workers_i686)
workers.extend(workers_x86_64)

# Setup nodes.conf in webapp/
with open('webapp/nodes.conf','w') as f:
    f.write('[i686]\n')
    f.write('broker_url={0:s}\n'.format(i686_broker))
    f.write('[x86_64]\n')
    f.write('broker_url={0:s}\n'.format(x86_64_broker))


# setup conf/celeryconfig_i686.py for workers
# setup conf/celeryconfig_x86_64.py for workers
with open('conf/celeryconfig_i686.py','w') as f:
    f.write('BROKER_URL = {0:s}\n'.format(i686_broker))
    f.write('CELERY_IMPORTS = ("tasks", )\n')

with open('conf/celeryconfig_x86_64.py','w') as f:
    f.write('BROKER_URL = {0:s}\n'.format(x86_64_broker))
    f.write('CELERY_IMPORTS = ("tasks", )\n')

# setup zdaemon_master.conf for Flask
with open('conf/zdaemon_master.conf','w') as f:
    f.write('<runner>\n')
    f.write('program python {0:s}/webapp/app.py\n'.format(master_workdir))
    f.write('directory {0:s}/webapp\n'.format(master_workdir))
    f.write('transcript {0:s}/zdaemon_webapp.log\n'.format(master_workdir))
    f.write('</runner>\n')

# setup zdaemon_celeryd.conf for celeryd
with open('conf/zdaemon_worker.conf','w') as f:
    import time
    f.write('<runner>\n')
    logfile='{0:s}/celery_{1:s}.log'.format(worker_workdir,str(time.time()).split('.')[0])
    f.write('program /usr/bin/celeryd --loglevel=INFO --logfile={0:s}\n'.format(logfile))
    f.write('directory {0:s}\n'.format(worker_workdir))
    f.write('transcript {0:s}/zdaemon_celeryd.log\n'.format(worker_workdir))
    f.write('socket-name {0:s}/celeryd_worker.sock\n'.format(worker_workdir))    
    f.write('</runner>\n')


@task
@hosts(master)
def install_packages_master():
    run('sudo yum --assumeyes install python-flask python-flask-wtf python-wtforms python-celery python-amqplib rabbitmq-server')
    
@task
@hosts(workers)
def install_packages_workers():
    run('sudo yum --assumeyes install koji pykickstart lorax livecd-tools pungi python-celery rabbitmq-server python-zdaemon')
    
   
@task
@hosts(master)
def create_workdir_master():
    # create the work dirs if they do not exist
    run('mkdir -p {0:s}'.format(os.path.abspath(master_workdir)))

@task
@hosts(workers)
def create_workdir_worker():
    # create the work dirs if they do not exist
    run('sudo mkdir -p {0:s}'.format(os.path.abspath(worker_workdir)))
    

@task
@hosts('localhost')
def copy_files():
    webapp=os.path.abspath('webapp')
    setuppy=os.path.abspath('setup.py')
    image_builder=os.path.abspath('image_builder')
    conf=os.path.abspath('conf')

    # copy webapp and image_builder+setup.py to master
    run('scp  {0:s}/ {1:s}:{2:s}/'.format(setuppy,master,os.path.abspath(master_workdir)))
    run('scp -r {0:s}/ {1:s}:{2:s}/'.format(webapp,master,os.path.abspath(master_workdir)))
    run('scp -r {0:s}/ {1:s}:{2:s}/'.format(image_builder,master,os.path.abspath(master_workdir)))
    run('scp {0:s}/zdaemon_master.conf {1:s}:{2:s}/'.format(conf,master,os.path.abspath(master_workdir)))

    # copy image_builder, setup.py, tasks.py
    for worker in workers:
        run('sudo scp -r {0:s} {1:s}:{2:s}/'.format(webapp,master,os.path.abspath(worker_workdir)))
        run('sudo scp -r {0:s}/tasks.py {1:s}:{2:s}/'.format(webapp,master,os.path.abspath(worker_workdir)))
        run('sudo scp -r {0:s} {1:s}:{2:s}/'.format(image_builder,master,os.path.abspath(worker_workdir)))
        run('sudo scp {0:s} {1:s}:{2:s}/'.format(setuppy,master,os.path.abspath(worker_workdir)))
        
    # celeryconfig,zdaemon
    for worker in workers_i686:
        run('sudo scp {0:s}/celeryconfig_i686.py {1:s}:{2:s}/celeryconfig.py'.format(conf,master,os.path.abspath(worker_workdir)))
        #zdaemon_worker.conf
        run('sudo scp {0:s}/zdaemon_worker.conf {1:s}:{2:s}/'.format(conf,master,os.path.abspath(worker_workdir)))
        

    for worker in workers_x86_64:
        run('sudo scp {0:s}/celeryconfig_x86_64.py {1:s}:{2:s}/celeryconfig.py'.format(conf,master,os.path.abspath(worker_workdir)))
        #zdaemon_worker.conf
        run('sudo scp {0:s}/zdaemon_worker.conf {1:s}:{2:s}/'.format(conf,master,os.path.abspath(worker_workdir)))

@task
@hosts(master)
def deploy_webapp():
    # Install image_builder
    print 'Installing image_builder library on {0:s}'.format(master)
    run('cd {0:s}/;sudo python setup.py install'.format(master_workdir))
    # then run webapp in background
    print 'Starting Web application'
    run('/usr/bin/zdaemon -d -C{0:s}/zdaemon_master.conf start'.format(master_workdir))
    
@task
@hosts(workers)
def deploy_workers():
    import time
    for worker in workers:
        # Install image_builder
        print 'Installing image_builder library on {0:s}'.format(worker)
        run('cd {0:s}/;sudo python setup.py install'.format(worker_workdir))
        run('sudo /usr/bin/zdaemon -d -C{0:s}/zdaemon_worker.conf start'.format(worker_workdir))
