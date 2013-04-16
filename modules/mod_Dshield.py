# encoding: iso-8859-1

#
# Copyright (C) 20011-2013 by Booksize
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

#Using the DROP-Table from Dshield.org
#http://feeds.dshield.org/top10-2.txt

# BaseAddress
import urllib2, CP, time, threading, sys, os, commands
address = "302"
m_version ="0.1"


class Master:
    CP #Pointer for the CP
    def __init__(self,CP):
        ## Set the CP
        self.CP = CP

    def start(self):
        self.Event()
        return

    def initfromdrone(self, args, handler):
        return

    def config(self, args, CP):
        Master.CP = CP;
        return

    def command(self,args,handler):
        return

    def stop(self):
        return True

    def Event(self):
        self.refreshList()
        self.CP.InsertEvent((86700 + time.time()), self)
        return

    def refreshList(self):
        urlStr = 'http://feeds.dshield.org/top10-2.txt'
        try:
          fileHandle = urllib2.urlopen(urlStr)
          str1 = fileHandle.read()
          fileHandle.close()
        except IOError:
          str1 = 'error!'

        offset = 0
        out = str1.split("\t")

        i=0
        for item in out:
          if (len(item) == 0):
            return
          if (len(item.split("\n")[-1])<>0):
            self.CP.command("300 1 " + item.split("\n")[-1] + " 0 " + str(int((time.time() + 86400))) + " 1", "NULL")
        return