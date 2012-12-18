#Using the DROP-Table from Dshield.org
#http://feeds.dshield.org/top10-2.txt

# BaseAddress
import urllib2, CP, time, threading, sys, os, commands
address = "302"
m_version ="0.1"


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
        return
    
    def Event(self):
        self.refreshList()
        self.CP.InsertEvent((86700 + time.time()), self) 
        return
    
    def refreshList(self):
        urlStr = 'http://feeds.dshield.org/top10-2.txt'
        try:
          fileHandle = urllib2.urlopen(urlStr)
          str1 = fileHandle.read()
          fileHandle.close()
        except IOError:
          str1 = 'error!'

        offset = 0
        out = str1.split("\t")

        i=0
        for item in out:
          if (len(item) == 0):
            return
          if (len(item.split("\n")[-1])<>0):
            self.CP.command("300 1 " + item.split("\n")[-1] + " 0 " + str(int((time.time() + 86400))) + " 1", "NULL")
        return