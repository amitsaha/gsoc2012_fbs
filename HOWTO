	                	    Deploying the Image builder Service
				       Version 0.1 - June 14, 2012
				     Version 0.1 (Modified) - June 17, 2012
				     Version 0.1 (Modified) - June 25, 2012
       				       	       DRAFT


Get the sources: $ git clone git://github.com/amitsaha/gsoc2012_fbs.git

Navigate to gsoc2012_fbs, and setup conf/deploy.conf with the
following information (change the broker URL's as appropriate):

[broker]
i686="amqp://guest@localhost//"
x86_64="amqp://guest@localhost//"

[master]
host=gene@localhost
workdir=/tmp/imagebuilder_webapp

[workers]
i686=root@localhost
x86_64=root@localhost
workdir=/tmp/imagebuilder_worker

The broker section of the config file should specify the information
for the broker. Since, we can have two kinds of image build requests,
i686 and x86_64, we maintain two separate brokers for them. 

The master section specifies the user@host where the web application will
be setup and which will be responsible for delegating the build
requests to the workers. The workdir specificies the location which
will be used for running the web application from and the user must
have read/write permissions in that directory. 

The workers section specifies the hosts which will act as build
nodes. More than one worker is specified by listing them as
user1@host1;user1@host2; and so on. The workdir is used by the image
builder as its work dir and storing logs etc. 'root' access is needed
on the build nodes.


Once this information has been setup, install 'fabric':

# yum install fabric

Then, run the tasks from deploy.py (Note that the SSH server must be
running and accepting connections on the master and the workers). The
fabric file currently performs a number of separate tasks:

$ fab -f /path/to/deploy.py --list
This is a fabfile (http://docs.fabfile.org/en/1.4.2/index.html)
to deploy image_builder. See HOWTO here: 
https://github.com/amitsaha/gsoc2012_fbs/blob/master/HOWTO

TODO: Too many globals being used. The way out is to use a Class
but to use it with Fabric involves a little convolution. Doable.
Will do.

Available commands:

    copy_files_master         Copy the files to the 'master' from which the web
    copy_files_workers        Copy the files to the workers where the build tasks
    deploy_webapp             Deploy the web application
    deploy_workers            Deploy the workers. Basically start celeryd
    install_packages_master   Install dependencies on the 'master' where the
    install_packages_workers  Install dependencies on the workers
    setup_cli                 Setup for using the CLI

Command line Client
-------------------

To use the command line client, deploy the workers and setup nodes.conf using the 
deployment script: 

$ fab -f /path/to/deploy.py setup_cli install_packages_worker copy_files_worker 
deploy_workers 

In the 'cli' directory, setup imagebuild.conf (see sample_imagebuild.conf for a sample)
and copy a ksflattened KS file, if any. Then execute the build_cli.py script:

$ python build_cli.py 

Using the Web Interface/REST API
--------------------------------

$ fab -f /path/to/deploy.py
install_packages_worker install_packages_master copy_files_master copy_files_worker deploy_webapp deploy_workers

Once this is completed, the build service should be accessible from http://<master>:5000/build.
You may also use the REST API at http://<master>:5000/rest. See cli/build_rest.py for an example.

Currently, it is not possible to monitor the progress of the build. An email notification system
will soon be made possible which will notify you once the image is ready.