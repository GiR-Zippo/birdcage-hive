import socket
import select
import time
import sys
import CP, time, threading, os, commands, FILEIO
from collections import deque

# BaseAddress
address = "200"
m_version ="0.1"
LOCK = threading.Lock()

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things

delay = 0.0001

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception, e:
            print e
            return False

class TheServer(threading.Thread):
    def __init__(self, host, port, forward_to_ip, forward_to_port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)
        self.forward_to_ip = forward_to_ip
        self.forward_to_port = forward_to_port
        self.inputready = None
        self.running = True
        self.buffer_size = 4096
        self.input_list = []
        self.channel = {}
        threading.Thread.__init__(self)
        return

    def run(self):
        self.input_list.append(self.server)
        while self.running == True:
            time.sleep(delay)
            self.ss = select.select
            self.inputready, outputready, exceptready = self.ss(self.input_list, [], [], 2)
            for self.s in self.inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                try:
                    self.data = self.s.recv(self.buffer_size)
                except:
                    self.data = ""

                if len(self.data) == 0:
                    self.on_close()
                else:
                    self.on_recv()

    def Stop(self):
        self.running = False
        return

    def on_accept(self):
        self.forward = Forward().start(self.forward_to_ip, self.forward_to_port)
        self.clientsock, self.clientaddr = self.server.accept()
        if self.forward:
            self.input_list.append(self.clientsock)
            self.input_list.append(self.forward)
            self.channel[self.clientsock] = self.forward
            self.channel[self.forward] = self.clientsock
        else:
            print "Can't establish connection with remote server.",
            print "Closing connection with client side",  self.clientaddr
            self.clientsock.close()

    def on_close(self):
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        self.out = self.channel[self.s]
        # close the connection with client
        self.channel[self.out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[self.out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.data
        self.channel[self.s].send(data)

#The FIFO-Buffer for incomming commands / unblocking the addressbus
class Fifo:
    def __init__(self):
        self.first_a= deque()
        self.first_b= deque()

    def append(self,data,handler):
        self.first_a.append(data)
        self.first_b.append(handler)

    def pop(self):
        try:
            return self.first_a.popleft(), self.first_b.popleft()
        except (IndexError):
            pass

    def hascontent(self):
        if (len(self.first_a) > 0):
            return True
        return False

## define Checking-Thread
class Master(threading.Thread):
    check = True;
    interval = 1;
    CP #Pointer for the CP

    def __init__(self,CP): 
        ## Set the CP
        self.CP = CP

        ## Setup the Buffer
        self.buffer = Fifo()
        self.server = []

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        return

    def addroute(self, rName, rParam):
        # Iza:9090 -> Fuu:9099 => 127.0.0.1:77
        self.data = rParam.split("->")
        for self.t in xrange(0, len(self.data), 2):
            self.src = self.data[self.t].strip().split(":")
            self.dest = self.data[self.t+1].strip().split(":")
            self.server.append([rName, TheServer(self.src[0], int(self.src[1]), self.dest[0], int(self.dest[1]))])
        return

    ##If any drones sends an init, this routine would be called
    def initfromdrone(self, args, handler):
        return

    def run(self):
        #while Master.check:
        for self.routes in self.server:
            self.routes[1].start()
        return

    def config(self, args, CP):
        self.m_args = FILEIO.FileIO().ReadLine("./configs/mod_Routing.conf")
        self.temp = self.m_args.split("\n")
        self.Name = ""
        self.Route = ""

        for self.r_item in self.temp:
            try:
                if self.r_item[0] == "#":
                    continue
            except IndexError:
                continue

            self.out = self.r_item.split("=")
            i=0
            for item in self.out:
                i=i+1
                if item.strip() == "Name":
                    self.Name = self.out[i].strip()
                if item.strip() == "Route":
                    self.Route = self.out[i].strip()
                if item.strip() == "End":
                    self.addroute(self.Name, self.Route)
        return

    def command(self,args, handler):
        self.buffer.append(args,handler)
        return

    def update(self):
        while (self.buffer.hascontent() == True):
            args, handler = self.buffer.pop()
            omv = args.split(" ")
            if omv[0] == address:
                if omv[1] == "1":
                    handler.writeline ("HELLO WORLD!")
        return

    def stop(self):
        Master.check = False
        for self.s in self.server:
            self.s[1].Stop()
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False



#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" ")) - 1
            if (args.split(" ")[0] == "test"):
                return "200 1"
        except IndexError:
            return

#########################################
############# Commands ##################
#########################################

# 200 1 = Testcommand