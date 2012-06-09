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

class Transfer:

    def __init__(self,staging,imgloc):
        self.staging=staging
        self.imgloc=imgloc

    #ftp
    def transfer_ftp(self):

        from ftplib import FTP
        ftp=FTP(staging)

        # anonymous
        ftp.login()

        # assumes a 'pub' directory where the files are to be 
        # put
        ftp.cwd('pub')
        
        # transfer the files
        for img in imgloc:
            print 'Transfering {0:s} to {1:s}'.format(img,staging)
            with open(img) as f:
                # extract the filename from 'img'
                head,fname=os.path.split(img)
                ftp.storbinary('STOR {0:s}'.format(fname),f)

        # end ftp session
        ftp.close()
        return

    # email notification
    # TBD
    def notify():
        pass



