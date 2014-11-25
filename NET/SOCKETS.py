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
import socket
import select
import PACKET

import time
from collections import deque

INPORT = 5022
OUTPORT = 5022
DIFF = 0.005

#################################################
####              SOCKET-WRAPPER             ####
#################################################
class SockMain:
    def __init__(self, sock):
        self.sock = sock
        self.session = None
        self.outbuffer = deque()
        self.inbuffer = ''
        self.ip = ''
        return

    def Connect(self,ip):
        self.ip = ip
        self.sock.connect((ip, OUTPORT))
        return

    def SetSession(self, sess):
        self.session = sess
        return

    def Update(self):
        is_readable = [self.sock]
        is_writable = []
        is_error = []
        r, w, e = select.select(is_readable, is_writable, is_error, DIFF)
        if r or w:
            try:
                #build new packet
                pck = PACKET.Packet()
                #set header to calc size
                pck.SetHeader(self.sock.recv(4))
                if (pck.GetPacketSize() <= 0):
                    return False
                #read content
                pck.SetData(self.sock.recv(pck.GetPacketSize()))
                #und wech
                self.session.AddPacket(pck)
            except:
                return False
        return True

    def SendPacket(self, data):
        self.sock.send(data.GetPacketWithHeader())
        return

    def Close(self):
        self.sock.close()
        return

class SocketMgr(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.listener = SockMain(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.listener.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.sock.bind(("", INPORT))
        self.listener.sock.listen(1)
        self.Running = False
        self.SocketList = []
        self.Master = None
        return

    def SetMaster(self, Master):
        self.Master = Master
        return

    def ConnectTo(self, ip):
        try:
            tsock = SockMain(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            tsock.Connect(ip)
            self.SocketList.append((ip, tsock))
        except socket.error:
            return None
        return tsock

    def Listen(self):
        is_readable = [self.listener.sock]
        is_writable = []
        is_error = []
        r, w, e = select.select(is_readable, is_writable, is_error, DIFF)
        if r:
            0
            channel, info = self.listener.sock.accept()
            #print "connection from", info
            try:
                tsock = SockMain(channel)
                for self.tsess in self.Master.SessionMgr.SessionList:
                    if (self.tsess.IP == info[0]):
                        self.tsess.SetSocket(tsock)
                        self.SocketList.append((info[0], tsock))
            except:
                channel.close()
        return

    def stop(self):
        self.Running=False
        return

    def run(self):
        self.Running = True
        while self.Running == True:
            time.sleep(DIFF) #Take a nap :)
            for tsock in self.SocketList:
                if (tsock[1].Update() == False):
                    self.SocketList.remove(tsock)
            if(self.Running == True):
                self.Listen()

        self.listener.sock.shutdown(socket.SHUT_RDWR)
        self.listener.sock.close()
        for tsock in self.SocketList:
            tsock[1].sock.shutdown(socket.SHUT_RDWR)
            tsock[1].sock.close()

