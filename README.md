gsoc2012_fbs
============

Projet details: [On-Demand Fedora Build Service](http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001). See HOWTO for some draft usage instructions.

STATUS
------

+ Web Forms, REST API and Command Line interface for build job submission
+ Can use multiple worker nodes to build images
+ Copies the image(s) to the designated FTP location specified in staging.

TODO
----

+ Unit tests
+ Monitoring/Book-keeping of Jobs submitted/processed/running/finished
+ Validating the imagebuild.conf syntax/semantics for the CLI interfaces
+ Test building x86_64 images
+ Email notification
+ Need to think more on how the images will be stored and ability to identify
  an existing image uniquely. email_timestamp?

GOOD-TO-HAVE
-----------

+ User sessions
+ Enhanced UI (dynamic forms/CSS/etc)
+ Implement error handling on the client UI (Available; but server side for now)
