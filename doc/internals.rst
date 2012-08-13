=========
Internals
=========
This document will list some of the implementation details and aims to
give you a better idea of the project implementation. The details are
in no particular order and cannot be considered complete.


Kickstart files
---------------

The ``DVD`` and ``Live`` ISO creation requires the specification of
``kickstart`` files. Now, kickstart files are such that one kickstar
file may be building upon existing ones. The On-Demand Fedora Build
Service recommends you to specify kickstart files which are
*ksflattened* via ``ksflatten``. However, there are two
possibilities:

1. If you use one of the standard_ kickstart files, then you don't need to ksflatten them.
2. When you are using the service in local mode, you may specify a kickstart file which includes others, provided they are all in the same directory.

Logging and Build Monitoring
----------------------------

The application uses the standard ``logging`` module to log the
important events during the image building. A separate log file of the
form ``/tmp/imagebuild_<timestamp>/log`` is created for each new build
request. 

In *local mode*, this file can be monitored for the progress and reason
out a failure in the process, if any.

In *distributed mode*, this log file is exposed via a *build monitor*
whose URL is sent in the email notification on job submission. Basically,
this is a Flask_ web application returning the contents of the log
file upon a request.

Here is a note to be kept in mind when the application is deployed in
distributed mode:

Due to the integration of the application with *Celery* in the
distributed mode, a hackish way has been employed to prevent the
application's logging from getting hijacked by *Celery* (which is the
default behavior). Now, for some reason yet unknown this doesn't work
at random times. In that case, the Build monitor URL sent via the
email notification just returns a blank page. Till this is sorted out,
it is suggested to ``ssh`` to the particular worker node (retrievable
from the URL sent) and check the files, ``/tmp/celery_task.log`` and
``/tmp/zdaemon_celeryd.log`` for progress. If you cannot access the
worker node for some reason, just wait for the final notification
email and check your staging area for the image/logs.
           

.. _standard: http://git.fedorahosted.org/git/?p=spin-kickstarts.git;a=summary
.. _Flask: http://flask.pocoo.org/


In case of Failure
------------------

The final notification email aims to keep you well informed about the image
building result. However, for some reason, you do not get the final
email or an email with a blank message (due to the problem cited in
the previous section), your best bet is to just contact the person
responsible for deployment of the service or if you have access to the
worker nodes, simply monitor the two files mentioned in the previous
section to look for any possible hints.


Celery integration
------------------

In distributed mode, the application uses celery_ (Celery 3.0) for task delegation
to workers using RabbitMQ_ as the message broker. As of now here is a
brief overview of how the task delegation functions right now.

There are different types of supported images that can be built via
the application in distributed mode. Different combinations of
architecture and release are possible and hence it needs to be ensured
that the image building task is picked up by the right worker
node. The application maintains two brokers: one for ``i686`` and
another for ``x86_64`` workers. Thus, the workers capable of building
``i686`` nodes use the former and ``x86_64`` capable workers use the
latter for listening to incoming requests. Now, each broker
additionally has multiple queues - one for each supported Fedora
release. That is, the ``i686`` broker can have a ``Fedora 17`` queue
and a ``rawhide`` queue, corresponding to the two supported
releases. Hence, workers capable of building ``i686`` images of the
``Fedora17`` release will be listening to the ``Fedora-17`` queue on
the ``i686`` broker for incoming jobs and so on. The application takes
care of assigning the right queue to a job depending on the incoming
build task. 

A single celery task is defined in the file ``tasks.py``, which takes
care of passing the image build job to the workers. A copy of this
exist in the ``webapp/`` as well as ``cli/`` directory.

.. _celery: http://celeryproject.org/
.. _RabbitMQ: http://rabbitmq.com

Zdaemon for Dameonization
-------------------------

Zdaemon_ is used to run the various parts of the application as daemon
processes: celery, celery flower, build monitor, web application are
all run as daemons with the help of ``zdaemon``.

.. _Zdaemon: http://pypi.python.org/pypi/zdaemon/


Deployment
----------

The deployment of the web application, the worker nodes and pretty
much anything to do with the setup of the service is done by a
fabric_ script, ``deploy.py``. The script logically defines the
complete deployment into a number of *tasks*. It reads the
specifications given in the ``conf/deploy.conf`` configuration file
and carries out the specified tasks. See the `Getting Started`_
document so see how it is used to deploy the various parts of the
application.


.. _fabric: http://docs.fabfile.org/en/1.4.3/index.html
.. _`Getting Started`: HOWTO.html

Source tour
-----------

The core of the build service is the package ``image_builder``, which
lives in the ``image_builder/`` directory. The ``imagebuilder`` module
is the entry point to the functionalities and invokes the classes and
methods defined in the other modules, ``worker, notification, transfer`` and others. 

The Web application lives in the ``app/`` directory with the ``app``
module as the entry point.

The command line clients are in the ``cli/`` directory and the project
documentation lives in the ``doc/`` directory. 

The ``testing/`` directory is supposed to contain ``py.test`` unit tests for the
service, but is currently lacking in them.

The ``scripts/`` directory contains throwaway scripts not used by any
of the other code.



