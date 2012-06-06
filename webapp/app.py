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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
#          http://fedoraproject.org/wiki/User:Amitksaha


from wtforms import Form, SelectField, TextField,BooleanField, validators
from werkzeug import secure_filename
from flask import Flask,request,render_template
from flaskext.wtf import FileField
from multiprocessing import Process
import os
import shutil
import ConfigParser
import subprocess

class BuildConfigForm(Form):
    image=SelectField(u'Image Type', choices=[('boot', 'boot'), \
                        ('dvd', 'DVD'), ('live', 'Live Image')])
    arch=SelectField(u'Architecture', choices=[('i686', 'i686'), \
                        ('x86_64', 'x86_64')])
    staging=TextField(u'Staging FTP URL (No ftp://)')
    email = TextField('Email Address', [validators.Length(min=6, max=35)])
    product=SelectField(u'Product',choices=[('fedora','Fedora')])
    release=SelectField(u'Release',choices=[('17','17'),('18','18'),('rawhide','rawhide')])
    version=SelectField(u'Version',choices=[('17','17'),('18','18'),('rawhide','rawhide')])
    baseurl = TextField(u'Base URL of the repository')
    proxy = TextField(u'Proxy URL')
    gold = BooleanField(u'Gold?')
    updates=BooleanField(u'Enable updates?')
    updates_testing=BooleanField(u'Enable updates-testing?')
    nvr_boot=TextField('NVR of extra packages (Multiple separate by ;)')
    bid_boot=TextField('BuildIDs of extra packages (Multiple separate by ;)')
    nvr_dvd=TextField('NVR of extra packages(Multiple separate by ;)')
    bid_dvd=TextField('BuildIDs of extra packages(Multiple separate by ;)')
    flavor=TextField(u'Flavor')
    config_dvd=FileField('Kickstart file')
    remoteconfig_dvd=TextField(u'Kickstart file URL')
    config_live=FileField('Kickstart file')
    remoteconfig_live=TextField(u'Kickstart file URL')
    nvr_live=TextField('NVR of extra packages(Multiple separate by ;)')
    bid_live=TextField('BuildIDs of extra packages (Multiple separate by ;)')
    label=TextField(u'Label')
    title=TextField(u'Title')


def parse_data(request,form):
    
    # config file creation
    with open('data/config/imagebuild.conf', 'w') as f:
        f.write('[DEFAULT]\n')
        # Retrieve the data and create the config file
        image=form.image.data
        f.write('type={0:s}\n'.format(image))
        arch=form.arch.data
        f.write('arch={0:s}\n'.format(arch))
        staging=form.staging.data
        f.write('staging={0:s}\n'.format(staging))
        email=form.email.data
        f.write('email={0:s}\n'.format(email))
        

        if image == 'boot':
            f.write('[boot]\n')
            product=form.product.data
            f.write('product={0:s}\n'.format(product))
            release=form.release.data
            f.write('release={0:s}\n'.format(release))
            version=form.version.data
            f.write('version={0:s}\n'.format(version))
            baseurl=form.baseurl.data
            gold=form.gold.data
            if form.updates.data:
                updates='1'
            else:
                updates='0'
            f.write('updates={0:s}\n'.format(updates))

            if form.updates_testing.data:
                updates_testing='1'
            else:
                updates_testing='0'
            f.write('updates-testing={0:s}\n'.format(updates_testing))

            if arch=='i686':
                arch='i386'

            # form the repository URL's
            if gold:
                main_url='{0:s}/releases/{1:s}/Everything/{2:s}/os'.format(baseurl,release,arch)
            else:
                main_url='{0:s}/development/{1:s}/{2:s}/os}'.format(baseurl,release,arch)

            updates_url='{0:s}/updates/{1:s}/{2:s}'.format(baseurl,release,arch)
            updates_testing_url='{0:s}/updates/testing/{1:s}/{2:s}'.format(baseurl,release,arch)


            
            #form the mirror url's
            mirror_main_url = 'https://mirrors.fedoraproject.org/metalink?repo=fedora-{0:s}&arch={1:s}'.format(release,arch)
            mirror_updates_url = 'https://mirrors.fedoraproject.org/metalink?repo=updates-released-f{0:s}&arch={1:s}'.format(release,arch)   
            mirror_updates_testing_url = 'https://mirrors.fedoraproject.org/metalink?repo=updates-testing-f{0:s}&arch={1:s}'.format(release,arch)   


            #write the URLs
            f.write('{0:s}_url={1:s}\n'.format(release,main_url))
            f.write('{0:s}_mirror={1:s}\n'.format(release,mirror_main_url))
            if updates=='1':
                f.write('{0:s}-updates_url={1:s}\n'.format(release,updates_url))
                f.write('{0:s}-updates_mirror={1:s}\n'.format(release,mirror_updates_url))
            if updates_testing=='1':
                f.write('{0:s}-updates-testing_url={1:s}\n'.format(release,updates_testing_url))
                f.write('{0:s}-updates-testing_mirror={1:s}\n'.format(release,mirror_updates_testing_url))
            

            proxy=form.proxy.data
            f.write('proxy={0:s}\n'.format(proxy))
            
            nvr=form.nvr_boot.data
            f.write('nvr={0:s}\n'.format(nvr))

            bid=form.bid_boot.data
            f.write('bid={0:s}\n'.format(bid))                     

            # TODO: Better idea?
            # defaults
            outdir='/tmp/lorax_op'
            workdir='/tmp/lorax_work'
            f.write('outdir={0:s}\n'.format(outdir))                     
            f.write('workdir={0:s}\n'.format(workdir))                     
        
        if image=='dvd':

            f.write('[dvd]\n')
            product=form.product.data
            f.write('name={0:s}\n'.format(product))
            version=form.version.data
            f.write('version={0:s}\n'.format(version))
            flavor=form.flavor.data
            f.write('flavor={0:s}\n'.format(flavor))

            nvr=form.nvr_dvd.data
            f.write('nvr={0:s}\n'.format(nvr))

            bid=form.bid_dvd.data
            f.write('bid={0:s}\n'.format(bid))                     

            # TODO: Better idea?
            # defaults
            workdir='/tmp/pungi_work'
            destdir='/tmp/pungi_op'
            cachedir='/var/cache/pungi'
            bugurl='http://bugzilla.redhat.com'
            nosource='1'
            sourceisos='0'
            stage='all'
            force='1'

            f.write('destdir={0:s}\n'.format(destdir))                     
            f.write('cachedir={0:s}\n'.format(cachedir))                     
            f.write('workdir={0:s}\n'.format(workdir))                   
            f.write('bugurl={0:s}\n'.format(bugurl))                    
            f.write('nosource={0:s}\n'.format(nosource))                  
            f.write('sourceisos={0:s}\n'.format(sourceisos))                     
            f.write('force={0:s}\n'.format(force))                     
            f.write('stage={0:s}\n'.format(stage))                     
            
            file = request.files['config_dvd']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            f.write('config=/etc/imagebuild/{0:s}\n'.format(filename))


        if image=='live':

            f.write('[live]\n')
            label=form.label.data
            f.write('label={0:s}\n'.format(label))
            title=form.title.data
            f.write('title={0:s}\n'.format(title))
            product=form.product.data
            f.write('product={0:s}\n'.format(product))
            release=form.release.data
            f.write('releasever={0:s}\n'.format(release))

            nvr=form.nvr_live.data
            f.write('nvr={0:s}\n'.format(nvr))

            bid=form.bid_live.data
            f.write('bid={0:s}\n'.format(bid))                     

            # TODO: Better idea?
            # defaults
            tmpdir='/tmp/live_work'
            cachedir='/var/cache/liveimage'
            logfile='/tmp/liveimage.log'

            f.write('tmpdir={0:s}\n'.format(tmpdir))                     
            f.write('cachedir={0:s}\n'.format(cachedir))                     
            f.write('logfile={0:s}\n'.format(logfile))                     
            
            file = request.files['config_live']
            filename = secure_filename(file.filename)
            print os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            f.write('config=/etc/imagebuild/{0:s}\n'.format(filename))

    
    return

