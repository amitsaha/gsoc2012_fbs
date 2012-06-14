gsoc2012_fbs
============

Projet details: [On-Demand Fedora Build Service](http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001). See HOWTO for some draft usage instructions.

STATUS
------

+ Tested to be working for i686 images
+ Copies the image(s) to the designated FTP location specified in staging.
+ Can use multiple worker nodes to build images (Only tested for i686)


TODO
----

+ Script to install dependencies (DONE)
+ Command line interface (REST API / otherwise)
+ Test building x86_64 images
+ Automatically copy the worker_src to celery workers (DONE)
+ Unit testing 
+ Implement error handling on the client UI
+ Logging (DONE)
+ Email notification
+ Enhanced UI (dynamic forms?)
+ Need to think more on how the images will be stored and ability to identify
  an existing image uniquely. Timestamp?