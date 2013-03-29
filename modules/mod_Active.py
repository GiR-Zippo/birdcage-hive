import CP, time, threading, sys, os, commands
from collections import deque

# BaseAddress
address = "200"
m_version ="0.1"
LOCK = threading.Lock()

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

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        return

    ##If any drones sends an init, this routine would be called
    def initfromdrone(self, args, handler):
        return

    def run(self):
        while Master.check:
            self.update()
            time.sleep(0.5)

    def config(self, args, CP):
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