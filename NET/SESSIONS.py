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
import time
from collections import deque

import CRYPT
import PACKET

DIFF = 0.005

class Session:
    def __init__(self, Name, IP, In, Out, CP, Master):
        self.cp = CP
        self.Master = Master
        self.ID = "SCK"
        self.Name = Name.strip()  #drone Name
        self.IP = IP              #drone IP
        self.Social = []          #Drones known by this Drone
        self.online = False
        self.fastlane = []

        #Encryption
        self.digest = CRYPT.CRYPT.Crypt().SHA256(self.Name).hexdigest()
        self.inpbk = CRYPT.CRYPT.Crypt().PBKDF2(self.digest, self.digest, 16)
        self.outpbk = CRYPT.CRYPT.Crypt().PBKDF2(self.Master.Digest, self.Master.Digest, 16)

        #Handling for Restrictions
        self.EnInAdress = []
        if not (In == "0"):
            self.EnInAdress = In.split(",")
        self.EnOutAdress = []
        if not (Out == "0"):
            self.EnOutAdress = Out.split(",")
        self.sock = self.Master.SocketMgr.ConnectTo(self.IP)
        if(self.sock != None):
            self.sock.SetSession(self)

        #I/O Buffer
        self.InPacketList =  deque()
        self.OutPacketList = deque()
        return

    def AddFastLane(self, address, module):
        for flane in self.fastlane:
            if flane[0] == address:
                return
        self.fastlane.append([address, module])
        return

    def CheckForFastLane(self, data):
        addy = data.GetData().split(" ")[0]
        for fast in self.fastlane:
            if fast[0] == addy:
                fast[1].FastResponse(data.GetData(), self)
                return True
        return False

    def RemoveFromFastLane(self, address):
        for fast in self.fastlane:
            if fast[0] == address:
                self.fastlane.remove(fast)
                return
        return

    def SetSocket(self, sock):
        self.sock = sock
        self.sock.SetSession(self)
        return

    def Update(self):
        while (len(self.InPacketList) > 0):
            self.inc = self.InPacketList.popleft()
            if (self.CheckForFastLane(self.inc) == False):
                self.cp.command(self.inc.GetData(),self)

        while (len(self.OutPacketList) > 0):
            self.out = self.OutPacketList.popleft()
            try:
                self.sock.SendPacket(self.out)
            except:
                self.sock = None
        return

    def writeline(self, data):
        self.SendPacket(data)
        return

    def SendPacket(self, data):
        pck = PACKET.Packet()
        pck.AppendString(data)
        pck.Encrypt(self.Master.Digest, self.outpbk)
        print "OUT: " + data

        if (self.EnOutAdress):
            if not (data.split(" ")[0].strip() ==  "INIT"):
                adchk = data.split(" ")[0].strip() + " " + data.split(" ")[1].strip()

                if not (adchk in self.EnOutAdress):
                    return

        self.OutPacketList.append(pck)
        return

    def AddPacket(self, pck):
        #decrypt Packet
        pck.Decrypt(self.digest, self.inpbk)
        #get decrypted content
        inc = pck.GetData()
        print "IN: " + inc

        #Check if this drone has restrictions
        if (self.EnInAdress):
            if not (inc.split(" ")[0].strip() == "INIT"):
                adchk = inc.split(" ")[0].strip() + " " + inc.split(" ")[1].strip()
                if not (adchk in self.EnInAdress):
                    return

        #Check for DroneName and known Drones
        if (inc.split(" ")[0] ==  "002"):
            #if (self.inc.split(" ")[1] ==  "1"):
            #    self.Social.append(inc.split(" ")[2])

            if (inc.split(" ")[1] ==  "2"):
                tName = inc.split(" ")[2]
                if (tName == self.Name.strip()):
                    print "Drone %s online." % self.Name
                    self.online = True
                return
        self.InPacketList.append(pck)
        print self.Social
        return

class SessionMgr(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.Running = False
        self.SessionList = []
        return

    def NewSession(self, cdrone, cip, cinadress, coutadress, CP, Master):
        sess = Session(cdrone, cip, cinadress, coutadress, CP, Master)
        self.AppendSession(sess)
        return

    def AppendSession(self, sess):
        self.SessionList.append(sess)
        return

    def run(self):
        self.Running = True
        while self.Running:
            time.sleep(DIFF)
            for self.sess in self.SessionList:
                self.sess.Update()
        return

    def stop(self):
        self.Running = False
        return

    def writeline(self, data):
        for self.sess in self.SessionList:
            self.sess.SendPacket(data)
