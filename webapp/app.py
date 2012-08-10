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

from flask import Flask, request, render_template
from multiprocessing import Process
import os
import shutil
import ConfigParser
import json

from image_builder.util import Utilities
from image_builder.notification import Notification
from app_form import BuildConfigForm
from parseform import parse_data

# Flask Application
app = Flask(__name__)

# cleanup data to start with and
# create data/config and data/kickstarts
if not os.path.exists('data/config'):
    os.makedirs('data/config')
else:
    shutil.rmtree('data/config')
    os.makedirs('data/config')

if not os.path.exists('data/kickstarts'):
    os.makedirs('data/kickstarts')
else:
    shutil.rmtree('data/kickstarts')
    os.makedirs('data/kickstarts')
    
app.config['UPLOAD_FOLDER'] = 'data/kickstarts/'

# Entry point for the Web application
@app.route('/build', methods=['GET', 'POST'])
def build():
    form = BuildConfigForm(request.form)
    if request.method == 'POST':
        BuildConfigForm.pre_validate(form, request)

        if form.validate():
            parse_data(app, request, form)
            #Fire the build job in a separate process
            buildjob=Process(target=delegate)
            buildjob.start()
            
            return 'Request Registered. You will recieve an email notification once your job is complete, or could not be completed. Go <a href="/build">Home</a>.'

    return render_template('ui.html', form=form)

# Restful Interface
@app.route("/rest", methods=['GET','POST'])
def rest():
    import json
    if request.method == 'POST':
        if request.headers['Content-Type'] == 'application/json':
            # Create data/imagebuild.conf and KS file, if applicable
            # from the Request 
            configstr = json.loads(request.json['config'])
            with open('data/config/imagebuild.conf','w') as f:
                f.write(configstr)

            ksfname = json.loads(json.dumps(request.json['ksfname']))
            if ksfname:
                if not ksfname.startswith(('http','ftp')):
                    ksstr = json.loads(request.json['ks'])
                    with open('data/kickstarts/{0:s}'.format(ksfname),'w') as f:
                        f.write(ksstr)

        #Fire the build job in a separate process
            buildjob=Process(target=delegate)
            buildjob.start()
    
            return json.dumps('Request Registered. You will recieve an email notification once your job is complete, or could not be completed.')
        else:
            return json.dumps('Request must be passed as a JSON encoded string')

    if request.method == 'GET':
        return "<p>Rest API to On-Demand Fedora Build Service</p>"


@app.route("/")
def index():
    return "<center><h2>On-Demand Fedora Build Service</h2><p>Go to the <a href='/build'>Web Interface</a> or browse the code on <a href='https://github.com/amitsaha/gsoc2012_fbs'>GitHub</a></a></center>"


# delegate build job to Celery using configuration information
# from nodes.conf
def delegate():
    # Read the data/config/imagebuild.conf file
    # to find the architecture of the image sought

    util = Utilities()
    buildconfig = util.get_dict('data/config/imagebuild.conf')

    arch = buildconfig['default']['arch']
    #find an appropriate build node from nodes.conf
    #based on the arch
    config = ConfigParser.SafeConfigParser()
    config.read('nodes.conf')
    broker_url = config.get(arch,'broker_url')

    #now create the celeryconfig.py using this broker_url
    with open('celeryconfig.py','w') as f:
        f.write('BROKER_URL = {0:s}\n'.format(broker_url))
        f.write('CELERY_RESULT_BACKEND = "amqp"\n')
        f.write('\n')
    
    buildconfig_json = json.dumps(buildconfig)

    if not buildconfig['default']['type'] == 'boot':
        ksstr = util.get_kickstart(buildconfig)
    else:
        ksstr = None

    # celery task delegation
    from tasks import build

    try:
        release = buildconfig['default']['release']
        queue_name = 'fedora-{0:s}'.format(release)
        build.apply_async(args = [buildconfig_json, ksstr], queue = queue_name, serializer="json")
    except Exception as e:
        # if there is an error in submitting job to celery
        # we save this somewhere and retry (TODO)
        # for now, we just have an email error message
        # using config in smtp.py
        recipient = buildconfig['default']['email']
        subject = 'Your Image Build Request'
        message = 'Uh Oh. The image builders are having a bad day. Retry again in sometime.'

        headers = ["From: " + 'Fedora Build Service',
                   "Subject: " + subject,
                   "To: " + recipient,
                   "MIME-Version: 1.0",
                   "Content-Type: text/html"]
        headers = "\r\n".join(headers)

        notify = Notification()
        notify.send_email(recipient, headers, message)
        return 
    else:
        return

if __name__ == "__main__":

    # start webapp
    app.run(host='0.0.0.0',debug=True)
