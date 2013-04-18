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

import sys, os, commands, threading, time

class sLog: #(object):
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.console_critical = False
        self.console_debug = False
        self.utime = str(time.strftime("%Y-%m-%d %H:%M"))
        self.logfolder = "./"
        return

    def config(self, args, CP):
        self.temp = args.split("\n")
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
                if item.strip() == "LOG-Critical":
                    if self.out[i].strip() == "1":
                        self.console_critical = True
                if item.strip() == "LOG-Debug":
                    if self.out[i].strip() == "1":
                        self.console_debug = True
                if item.strip() == "LogDir":
                    self.logfolder = self.out[i].strip().replace('"', "")

    def outString(self, args, toFile = True):
            self.WriteLine(" [INFO] ", args)
            print args
            return

    def outCritical(self, args, toFile = True):
        if (toFile == True):
            self.WriteLine(" [CRITICAL] ", args)
        if self.console_critical == True:
            print args
        return

    def outDebug(self, args, toFile = True):
        if (toFile == True):
            self.WriteLine(" [DEBUG] ", args)
        if self.console_debug == True:
            print args
        return

    def WriteLine(self,ct, args):
        self.file = open(self.logfolder + self.utime + "-Hive.log", 'a')
        self.file.write(str(time.strftime("%Y-%m-%d %H:%M"))+ ct + args + "\n")
        self.file.close()