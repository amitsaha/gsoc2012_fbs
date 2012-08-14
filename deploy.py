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
to deploy On-Demand Fedora Build Service.
See doc/ for usage guidelines.

"""

from fabric.api import task, run, hosts, cd, env, local
from fabric.operations import put

import ConfigParser
import os
import sys

# config file
deploy_conf = 'conf/deploy.conf'

items = []
def flatten(mylist):
    for item in mylist:
        if type(item) is list:
            flatten(item)
        else:
            items.append(item)
    return items

# Read configuration
config = ConfigParser.SafeConfigParser()
try:
    config.read(deploy_conf)
except ConfigParser.ParsingError:
    print 'Error parsing {0:s}'.format(deploy_conf)
    sys.exit(1)

try:
    # Read broker config
    i686_broker = config.get('broker','i686')
    x86_64_broker = config.get('broker','x86_64')

    i686_broker_host = i686_broker.split('@')[1]
    i686_broker_host = i686_broker_host.split('//')[0]

    x86_64_broker_host = x86_64_broker.split('@')[1]
    x86_64_broker_host = x86_64_broker_host.split('//')[0]

    # read supported releases
    releases = config.get('releases','releases')
    releases = releases.split(',')

    # Read master config
    master = config.get('master','host')
    master_workdir = config.get('master','workdir')

    # Read worker config
    # dictionary of the form
    # workers_dict[release] => nodes_dict
    # nodes_dict[arch] = ['node1',...]
    workers_dict = {}
    for release in releases:
        nodes_dict = {}
        nodes = [] 
        for arch in ['i686','x86_64']:
            # if this arch is defined for this release
            if config.has_option('workers-{0:s}'.format(release),arch):
                nodes = config.get('workers-{0:s}'.format(release),arch).split(';')
            else:
                nodes = []

            nodes_dict[arch] = nodes
            worker_workdir = config.get('workers-{0:s}'.format(release),'workdir')

        workers_dict[release] = nodes_dict

    # form the list of workers
    workers = []
    for worker in workers_dict.values():
        workers.extend(worker.values())

    workers = flatten(workers)

    # Read SMTP config
    SMTP_SERVER = config.get('SMTP', 'server')
    SMTP_PORT = config.get('SMTP', 'port')
    sender = config.get('SMTP', 'login')
    password = config.get('SMTP', 'password')

except (ConfigParser.NoSectionError,ConfigParser.NoOptionError):

    print 'One or more of the required sections/options missing in conf/deploy.conf'
    sys.exit(1)

# Setup nodes.conf in webapp/
with open('webapp/nodes.conf','w') as f:
    f.write('[i686]\n')
    f.write('broker_url = {0:s}\n'.format(i686_broker))
    f.write('[x86_64]\n')
    f.write('broker_url = {0:s}\n'.format(x86_64_broker))

# Setup smtp.py in image_builder/
with open('image_builder/smtp.py','w') as f:
    f.write('smtp_server={0:s}\n'.format(SMTP_SERVER))
    f.write('smtp_port={0:s}\n'.format(SMTP_PORT))
    f.write('smtp_login={0:s}\n'.format(sender))
    f.write('smtp_password={0:s}\n'.format(password))

# setup conf/celeryconfig_i686.py for workers
# setup conf/celeryconfig_x86_64.py for workers
with open('conf/celeryconfig_i686.py','w') as f:
    f.write('BROKER_URL  =  {0:s}\n'.format(i686_broker))
    f.write('CELERY_RESULT_BACKEND = "amqp"\n')
    f.write('CELERY_IMPORTS = ("tasks", )\n')

with open('conf/celeryconfig_x86_64.py','w') as f:
    f.write('BROKER_URL  =  {0:s}\n'.format(x86_64_broker))
    f.write('CELERY_RESULT_BACKEND = "amqp"\n')
    f.write('CELERY_IMPORTS = ("tasks", )\n')

# setup zdaemon_master.conf for Flask
with open('conf/zdaemon_master.conf','w') as f:
    f.write('<runner>\n')
    f.write('program python {0:s}/webapp/app.py\n'.format(master_workdir))
    f.write('directory {0:s}/webapp\n'.format(master_workdir))
    f.write('transcript {0:s}/zdaemon_webapp.log\n'.format(master_workdir))
    f.write('socket-name {0:s}/webapp.sock\n'.format(worker_workdir))    
    f.write('</runner>\n')
    
# setup zdaemon_celeryd.conf for celeryd
# release specific
# celeryconfig.py will take care of the architecture
for release in releases:
    fname = 'conf/zdaemon_worker_{0:s}.conf'.format(release)
    with open(fname,'w') as f:
        f.write('<runner>\n')
        logfile = '{0:s}/celery_task.log'.format(worker_workdir)
        f.write('program /bin/celery -A tasks worker -Q fedora-{1:s} --loglevel=INFO --logfile={0:s}\n'.format(logfile,release))
        f.write('directory {0:s}\n'.format(worker_workdir))
        f.write('transcript {0:s}/zdaemon_celeryd.log\n'.format(worker_workdir))
        f.write('socket-name {0:s}/celeryd_worker.sock\n'.format(worker_workdir))    
        f.write('</runner>\n')

# setup zdaemon_monitor.conf for build monitor
with open('conf/zdaemon_monitor.conf','w') as f:
    f.write('<runner>\n')
    f.write('program python image_builder/build_monitor.py\n')
    f.write('directory {0:s}\n'.format(worker_workdir))
    f.write('socket-name {0:s}/monitor.sock\n'.format(worker_workdir))    
    f.write('</runner>\n')

# setup zdaemon_celeryd.conf for celeryd
with open('conf/zdaemon_flower.conf','w') as f:
    f.write('<runner>\n')
    logfile = '{0:s}/celery_flower.log'.format(worker_workdir)
    f.write('program /bin/celery flower\n')
    f.write('directory {0:s}\n'.format(worker_workdir))
    f.write('transcript {0:s}/zdaemon_flower.log\n'.format(worker_workdir))
    f.write('socket-name {0:s}/celery_flower.sock\n'.format(worker_workdir))    
    f.write('</runner>\n')


@task
@hosts(master)
def install_packages_webapp():
    """ Install dependencies for the web application
    """

    deps = 'python-flask python-flask-wtf python-wtforms python-amqplib rabbitmq-server python-zdaemon'
    run('sudo yum --assumeyes --enablerepo=updates install {0:s}'.format(deps)) 

    # install celery 3.0 (not available in repos)
    run('sudo yum --assumeyes --enablerepo=updates install gcc python-devel python-pip')
    run('sudo pip-python install celery')
    
@task
@hosts(workers)
def install_packages_workers():
    """ Install dependencies on the workers"""

    deps = 'koji pykickstart lorax livecd-tools pungi rabbitmq-server python-zdaemon python-flask python-amqplib spin-kickstarts'
    run('yum --assumeyes --enablerepo=updates install {0:s}'.format(deps))

    # install celery 3.0 (not available in repos)
    run('yum --assumeyes --enablerepo=updates install gcc python-devel python-pip')
    run('pip-python install celery')
    run('pip-python install flower')
    
    
@task
@hosts(master)
def copy_files_webapp():
    """ Copy files to the web application host
    """

    webapp = os.path.abspath('webapp')
    setuppy = os.path.abspath('setup.py')
    image_builder = os.path.abspath('image_builder')
    conf = os.path.abspath('conf')
    zdaemon = '{0:s}/zdaemon_master.conf'.format(conf)

    # clean and create the work dirs
    run('sudo rm -rf {0:s}'.format(os.path.abspath(master_workdir)))
    run('mkdir -p {0:s}'.format(os.path.abspath(master_workdir)))

    put(setuppy, os.path.abspath(master_workdir), use_sudo=False)
    put(webapp, os.path.abspath(master_workdir), use_sudo=False)
    put(image_builder, os.path.abspath(master_workdir), use_sudo=False)
    put(zdaemon, os.path.abspath(master_workdir), use_sudo=False)

    return

@task
@hosts(workers)
def copy_files_workers():
    """ Copy the files to the workers """

    webapp = os.path.abspath('webapp')
    taskspy = '{0:s}/tasks.py'.format(webapp)
    setuppy = os.path.abspath('setup.py')
    image_builder = os.path.abspath('image_builder')
    conf = os.path.abspath('conf')
    celeryconfig_i686 = '{0:s}/celeryconfig_i686.py'.format(conf)
    celeryconfig_x86_64 = '{0:s}/celeryconfig_x86_64.py'.format(conf)
    celeryconfig = '{0:s}/celeryconfig.py'.format(worker_workdir)
    zdaemon_worker = '{0:s}/zdaemon_worker.conf'.format(worker_workdir)
    zdaemon_monitor = '{0:s}/zdaemon_monitor.conf'.format(conf)
    zdaemon_flower = '{0:s}/zdaemon_flower.conf'.format(conf)
    
    # clean and create the work dirs
    run('rm -rf {0:s}'.format(os.path.abspath(worker_workdir)))
    run('mkdir -p {0:s}'.format(os.path.abspath(worker_workdir)))
    
    # copy image_builder,  setup.py,  tasks.py
    put(setuppy, os.path.abspath(worker_workdir), use_sudo=True)
    put(taskspy, os.path.abspath(worker_workdir), use_sudo=True)
    put(image_builder, os.path.abspath(worker_workdir), use_sudo=True)
    put(zdaemon_monitor, os.path.abspath(worker_workdir), use_sudo=True)
    put(zdaemon_flower, os.path.abspath(worker_workdir), use_sudo=True)

    # check which releases this worker supports and 
    # copy the appropriate celeryconfig and zdaemon_worker 
    #conf file
    for release in releases:
        if env.host_string in workers_dict[release]['i686']:
            put(celeryconfig_i686, celeryconfig, use_sudo=True)
            zdaemon_worker_release = '{0:s}/zdaemon_worker_{1:s}.conf'.format(conf,release)
        if env.host_string in workers_dict[release]['x86_64']:
            put(celeryconfig_x86_64, celeryconfig, use_sudo=True)
            zdaemon_worker_release = '{0:s}/zdaemon_worker_{1:s}.conf'.format(conf,release)

    put(zdaemon_worker_release, zdaemon_worker, use_sudo=True)

@task
@hosts(master)
def deploy_webapp():
    """ Deploy the web application (and enable REST API)"""

    with cd(master_workdir):
        run('sudo python setup.py install')
        run('sudo /usr/bin/zdaemon -d -C{0:s}/zdaemon_master.conf start'.format(master_workdir))

@task
@hosts(workers)
def deploy_workers():
    """ Deploy the workers """


    with cd(worker_workdir):
        run('python setup.py install')
        
        if env.host_string.split('@')[1] == i686_broker_host or env.host_string.split('@')[1] == x86_64_broker_host:
            run('service rabbitmq-server start')

        run('/usr/bin/zdaemon -d -C{0:s}/zdaemon_monitor.conf start'.format(worker_workdir))
        run('/usr/bin/zdaemon -d -C{0:s}/zdaemon_worker.conf start'.format(worker_workdir))
        run('/usr/bin/zdaemon -d -C{0:s}/zdaemon_flower.conf start'.format(worker_workdir))

    run('service iptables stop')
    run('setenforce 0')
    # copy the /usr/share/spin-kickstarts to /tmp
    # for Live and DVD image building.
    # Hence the supplied KS file need not be ksflattened
    run('cp /usr/share/spin-kickstarts/*.ks /tmp/')

@task
def deploy_local():
    """ Deployment in local mode """

    # image building tools/misc.
    deps = 'koji lorax livecd-tools pungi pykickstart spin-kickstarts'
    local('sudo yum --enablerepo=updates --assumeyes install {0:s}'.format(deps)) 

    # image builder package instalaltion
    local('sudo python setup.py install')

    # copy the /usr/share/spin-kickstarts to /tmp
    # for Live and DVD image building.
    # Hence the supplied KS file need not be ksflattened
    local('sudo cp /usr/share/spin-kickstarts/*.ks /tmp/')


@task
def setup_cli():
    """ Deployment for using the command line client in distributed mode """

    # Setup nodes.conf in cli/
    with open('cli/nodes.conf','w') as f:
        f.write('[i686]\n')
        f.write('broker_url = {0:s}\n'.format(i686_broker))
        f.write('[x86_64]\n')
        f.write('broker_url = {0:s}\n'.format(x86_64_broker))


    deps = 'python-amqplib'
    local('sudo yum --assumeyes install {0:s}'.format(deps)) 
    local('sudo python setup.py install')

    # install celery 3.0 (not available in repos)
    run('sudo yum --assumeyes --enablerepo=updates install gcc python-devel python-pip')
    run('sudo pip-python install celery')


# @task
# def run_tests():
#     """ Run tests in testing/ """
#     deps = 'pytest python-mock'
#     local('sudo yum --assumeyes install {0:s}'.format(deps)) 
#     local('sudo python setup.py install')
#     local('py.test')
