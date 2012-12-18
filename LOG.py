# encoding: iso-8859-1

#
# Copyright (C) 20011-2012 by Booksize
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys, os, commands, threading, time

class sLog: #(object):
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        return

    def outCritical(self, args):
        self.WriteLine(" [CRITICAL] ", args)

    def outLog(self, args):
        self.WriteLine(" [INFO] ", args)

    def WriteLine(self,ct, args):
        self.file = open("Hive.log", 'a')
        self.file.write(str(time.strftime("%Y-%m-%d %H:%M"))+ ct + args + "\n")
        self.file.close()