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

''' One monitoring app per worker node'''

from flask import Flask
import os

app = Flask(__name__)

@app.route('/log/<path:logfile>')
def sendlog(logfile):
    if os.path.exists(os.path.abspath('/'+logfile)):
        lines = ''
        with open(os.path.abspath('/'+logfile),'r') as f:
            for line in f:
                lines = lines + '<p>' + line
        return lines
    else:
        return "Error. No Such Log file"

@app.route('/')
def index():
    return "You should not have been here"

#start
if __name__=='__main__':
    app.run('0.0.0.0', port = 5100)
