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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
#          http://fedoraproject.org/wiki/User:Amitksaha

"""
This is a fabfile (http://docs.fabfile.org/en/1.4.2/index.html)
to deploy image_builder. See HOWTO here: 
https://github.com/amitsaha/gsoc2012_fbs/blob/master/HOWTO

TODO: Too many globals being used. The way out is to use a Class
but to use it with Fabric involves a little convolution. Doable.
Will do.
"""

from fabric.api import task, run, hosts, cd, env, local
from fabric.operations import put

import ConfigParser
import os
import sys

# config file
deploy_conf = 'conf/deploy.conf'

# workers
workers = []

# Read configuration
config = ConfigParser.SafeConfigParser()
try:
    config.read(deploy_conf)
except ConfigParser.ParsingError:
    print 'Error parsing {0:s}'.format(deploy_conf)
    sys.exit(1)

# Read broker config
try:
    i686_broker = config.get('broker','i686')
    x86_64_broker = config.get('broker','x86_64')

    # Read master config
    master = config.get('master','host')
    master_workdir = config.get('master','workdir')

    # Read worker config
    workers_i686 = config.get('workers','i686')
    workers_i686 = workers_i686.split(';')
    workers_x86_64 = config.get('workers','x86_64')
    workers_x86_64 = workers_x86_64.split(';')
    worker_workdir = config.get('workers','workdir')
    workers.extend(workers_i686)
    workers.extend(workers_x86_64)
except (ConfigParser.NoSectionError,ConfigParser.NoOptionError):
    print 'One or more of the required sections/options missing in conf/deploy.conf'
    sys.exit(1)

# Setup nodes.conf in webapp/
with open('webapp/nodes.conf','w') as f:
    f.write('[i686]\n')
    f.write('broker_url = {0:s}\n'.format(i686_broker))
    f.write('[x86_64]\n')
    f.write('broker_url = {0:s}\n'.format(x86_64_broker))

# Setup nodes.conf in cli/
with open('cli/nodes.conf','w') as f:
    f.write('[i686]\n')
    f.write('broker_url = {0:s}\n'.format(i686_broker))
    f.write('[x86_64]\n')
    f.write('broker_url = {0:s}\n'.format(x86_64_broker))

# setup conf/celeryconfig_i686.py for workers
# setup conf/celeryconfig_x86_64.py for workers
with open('conf/celeryconfig_i686.py','w') as f:
    f.write('BROKER_URL  =  {0:s}\n'.format(i686_broker))
    f.write('CELERY_IMPORTS  =  ("tasks", )\n')

with open('conf/celeryconfig_x86_64.py','w') as f:
    f.write('BROKER_URL  =  {0:s}\n'.format(x86_64_broker))
    f.write('CELERY_IMPORTS  =  ("tasks", )\n')

# setup zdaemon_master.conf for Flask
with open('conf/zdaemon_master.conf','w') as f:
    f.write('<runner>\n')
    f.write('program python {0:s}/webapp/app.py\n'.format(master_workdir))
    f.write('directory {0:s}/webapp\n'.format(master_workdir))
    f.write('transcript {0:s}/zdaemon_webapp.log\n'.format(master_workdir))
    f.write('socket-name {0:s}/webapp.sock\n'.format(worker_workdir))    
    f.write('</runner>\n')

# setup zdaemon_celeryd.conf for celeryd
with open('conf/zdaemon_worker.conf','w') as f:
    f.write('<runner>\n')
    logfile = '{0:s}/celery_task.log'.format(worker_workdir)
    f.write('program /usr/bin/celeryd --events --loglevel=INFO --logfile={0:s}\n'.format(logfile))
    f.write('directory {0:s}\n'.format(worker_workdir))
    f.write('transcript {0:s}/zdaemon_celeryd.log\n'.format(worker_workdir))
    f.write('socket-name {0:s}/celeryd_worker.sock\n'.format(worker_workdir))    
    f.write('</runner>\n')

