# On-Demand Fedora Build Service

On-Demand build service seeks to build Live and installation images for developers, testers and consumers of Fedora Linux. During the testing of Fedora releases, test images are often useful as smoke tests before full TC/RC composes, as baselines for specific test days or for automated installation testing in AutoQA. The idea is to make an on-demand Web-based build service which users/developers can use to make custom Fedora based distributions so that command-line wrangling can be minimized. More details on the Google melange page.

[Google Summer of Code'2012 project] (http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001)


## DOCUMENTATION

+ Read the documentation on [Read the docs] (http://on-demand-fedora-build-service.readthedocs.org/en/latest/)
+ Download a PDF of the latest documentation [here] (http://readthedocs.org/projects/on-demand-fedora-build-service/downloads/)


##STATUS

+ Web Forms, REST API and Command Line interface for build job submission
+ Can use multiple worker nodes to build images
+ Copies the image(s) to the designated FTP location/local file system specified in staging
+ HTTP based Build Job monitoring, Email Notifications


## TODO

+ Unit tests
+ Validating the imagebuild.conf syntax/semantics for the CLI interfaces

## GOOD TO HAVE

+ User sessions
+ Enhanced UI (dynamic forms/CSS/etc)
+ Implement error handling on the client UI (Available; but server side for now)
