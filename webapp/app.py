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

# This application uses code from the sample application shipped
# with Flask-FAS integration plugin:
# http://git.fedorahosted.org/cgit/flask-fas.git/tree/sample_app.py

# Original code notice:

# Flask-FAS - A Flask extension for authorizing users with FAS
# Primary maintainer: Ian Weller <ianweller@fedoraproject.org>
#
# Copyright (c) 2012, Red Hat, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# * Neither the name of the Red Hat, Inc. nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# This is a sample application. In addition to using Flask-FAS, it uses
# Flask-WTF (WTForms) to handle the login form. Use of Flask-WTF is highly
# recommended because of its CSRF checking.

from flask import Flask, request, render_template
from flask.ext import wtf
from flask.ext.fas import FAS
from functools import wraps
from multiprocessing import Process
import flask

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
app.config['SECRET_KEY'] = os.urandom(24)
app.config['FAS_CHECK_CERT'] = False
app.config['FAS_HTTPS_REQUIRED'] = False


# Set up FAS extension
fas = FAS(app)

# A basic login form
class LoginForm(wtf.Form):
    username = wtf.TextField('Username', [wtf.validators.Required()])
    password = wtf.PasswordField('Password', [wtf.validators.Required()])

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Your application should probably do some checking to make sure the URL
    # given in the next request argument is sane. (For example, having next set
    # to the login page will cause a redirect loop.) Some more information:
    # http://flask.pocoo.org/snippets/62/
    if 'next' in flask.request.args:
        next_url = flask.request.args['next']
    else:
        next_url = flask.url_for('index')
    # If user is already logged in, return them to where they were last
    if flask.g.fas_user:
        return flask.redirect(next_url)
    # Init login form
    form = LoginForm()
    # Init template
    data = render_template('login.html')
    data += ('<p>Log into the <a href="{{ config.FAS_BASE_URL }}">'
             'Fedora Accounts System</a>:')
    # If this is POST, process the form
    if form.validate_on_submit():
        if fas.login(form.username.data, form.password.data):
            # Login successful, return
            return flask.redirect(next_url)
        else:
            # Login unsuccessful
            data += '<p style="color:red">Invalid login</p>'
    data += """
<form action="" method="POST">
{% for field in [form.username, form.password] %}
    <p>{{ field.label }}: {{ field|safe }}</p>
    {% if field.errors %}
        <ul style="color:red">
        {% for error in field.errors %}
            <li>{{ error }}</li>
        {% endfor %}
        </ul>
    {% endif %}
{% endfor %}
<input type="submit" value="Log in">
{{ form.csrf_token }}
</form>"""
    return flask.render_template_string(data, form=form)


@app.route('/logout')
def logout():
    if flask.g.fas_user:
        fas.logout()
    return flask.redirect(flask.url_for('index'))


# This is a decorator we can use with any HTTP method (except login, obviously)
# to require a login. In this application it is only used with claplusone and
# secret. If the user is not logged in, it will redirect them to the login form.
# http://flask.pocoo.org/docs/patterns/viewdecorators/#login-required-decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None:
            return flask.redirect(flask.url_for('login',
                                                next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function

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
@login_required
def build():
    form = BuildConfigForm(request.form)
    if request.method == 'POST':
        BuildConfigForm.pre_validate(form, request)

        if form.validate():
            parse_data(app, request, form)
            #Fire the build job in a separate process
            buildjob=Process(target=delegate)
            buildjob.start()
            
            return 'Request Registered. Await Email Notification. Go <a href="/">Home</a>.'

    return render_template('ui.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

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
    return render_template('index.html')

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
