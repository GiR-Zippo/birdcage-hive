# encoding: iso-8859-1
import threading
import socket
import select
import zlib
import string, StringIO,time
from collections import deque
from Crypto.Cipher import ARC4
from Crypto.Hash import SHA256

import binascii

INPORT = 5022
OUTPORT = 5022
DIFF = 0.05
#################################################
####      Decompressor for Input Stream      ####
#################################################
class ZipInputStream:

    def __init__(self, file):
        self.file = file
        self.__rewind()

    def __rewind(self):
        self.zip = zlib.decompressobj()
        self.pos = 0 # position in zipped stream
        self.offset = 0 # position in unzipped stream
        self.data = ""

    def __fill(self, bytes):
        if self.zip:
            # read until we have enough bytes in the buffer
            while not bytes or len(self.data) < bytes:
                self.file.seek(self.pos)
                data = self.file.read(16384)
                if not data:
                    self.data = self.data + self.zip.flush()
                    self.zip = None # no more data
                    break
                self.pos = self.pos + len(data)
                try:
                    self.data = self.data + self.zip.decompress(data)
                except:
                    return

    def seek(self, offset, whence=0):
        if whence == 0:
            position = offset
        elif whence == 1:
            position = self.offset + offset
        else:
            raise IOError, "Illegal argument"
        if position < self.offset:
            raise IOError, "Cannot seek backwards"

        # skip forward, in 16k blocks
        while position > self.offset:
            if not self.read(min(position - self.offset, 16384)):
                break

    def tell(self):
        return self.offset

    def read(self, bytes = 0):
        self.__fill(bytes)
        if bytes:
            data = self.data[:bytes]
            self.data = self.data[bytes:]
        else:
            data = self.data
            self.data = ""
        self.offset = self.offset + len(data)
        return data

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
        r, w, e = select.select(is_readable, is_writable, is_error, 0.05)
        if r or w:
            try:
                self.reqsize = self.sock.recv(4)
                self.reqsize = int((ord(self.reqsize[0]) *0x1000000) + (ord(self.reqsize[1]) *0x10000) + (ord(self.reqsize[2]) *0x100) + ord(self.reqsize[3]))
                if (self.reqsize <= 0):
                    return False
                self.inbuffer = self.sock.recv(self.reqsize)
                self.session.AddPacket(self.inbuffer)
            except:
                return False
        return True

    def SendPacket(self, data):
        self.size = len(data)
        self.data1 = 0xFF &(self.size>>24)
        self.data2 = 0xFF &(self.size>>16)
        self.data3 = 0xFF &(self.size>>8)
        self.data4 = 0xFF & self.size
        self.out = chr(self.data1)+ chr(self.data2) + chr(self.data3) + chr(self.data4) + data
        self.sock.send(self.out)
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
            self.tsock = SockMain(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            self.tsock.Connect(ip)
            self.SocketList.append((ip, self.tsock))
        except:
            return None
        return self.tsock

    def Listen(self):
        is_readable = [self.listener.sock]
        is_writable = []
        is_error = []
        r, w, e = select.select(is_readable, is_writable, is_error, 0.05)
        if r:
            channel, info = self.listener.sock.accept()
            #print "connection from", info
            try:
                self.tsock = SockMain(channel)
                for self.tsess in self.Master.SessionMgr.SessionList:
                    if (self.tsess.IP == info[0]):
                        self.tsess.SetSocket(self.tsock)
                        self.SocketList.append((info[0], self.tsock))
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
            for self.tsock in self.SocketList:
                if (self.tsock[1].Update() == False):
                    self.SocketList.remove(self.tsock)
            if(self.Running == True):
                self.Listen()

        self.listener.sock.shutdown(socket.SHUT_RDWR)
        self.listener.sock.close()
        for self.tsock in self.SocketList:
            self.tsock[1].sock.shutdown(socket.SHUT_RDWR)
            self.tsock[1].sock.close()

class Session:
    def __init__(self, Name, IP, In, Out, CP, Master):
        self.ID = "SCK";
        self.Name = Name.strip()
        self.IP = IP
        self.online = False

        #Encryption
        self.sha = SHA256.new()
        self.sha.update(b'%s' % self.Name)
        self.digest = self.sha.hexdigest()

        #Handling for Restrictions
        self.EnInAdress = []
        if not (In == "0"):
            self.EnInAdress = In.split(",")
        self.EnOutAdress = []
        if not (Out == "0"):
            self.EnOutAdress = Out.split(",")
        self.cp = CP
        self.Master = Master
        self.sock = self.Master.SocketMgr.ConnectTo(self.IP)
        if(self.sock != None):
            self.sock.SetSession(self)

        #I/O Buffer
        self.InPacketList =  deque()
        self.OutPacketList = deque()
        return

    def SetSocket(self, sock):
        self.sock = sock
        self.sock.SetSession(self)
        return

    def Update(self):
        while (len(self.InPacketList) > 0):
            self.inc = self.InPacketList.popleft()
            self.cp.command(self.inc,self)

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
        self.cryp = ARC4.new(self.Master.Digest)
        self.data = zlib.compress(data)
        self.data = self.cryp.encrypt(self.data)
        #print "OUT: " + data
        if (self.EnOutAdress):
            if not (data.split(" ")[0].strip() ==  "INIT"):
                self.adchk = data.split(" ")[0].strip() + " " + data.split(" ")[1].strip()

                if not (self.adchk in self.EnOutAdress):
                    return
        self.OutPacketList.append(self.data)
        return

    def AddPacket(self, data):
        self.cryp = ARC4.new(self.digest)
        self.data = self.cryp.decrypt(data)
        self.data = ZipInputStream(StringIO.StringIO(self.data)).read()
        self.inc = self.data
        #print "IN: " + self.data
        #Check if this drone has restrictions
        if (self.EnInAdress):
            if not (self.inc.split(" ")[0].strip() == "INIT"):
                self.adchk = self.inc.split(" ")[0].strip() + " " + self.inc.split(" ")[1].strip()
                if not (self.adchk in self.EnInAdress):
                    return

        #Check for DroneName
        if (self.inc.split(" ")[0] ==  "002"):
            if (self.inc.split(" ")[1] ==  "2"):
                self.tName = self.inc.split(" ")[2]
                if (self.tName == self.Name.strip()):
                    print "Drone %s online." % self.Name
                    self.online = True
                return;
        self.InPacketList.append(self.data)
        return

class SessionMgr(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.Running = False
        self.SessionList = []
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

class Listener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.SocketMgr = SocketMgr()
        self.SocketMgr.SetMaster(self)
        self.SessionMgr = SessionMgr()
        self.CP = None
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

    def config(self, args, cp):
        self.CP = cp
        self.h = SHA256.new()
        self.h.update(b'%s' % self.CP.Drone_Name)
        self.Digest = self.h.hexdigest()
        self.cip = ""
        self.cdrone = ""
        self.cinadress = ""
        self.coutadress = ""

        self.temp = args.split("\n")
        for self.item in self.temp:
            if not (self.item):
                continue
            if (self.item[0] == "#"):
                continue
            if ("Drone-Name" in self.item):
                self.cdrone = self.item.split("=")[1].strip()
            if ("Drone-IP" in self.item):
                self.cip = self.item.split("=")[1].strip()
            if ("Drone-Enable-InAdress" in self.item):
                self.cinadress = self.item.split("=")[1].strip()
            if ("Drone-Enable-OutAdress" in self.item):
                self.coutadress = self.item.split("=")[1].strip()
            if ("Drone-Insert" in self.item):
                print "Adding Drone: " + self.cdrone
                self.SessionMgr.AppendSession(Session(self.cdrone, self.cip, self.cinadress, self.coutadress, self.CP, self))
                self.cip = ""
                self.cdrone = ""
                self.cinadress = ""
                self.coutadress = ""