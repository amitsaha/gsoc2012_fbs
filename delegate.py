# reads the configuration files created
# from the user's specifications and delegates
# a build job to a build node

# As of now, single node only
# Modify the nodes.conf file appropriately
# to build x86_64 images (untested)

import ConfigParser
import shutil
import subprocess
import os

# Create mock data in data/config and data/kickstarts
def create_data():
    pass


if __name__=='__main__':

    # The web form handling code should create the
    # data files based on user specifications

    # Create mock data if required
    create_data()


    # copy the config/ and kickstarts/ to 
    # image_builder directory
    # first delete the previous config/ kickstarts/
    if os.path.exists('image_builder/config'):
        shutil.rmtree('image_builder/config')

    if os.path.exists('image_builder/kickstarts'):
        shutil.rmtree('image_builder/kickstarts')

    shutil.copytree('data/config','image_builder/config')
    shutil.copytree('data/kickstarts','image_builder/kickstarts')
    
    # then read the data/config/imagebuild.conf file
    # to find the architecture of the image sought
    config = ConfigParser.SafeConfigParser()
    config.read('data/config/imagebuild.conf')
    arch = config.get('DEFAULT','arch')
    
    #find an appropriate build node from nodes.conf
    #based on the arch
    config = ConfigParser.SafeConfigParser()
    config.read('nodes.conf')
    hostname = config.get(arch,'hostname')
    workdir = config.get(arch,'workdir')
  
    #tar up the image_builder directory
    shutil.make_archive('image_builder','tar','.' ,'image_builder')
    
    # scp it to the workdir there
   
    args=['image_builder.tar','{0:s}:{1:s}'.format(hostname,workdir)]
    # setup 'scp' and fire
    process_call = ['scp']
    process_call.extend(args)
    print 'Transfering source to {0:s}:{1:s}'.format(hostname,workdir)
    subprocess.call(process_call)   
    
    # Now, remotely untar the archive at the remote location
    args= [hostname, 'cd {0:s};tar xf'.format(os.path.abspath(workdir)), '{0:s}/image_builder.tar'.format(os.path.abspath(workdir))]
    process_call=['ssh']
    process_call.extend(args)
    print 'Extracting the source code at the remote location'
    subprocess.call(process_call)

    # remotely execute the run_imagebuild.py script there
    args=[hostname,'cd {0:s}/image_builder;python'.format(os.path.abspath(workdir)),'{0:s}/image_builder/run_imagebuild.py'.format(os.path.abspath(workdir))]
    process_call=['ssh']
    process_call.extend(args)
    
    print 'Executing build Job on the remote node'    
    subprocess.call(process_call)

    print 'Check your specified Staging area for the built image'
