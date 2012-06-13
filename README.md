gsoc2012_fbs
============

[On-Demand Fedora Build Service](http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001)

SOURCE TOUR
-----------

+ webapp: Web application lives in app.py. Begin there.
+ image_builder: Working snapshot of image building code
+ worker_src: Sources which has to be copied to the worker and celeryd should be started from this directory, where the sources are copied. The image building code is same as in image_builder/, and tasks.py from webapp. They have to be the same!
+ scripts: Throw-away scripts

DEPENDENCIES
------------

On the node used for deployment (using deploy.py), you need 'fabric' installed:

+ # yum install fabric

The Web application's dependencies can be installed by:

+ #yum install python-flask python-flask-wtf python-wtforms python-celery python-amqplib rabbitmq-server 

On the build node(s), the following dependencies are to be installed:

+ #yum install koji pykickstart lorax livecd-tools pungi python-celery rabbitmq-server python-zdaemon


STATUS
------

+ Tested to be working for i686 images
+ Copies the image(s) to the designated FTP location specified in staging.
+ Can use multiple worker nodes to build images (Only tested for i686)


TODO
----

+ <strike>Script to install dependencies</strike> (will use deploy.py task)
+ Finish the cli client in webapp/
+ x86_64 images
+ Automatically copy the worker_src to celery workers
+ Unit testing 
+ Implement error handling on the client UI
+ Logging
+ Email notification
+ Enhanced UI (dynamic forms?)
+ Need to think more on how the images will be stored and ability to identify
  an existing image uniquely. Timestamp?