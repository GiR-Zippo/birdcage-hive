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

import time


address = "303"
m_version ="0.1"

class Exporter:
    def __init__(self, Master):
        self.Master = Master
        self.handler = None
        return

    def Load(self, handler):
        self.Master.CP.command("300 40 303 2", self)
        return

    def writeline(self, data):
        ex = data.split(" ")
        if (int(ex[0]) == int(address)):
            if (int(ex[1]) == 2):
                if (ex[2] == chr(1)):
                    f = open('/opt/Tesql/Server/Data/BanDB/BlackIps.txt', 'a')
                    f.write ("%s %s\r\n" %(ex[3], ex[6]))
                    f.close()
                if (ex[2] == chr(2)):
                    f = open('/opt/Tesql/Server/Data/BanDB/Rangeban.txt', 'a')
                    f.write ("%s %s %s\r\n" %(ex[3], ex[4], ex[5]))
                    f.close()
        return

class Master:
    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        return

    def start(self):
        self.Event()
        return

    def initfromdrone(self, args, handler):
        return

    def config(self, args, CP):
        return

    def command(self, args, handler):
        omv = args.split(" ")
        self.Exporter = Exporter(self)
        if omv[0] == address:
            if omv[1] == "1":
                self.Event()
                return
        if omv[0] == address:
            if omv[1] == "2":
                self.Exporter.writeline(omv)
                return
        return

    def stop(self):
        return True;

    def Event(self):
        f = open('/opt/Tesql/Server/Data/BanDB/BlackIps.txt', 'w')
        f.close()
        f = open('/opt/Tesql/Server/Data/BanDB/Rangeban.txt', 'w')
        f.close()
        self.Exporter = Exporter(self)
        self.Exporter.Load(None)
        self.CP.InsertEvent((86700 + time.time()), self)
        return

#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" "))
            if (args.split(" ")[0] == "load"):
                return address + " 1"
        except IndexError:
            print args
            return