@task
@hosts(master)
def install_packages_master():
    """ Install dependencies on the 'master' where the
    web application will run
    """

    deps = 'python-flask python-flask-wtf python-wtforms python-celery python-amqplib rabbitmq-server python-zdaemon'
    run('sudo yum --assumeyes install {0:s}'.format(deps)) 
    
@task
@hosts(workers)
def install_packages_workers():
    """ Install dependencies on the workers"""

    deps = 'koji pykickstart lorax livecd-tools pungi python-celery rabbitmq-server python-zdaemon'
    run('yum --assumeyes install {0:s}'.format(deps))
    
@task
@hosts(master)
def copy_files_master():
    """ Copy the files to the 'master' from which the web 
    applicaiton will be serving requests
    """

    webapp = os.path.abspath('webapp')
    setuppy = os.path.abspath('setup.py')
    image_builder = os.path.abspath('image_builder')
    conf = os.path.abspath('conf')
    zdaemon = '{0:s}/zdaemon_master.conf'.format(conf)

    # create the work dirs if they do not exist
    run('mkdir -p {0:s}'.format(os.path.abspath(master_workdir)))

    put(setuppy, os.path.abspath(master_workdir), use_sudo=False)
    put(webapp, os.path.abspath(master_workdir), use_sudo=False)
    put(image_builder, os.path.abspath(master_workdir), use_sudo=False)
    put(zdaemon, os.path.abspath(master_workdir), use_sudo=False)

    return

@task
@hosts(workers)
def copy_files_workers():
    """ Copy the files to the workers where the build tasks
    will be performed
    """
    webapp = os.path.abspath('webapp')
    taskspy = '{0:s}/tasks.py'.format(webapp)
    setuppy = os.path.abspath('setup.py')
    image_builder = os.path.abspath('image_builder')
    conf = os.path.abspath('conf')
    celeryconfig_i686 = '{0:s}/celeryconfig_i686.py'.format(conf)
    celeryconfig_x86_64 = '{0:s}/celeryconfig_x86_64.py'.format(conf)
    celeryconfig = '{0:s}/celeryconfig.py'.format(worker_workdir)
    zdaemon = '{0:s}/zdaemon_worker.conf'.format(conf)

    # create the work dirs if they do not exist
    run('mkdir -p {0:s}'.format(os.path.abspath(worker_workdir)))
    
    # copy image_builder,  setup.py,  tasks.py
    put(setuppy, os.path.abspath(worker_workdir), use_sudo=True)
    put(taskspy, os.path.abspath(worker_workdir), use_sudo=True)
    put(image_builder, os.path.abspath(worker_workdir), use_sudo=True)
    put(zdaemon, os.path.abspath(worker_workdir), use_sudo=True)

    if env.host_string in workers_i686:
        put(celeryconfig_i686, celeryconfig, use_sudo=True)

    if env.host_string in workers_x86_64:
        put(celeryconfig_x86_64, celeryconfig, use_sudo=True)

@task
@hosts(master)
def deploy_webapp():
    """ Deploy the web application"""

    with cd(master_workdir):
        run('sudo python setup.py install')
        print 'Starting Web application'
        run('sudo /usr/bin/zdaemon -d -C{0:s}/zdaemon_master.conf start'.format(master_workdir))
    
@task
@hosts(workers)
def deploy_workers():
    """ Deploy the workers. Basically start celeryd"""

    with cd(worker_workdir):
        run('python setup.py install')
        run('service rabbitmq-server start')
        run('/usr/bin/zdaemon -d -C{0:s}/zdaemon_worker.conf start'.format(worker_workdir))
        run('celerymon --detach')

@task
def setup_cli():
    """ Setup for using the CLI """
    deps = 'python-celery python-amqplib rabbitmq-server'
    local('sudo yum --assumeyes install {0:s}'.format(deps)) 
    local('sudo python setup.py install')

@task
def run_tests():
    """ Run tests in testing/ """
    deps = 'pytest python-mock'
    run('sudo yum --assumeyes install {0:s}'.format(deps)) 
    run('sudo python setup.py install')
    run('py.test')    
