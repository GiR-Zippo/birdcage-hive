import CP, time, threading, sys, os, commands
from collections import deque

# BaseAddress
address = "303"
m_version ="0.1"
LOCK = threading.Lock()

## define Checking-Thread
class Master(threading.Thread):
    check = True;
    CP #Pointer for the CP

    def __init__(self,CP):
        ## MaxCon
        self.max = 200
        
        ## Checkinterval
        self.interval = 10
        self.bantime = 300

        ## Set the CP
        self.CP = CP

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        return

    ##If any drones sends an init, this routine would be called
    def initfromdrone(self, args, handler):
        return

    def run(self):
        while Master.check:
            self.checkConnection()
            self.update()
            time.sleep(self.interval)

    def config(self, args, CP):
        Master.CP = CP
        self.fobject = open("./configs/mod_Deflater.conf", "r")
        for self.line in self.fobject:
            if (self.line.strip()):
                if (self.line.strip()[0] == "#"):
                    continue
                if (self.line.strip().find("Max =") != -1):
                    self.max = int(self.line.strip().replace(" ", "").split('=')[1])
                if (self.line.strip().find("Interval =") != -1):
                    self.interval = int(self.line.strip().replace(" ", "").split('=')[1])
                if (self.line.strip().find("BanTime =") != -1):
                    self.bantime = int(self.line.strip().replace(" ", "").split('=')[1])
        self.fobject.close()
        return

    def command(self,args, handler):
        return

    def checkConnection(self):
        self.p = os.popen("netstat -ntu | grep servers -v | grep Address -v | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr")
        self.str = self.p.read()
        self.p.close()
        for self.data in self.str.split("\n"):
            if (self.data.strip()):
                self.data = self.data[6:]
                self.data = self.data.split(" ")
                try:
                    self.con = self.data[0]
                    self.ip = self.data[1]
                    if (int(self.con) > int(self.max)):
                        self.CP.command("300 1 " + str(self.ip) + " " + str(self.con) + " " + str(int((time.time() + self.bantime))) + " 1", "NULL")
                except IndexError:
                    pass
        

    def update(self):
        return
    def stop(self):
        Master.check = False
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False
