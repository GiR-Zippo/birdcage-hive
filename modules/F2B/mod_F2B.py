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

import urllib2, CP, time, threading, sys, os, commands, re
address = "0000" #NONE
m_version ="0.1"
LOCK = threading.Lock()
firewall_flag = '5'

class FileChecker:
    def __init__(self, CP, logfile):
        self.CP         = CP
        self.seek       = 0
        self.filesize   = 0
        self.marked_ip  = []

        self.errorlog   = logfile
        self.errreg     = []
        self.ignex      = []
        return

    def insertFilter(self, regex, count, position, duration, flag, name):
        self.errreg.append([regex.upper(), position, count, duration, flag, name])
        return

    def insertIgnorex(self, ignore):
        self.ignex.append(ignore.upper())
        return

    def checkip(self, ip, count, duration, flag, name):
        if (int(count) == 0):
            if (int(duration) == 0):
                Master.CP.command("300 1 " + ip + " 0 0 " + flag + " " + name , "NULL")
            else:
                Master.CP.command("300 1 " + ip + " 0 " + str(int((time.time() + int(duration)))) + " " + flag + " " + name, "NULL")
            return

        for self.ip, self.count in self.marked_ip:
            if (self.ip == ip):
                if (int(count) > int(self.count)):
                    self.marked_ip[self.marked_ip.index([self.ip, self.count])] = [self.ip, (self.count + 1)]
                    return
                if (int(self.count) == int(count)):
                    if (int(self.duration) == 0):
                        Master.CP.command("300 1 " + self.ip + " 0 0 " + flag + " " + name, "NULL")
                        self.marked_ip[self.marked_ip.index([self.ip, self.count])] = [self.ip, (self.count + 1)]
                    else:
                        Master.CP.command("300 1 " + self.ip + " 0 " + str(int((time.time() + int(duration)))) + " " + flag + " " + name, "NULL")
                        del self.marked_ip[self.marked_ip.index([self.ip, (self.count)])]
                return

        self.marked_ip.append([ip, 1])
        return

    def refresh(self):
        #Dateigroesse ermitteln und ggf. den Seek resetten
        file_size = os.path.getsize(self.errorlog)
        if (file_size < self.filesize):
            self.seek = 0
        self.filesize = file_size

        self.fobj = open(self.errorlog, "r")
        self.fobj.seek(self.seek)
        for self.line in self.fobj:
            self.line = self.line.strip().upper()

            for self.ignorex in self.ignex:
                if self.ignorex in self.line:
                    break
            else:
                for self.regex, self.position, self.count, self.duration, flag, name in self.errreg:
                    if self.regex in self.line:
                        if (Master.LogDebug):
                            self.CP.ToLog("Info", self.line)
                        try:
                            self.fip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', self.line)[int(self.position)]
                            self.checkip(self.fip, self.count, self.duration, flag, name)
                        except IndexError:
                            pass

        self.seek = self.fobj.tell()
        self.fobj.close()
        return

class Master(threading.Thread):
    check = True
    CP #Pointer for the CP
    LogDebug = False

    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        self.Filter = []
        threading.Thread.__init__(self)

    def initfromdrone(self, args, handler):
        return

    def config(self, args, CP):
        Master.CP = CP

        self.fname = ""
        self.btime = 0
        self.flag = 0
        self.count = 0
        self.IPPosition = 0

        self.fobject = open("./configs/mod_F2B.conf", "r")
        for self.line in self.fobject:
            if (self.line.strip()):
                if (self.line.strip()[0] == "#"):
                    continue
                if (self.line.strip().find("LogDebug =") != -1):
                    if (int(self.line.strip().replace(" ", "").split('=')[1]) == 1):
                        Master.LogDebug = True
                if (self.line.strip().find("FilterName =") != -1):
                    self.fname = self.line.strip().split('"')[1]
                if (self.line.strip().find("File =") != -1):
                    self.SetFilter (self.fname, self.line.strip().split('"')[1])
                if (self.line.strip().find("Bantime") != -1):
                    self.btime = self.line.strip().replace(" ", "").split('=')[1]
                if (self.line.strip().find("Flag") != -1):
                    self.flag = self.line.strip().replace(" ", "").split('=')[1]
                if (self.line.strip().find("IPPosition") != -1):
                    self.IPPosition = self.line.strip().replace(" ", "").split('=')[1]
                if (self.line.strip().find("Count") != -1):
                    self.count = self.line.strip().replace(" ", "").split('=')[1]
                if (self.line.strip().find("Regex =") != -1):
                    self.AppendRule(self.fname, self.line.strip().split('"')[1], self.count, self.IPPosition, self.btime, self.flag)
                if (self.line.strip().find("Ignorex =") != -1):
                    self.AppendIgnRule(self.fname, self.line.strip().split('"')[1])
        self.fobject.close()
        return

    def SetFilter(self, name, file):
        for self.Name, self.Class in self.Filter:
            if (self.Name == name):
                return
        self.newC = FileChecker(self.CP, file)
        self.Filter.append([name, self.newC])
        return

    def AppendRule(self, name, regex, count, position, duration, flag):
        #print 'Name: %s \nRegEx: "%s" \nCount: %s \nPos: %s \nDuration: %s\n' % (name, regex, count, position, duration)
        for self.Name, self.Class in self.Filter:
            if (self.Name == name):
                self.Class.insertFilter(regex, count, position, duration, flag, name)
        return

    def AppendIgnRule(self, name, ignorex):
        for self.Name, self.Class in self.Filter:
            if (self.Name == name):
                self.Class.insertIgnorex(ignorex)
        return

    def command(self,args,handler):
        return

    def stop(self):
        Master.check = False
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False

    def run(self):
        while Master.check:
            for self.Name, self.Class in self.Filter:
                self.Class.refresh()
            time.sleep(3)