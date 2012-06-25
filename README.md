gsoc2012_fbs
============

Projet details: [On-Demand Fedora Build Service](http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001). See HOWTO for some draft usage instructions.

STATUS
------

+ Web based and command line client for build job submission
+ Can use multiple worker nodes to build images
+ Copies the image(s) to the designated FTP location specified in staging.

TODO
----
+ Unit tests
+ Test building x86_64 images
+ Implement error handling on the client UI
+ Email notification
+ Enhanced UI (dynamic forms?)
+ Need to think more on how the images will be stored and ability to identify
  an existing image uniquely. Timestamp?
+ Implement a RESTful API to the build service