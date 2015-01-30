# encoding: iso-8859-1

#
# Copyright (C) 20011-2014 by Booksize
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

import threading
import CRYPT.CRYPT
import SOCKETS
import SESSIONS


class SocketApi(threading.Thread):
    def __init__(self, cp):
        threading.Thread.__init__(self)
        self.SocketMgr = SOCKETS.SocketMgr()
        self.SocketMgr.SetMaster(self)
        self.SessionMgr = SESSIONS.SessionMgr()
        self.CP = cp
        self.Digest = None
        return

    def run(self):
        self.SessionMgr.start()
        self.SocketMgr.start()
        return

    def stop(self):
        self.SocketMgr.stop()
        self.SessionMgr.stop()
        return

    def config(self, args):
        self.Digest = CRYPT.CRYPT.Crypt().SHA256(self.CP.Drone_Name).hexdigest()
        self.cip = ""
        self.cdrone = ""
        self.cinadress = ""
        self.coutadress = ""

        temp = args.split("\n")
        for item in temp:
            if not item:
                continue
            if item[0] == "#":
                continue
            if "Drone-Name" in item:
                self.cdrone = item.split("=")[1].strip()
            if "Drone-IP" in item:
                self.cip = item.split("=")[1].strip()
            if "Drone-Enable-InAdress" in item:
                self.cinadress = item.split("=")[1].strip()
            if "Drone-Enable-OutAdress" in item:
                self.coutadress = item.split("=")[1].strip()
            if "Drone-Insert" in item:
                print "Adding Drone: " + self.cdrone
                self.SessionMgr.NewSession(self.cdrone, self.cip, self.cinadress, self.coutadress, self.CP, self)
                self.cip = ""
                self.cdrone = ""
                self.cinadress = ""
                self.coutadress = ""

    def writeline(self, data):
        self.SessionMgr.writeline(data)
        return

    def writeTo(self, drone, data):
        #for i in self.SessionMgr.SessionList:

        return

    def GetSessionList(self):
        return self.SessionMgr.SessionList