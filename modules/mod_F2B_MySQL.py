# BaseAddress
import urllib2, CP, time, threading, sys, os, commands
address = "310"
m_version ="0.1"


class Master:
    CP #Pointer for the CP
    def __init__(self,CP):
        ## Set the CP
        self.CP         = CP
        self.lastline   = 0
        self.marked_ip  = []
        self.procIP     = []
        self.threeshold = 5
        self.duration   = 0 #Seconds or 0 = perma
        self.errorlog   = "/var/log/syslog"

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
        self.CP.InsertEvent((5 + time.time()), self) 
        return

    def checkip(self, ip):
        if ip in self.procIP:
            return;

        for self.item in self.marked_ip:
            if self.item[0] == ip:
                self.item[1] = int(self.item[1]) + 1
                if self.item[1] >= self.threeshold:
                    if self.duration == 0:
                        self.CP.command("300 1 " + self.item[0] + " 0 0 0", "NULL")
                    else:
                        self.CP.command("300 1 " + self.item[0] + " 0 " + str(int((time.time() + int(self.duration)))) + "0", "NULL")
                    self.procIP.append(self.item[0])
                    self.marked_ip.remove(self.item)
                return;

        self.marked_ip.append([ip, "1"])
        return;

    def refreshList(self):
        self.in_file = open(self.errorlog,"r")
        self.text = self.in_file.readlines()
        self.in_file.close()

        if len(self.text) < self.lastline:
            self.lastline = 0;

        for self.row in range(self.lastline, len(self.text)):
            if "Access denied for user " in self.text[self.row]: 
                self.ip = self.text[self.row].strip().split("@")
                self.checkip(self.ip[1].split("'")[1])

        self.lastline = self.row + 1
        return