# delegate build job to Celery using configuration information
# from nodes.conf
def delegate():
    # Read the data/config/imagebuild.conf file
    # to find the architecture of the image sought
    config = ConfigParser.SafeConfigParser()
    config.read('data/config/imagebuild.conf')
    arch = config.get('DEFAULT','arch')
    
    #find an appropriate build node from nodes.conf
    #based on the arch
    config = ConfigParser.SafeConfigParser()
    config.read('nodes.conf')
    broker_url = config.get(arch,'broker_url')

    #now create the celeryconfig.py using this broker_url
    with open('celeryconfig.py','w') as f:
        f.write('BROKER_URL = {0:s}\n'.format(broker_url))
        f.write('CELERY_RESULT_BACKEND = "amqp"\n')
    
    # task delegation
    from celery.execute import send_task
    from tasks import build
    import json
    
    buildconf=open('data/config/imagebuild.conf')
    buildconf_str=json.dumps(buildconf.read())
    buildconf.close()
        
    # retrieve the kickstart file name if any    
    config = ConfigParser.RawConfigParser()
    config.read('data/config/imagebuild.conf')
    if config.has_section('dvd'):
        head,ks_fname = os.path.split(config.get('dvd','config'))
    else:
        if config.has_section('live'):
            head,ks_fname = os.path.split(config.get('live','config'))
        else:
            ks_fname = None

    if ks_fname:
        ks=open('data/kickstarts/{0:s}'.format(ks_fname))
        ksstr=json.dumps(ks.read())
        ks.close()

    #send task to celery woker(s)
    if ks_fname:
        build.apply_async(args=[buildconf_str,[ks_fname,ksstr]],serializer="json")
    else:
        build.apply_async(args=[buildconf_str,None],serializer="json")
    
    return


# Flask Application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/kickstarts/'

@app.route('/build', methods=['GET', 'POST'])
def register():
    form = BuildConfigForm(request.form)
    if request.method == 'POST' and form.validate():
        # create configuration files from the form submitted
        parse_data(request,form)

        #Fire the build job in a separate process
        buildjob=Process(target=delegate)
        buildjob.start()

        return 'Request Registered. You will recieve an email notification once your job is complete, or could not be completed. Go <a href="/build">Home</a>.'

    return render_template('ui.html', form=form)

@app.route("/")
def index():
    return "<center><h2>On-Demand Fedora Build Service</h2></center>"


if __name__ == "__main__":
    import sys
    sys.path.append('../image_builder')

    # cleanup data to start with and
    # create data/config and data/kickstarts
    # if not os.path.exists('data/config'):
    #     os.makedirs('/etc/imagebuild')
    # else:
    #     shutil.rmtree('data/config')
    #     os.makedirs('data/imagebuild')

    # start webapp
    app.run(host='0.0.0.0',debug=True)
