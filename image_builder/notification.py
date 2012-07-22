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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  
# 02110-1301, USA.

# Contact: Amit Saha <amitksaha@fedoraproject.org>
#          http://fedoraproject.org/wiki/User:Amitksaha

import smtplib
import logging
import ConfigParser

class Notification:
    def __init__(self):

        self.logger = logging.getLogger('imagebuilder')
        self.getconfig()

    def getconfig(self):
        config = ConfigParser.SafeConfigParser()
        config.read('smtp.conf')
        self.SMTP_SERVER = config.get('SMTP', 'server')
        self.SMTP_PORT = config.get('SMTP', 'port')
        self.sender = config.get('SMTP', 'login')
        self.password = config.get('SMTP', 'password')

    def send_email(self, recipient, headers, message):
        
        session = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT)
 
        session.ehlo()
        session.starttls()
        session.ehlo

        try:
            session.login(self.sender, self.password)
            session.sendmail(self.sender, recipient, headers + "\r\n\r\n" + message)
        except Exception as e:
            self.logger.error('Error sending email. Email notification not possible')
        else:
            self.logger.info('Image Build notification sent')
            session.quit()     

        
        
