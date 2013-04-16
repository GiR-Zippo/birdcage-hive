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

import SocketServer

import socket
import select

import threading
import socket
import zlib
import string, StringIO,time
from collections import deque

OutPort = 5022 #Change Socket to 5022
InPort  = 5022

#Decompressor for Input Stream
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
                self.data = self.data + self.zip.decompress(data)

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


class Drone:
    def __init__(self,IP,CP):
        self.cp = CP;
        self.ip = IP;
        self.ID = "SCK";
        self.Name = "";
        self.in_IP = deque();
        self.in_Data = deque();
        self.incomming_ip = "";
        self.out_Data = deque();
        return

    def Buffer_In(self,ip,data):
        self.in_IP.append(ip);
        self.in_Data.append(data);
        return

    def Get_Buffer_In(self):
        try:
            return self.in_IP.popleft(), self.in_Data.popleft();
        except IndexError:
            pass

    def Buffer_Out(self, data):
        self.out_Data.append(data);

    def Get_Buffer_Out(self):
        try:
            return self.out_Data.popleft();
        except IndexError:
            pass

    #Recive Datas
    def recv_Data(self,ip,data):
        self.Buffer_In(ip, data);
        return;

    #Popout Queue
    def Update(self):
        self.SendPacket()
        self.output = self.Get_Buffer_In();
        if (self.output == None):
            return;

        #self.incomming_ip = self.output[0];
        self.data = self.output[1];

        self.inc = ZipInputStream(StringIO.StringIO(self.data)).read();
        #Check for DroneName
        if (self.inc.split(" ")[0] ==  "001"):
            if (self.inc.split(" ")[1] ==  "10"):
                self.Name = self.inc.split(" ")[2];
                DroneUpdater.KnownDrones_Name[DroneUpdater.KnownDrones.index(self.ip)] = self.Name #Temporary
                return;

        self.cp.command(self.inc,self);
        return;

    def SendPacket(self):
        self.output = self.Get_Buffer_Out();
        if (self.output == None):
            return;

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.sendto(zlib.compress(self.output) , (self.ip, OutPort))
        except socket.error:
            pass
        self.sock.close()

    def writeline(self,args):
       self.Buffer_Out(args)

#Updater der Sessions, bis ich ne Alternative hab
class DroneUpdater(threading.Thread):
    KnownDrones = [];      #DroneIP for ID
    KnownDrones_Name = []; #DroneName
    KnownDrones_Acc = [];  #Accesssor
    Runnable = True;
    CP = None
    def __init__(self, CP):
        threading.Thread.__init__(self);
        DroneUpdater.CP = CP

    def run(self):
        while (DroneUpdater.Runnable == True):
            time.sleep(0.01) #Take a nap :)
            for self.item in DroneUpdater.KnownDrones_Acc:
                self.item.Update();

    def stop(self):
        DroneUpdater.Runnable = False;

    def writeTo(self,Name, args):
        self.drone = DroneUpdater.KnownDrones_Acc[DroneUpdater.KnownDrones_Name.index(Name)]
        self.drone.writeline(args)

    def writeline(self,args):
        for self.item in DroneUpdater.KnownDrones_Acc:
            self.item.writeline(args)

#Helper
class UDP_Listener(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        #socket = self.request[1]

        try:
            self.index = DroneUpdater.KnownDrones.index(self.client_address[0])
            if (self.index > -1):
                DroneUpdater.KnownDrones_Acc[self.index].recv_Data(self.client_address[0],data)
        except (ValueError):
            pass

#Our Listener
class Listener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        HOST, PORT = "0.0.0.0", InPort
        self.server = SocketServer.UDPServer((HOST, PORT), UDP_Listener)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def config(self, args, cp):
        self.temp = args.split("\n")
        for str in self.temp:
            Listener.CP = cp
            out = str.split("=")
            i=0
            for item in out:
                i=i+1
                if item.strip() == "drones":
                    t_ip = out[i].split(",")
                    for item in t_ip:
                        print "adding Drone IP: " + item.strip()
                        DroneUpdater.KnownDrones.append(item.strip())
                        DroneUpdater.KnownDrones_Name.append(" ")
                        DroneUpdater.KnownDrones_Acc.append(Drone(item.strip(), cp))
