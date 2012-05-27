gsoc2012_fbs
============

Summary
-------

This is an in-progress snapshot of code to facilitate custom image building
for Fedora. First version of the code was written by my Google Summer of Code
project mentor: Tim Flink.

Project details: http://www.google-melange.com/gsoc/project/google/gsoc2012/amitsaha/24001

Contact: Amit Saha <amitksaha@fedoraproject.org>


Usage
-----
Dependencies: pylorax (http://git.fedorahosted.org/git/?p=lorax.git;a=tree), Koji and some more which I don't remember :-(

The user options are specified by a number of .conf files in the config/ directory. 

The file config/imagebuild.conf specifies the type of image to be built- Boot ISO, DVD or Live image. Only one of boot, dvd or live is allowed. The staging location is also specified here. This is the location where you want your image to be delivered. The specification should be of the form <hostname>:<location>. An email is sent once the image building is complete to the email address specified. (This is not yet implemented).

The file config/boot.conf specifies the options for creating the Boot ISO and the config/repoinfo.conf specifies the repositories to use for creating the same.

The file config/pungi.conf specifies the options for creating the DVD ISO. The kickstart file specified should be a 'ksflatten'ed KS file. Note that, you should just change the filename of the KS file and leave the /etc/imagebuild part intact.

The file config/live.conf specifies the options for creating the Live image. The kickstart file specified should be a 'ksflatten'ed KS file. Note that, you should just change the filename of the KS file and leave the /etc/imagebuild part intact.

Place your kickstart files in kickstarts/ directory 

Currently, extra packages may be specified via NVR and/or Build IDs in the relevant .conf files.

Once this is done, run
$ sudo python run_imagebuild.py