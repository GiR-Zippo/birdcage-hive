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

#Using the DROP-Table from Spamhaus
#http://www.spamhaus.org/drop/drop.txt

# BaseAddress
import urllib2, cookielib, CP, time, threading, sys, os, commands
address = "301"
m_version ="0.1"
firewall_flag = "6"

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
        return True;

    def Event(self):
        self.refreshList()
        self.CP.InsertEvent((86700 + time.time()), self)
        return

    def refreshList(self):
	hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
	       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
	       'Accept-Encoding': 'none',
	       'Accept-Language': 'en-US,en;q=0.8',
	       'Connection': 'keep-alive'}

	site = 'http://www.spamhaus.org/drop/drop.txt'
        urlStr = urllib2.Request(site, headers=hdr)
        try:
          fileHandle = urllib2.urlopen(urlStr)
          self.instring = fileHandle.readlines()
          fileHandle.close()
        except IOError:
          print 'Spamhaus error!'
          return

        offset = 4
        for self.item in self.instring:
            if self.item.strip()[0] != ";":
                #print self.item.split(";")[0].strip()
                self.CP.command("300 1 " + self.item.split(";")[0].strip() + " 0 " + str(int((time.time() + 86400))) + " " + firewall_flag + " SPAMHAUS-EXPORT", "NULL")
        return
