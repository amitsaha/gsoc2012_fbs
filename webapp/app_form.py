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
from flaskext.wtf import FileField

class BuildConfigForm(Form):

    image=SelectField(u'Image Type', choices=[('boot', 'boot'), \
                        ('dvd', 'DVD'), ('live', 'Live Image')])
    arch=SelectField(u'Architecture', choices=[('i686', 'i686'), \
                        ('x86_64', 'x86_64')])
    staging=TextField(u'Staging FTP URL (No ftp://)', [validators.required()])
    email = TextField('Email Address', [validators.Email()])
    product=SelectField(u'Product',choices=[('Fedora','Fedora')])
    release=SelectField(u'Release',choices=[('17','17'),('rawhide','rawhide')])
    boot_version=TextField(u'Version', [validators.required()])
    baseurl = TextField(u'Base URL of the repository',[validators.required()])
    proxy = TextField(u'Proxy URL')
    gold = BooleanField(u'Gold?')
    updates=BooleanField(u'Enable updates?')
    updates_testing=BooleanField(u'Enable updates-testing?')
    nvr_boot=TextField('NVR of extra packages (Multiple separate by ;)')
    bid_boot=TextField('BuildIDs of extra packages (Multiple separate by ;)')
    nvr_dvd=TextField('NVR of extra packages(Multiple separate by ;)')
    bid_dvd=TextField('BuildIDs of extra packages(Multiple separate by ;)')
    flavor=TextField(u'Flavor',[validators.Required()])
    config_dvd=FileField('Kickstart file')
    remoteconfig_dvd=TextField(u'Kickstart file URL (http/ftp)', [validators.Required()])
    config_live=FileField('Kickstart file')
    remoteconfig_live=TextField(u'Kickstart file URL (http/ftp)', [validators.Required()])
    nvr_live=TextField('NVR of extra packages(Multiple separate by ;)')
    bid_live=TextField('BuildIDs of extra packages (Multiple separate by ;)')
    label=TextField(u'Label',[validators.Required()])
    title=TextField(u'Title',[validators.Required()])

    @classmethod
    def pre_validate(self,form,request):
        if form.image.data == 'boot':
            form.config_dvd.validators = []
            form.remoteconfig_dvd.validators = []
            form.config_live.validators = []
            form.remoteconfig_live.validators = []
        
        if form.image.data == 'live':
            if request.files['config_live']:
                form.remoteconfig_live.validators = []
            
            form.boot_version.validators = []
            form.remoteconfig_dvd.validators = []

        if form.image.data == 'dvd':
            if request.files['config_dvd']:
                form.remoteconfig_dvd.validators = []
            
            form.boot_version.validators = []
            form.remoteconfig_live.validators = []

        if form.image.data == 'boot' or form.image.data == 'live':
            form.flavor.validators = []

        if form.image.data == 'boot' or form.image.data == 'dvd':
            form.title.validators = []
            form.label.validators = []
        
        if form.image.data == 'dvd' or form.image.data == 'live':
            form.baseurl.validators = []          
