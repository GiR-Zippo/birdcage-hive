import CP, time, threading, sys, os, commands

#Base-Address
#Please read the read.me in the root-dir
address = "200"
m_version ="0.1"


class Master:
    CP #Pointer for the CP
    def __init__(self,CP):
        ## Set the CP
        self.CP = CP

        #UNCOMMENT THIS IF YOU WAN'T TO USE EVENTS
        #self.timer = 60
        return

    def start(self):
        #UNCOMMENT THIS IF YOU WAN'T TO USE EVENTS
        #Instant Startup
        #self.Event()
        #Delayed Startup
        #self.CP.InsertEvent((int(self.timer) + time.time()), self) 

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
        #DO SOMETHING

        #SET TIMER TO 60 SEC
        #self.t = 60
        #self.CP.InsertEvent((int(self.t) + time.time()), self) 
        return
