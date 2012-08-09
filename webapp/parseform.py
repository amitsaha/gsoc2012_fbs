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

import os
from werkzeug import secure_filename

def parse_data(app, request, form):
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
                main_url = '{0:s}/releases/{1:s}/Everything/{2:s}/os'.format(baseurl, release, arch)
            else:
                main_url = '{0:s}/development/{1:s}/{2:s}/os'.format(baseurl, release, arch)

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

            # If KS uploaded
            file = request.files['config_dvd']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                f.write('config=data/kickstarts/{0:s}\n'.format(filename))
            else:
                # If KS URL specified
                ksurl = form.remoteconfig_dvd.data
                f.write('config={0:s}\n'.format(ksurl))          
                
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
            # If KS uploaded
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                f.write('config=data/kickstarts/{0:s}\n'.format(filename))

            # If KS URL specified
            else:
                ksurl = form.remoteconfig_live.data
                f.write('config={0:s}\n'.format(ksurl))          
    
    return
