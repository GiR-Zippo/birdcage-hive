# encoding: iso-8859-1

#
# Copyright (C) 20011-2012 by Booksize
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

import CP
# Our Console

import commands
import os
import sys
import threading
import time

## define Checking-Thread
class Master(threading.Thread):
    check = True;
    interval = 1;
    CP #Pointer for the CP

    def __init__(self,CP):
        ## Set the CP
        self.CP = CP

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        self.active_module = ""
        #Zum idend. woher die Anfrage kam
        self.ID = "CLI"
        return

    ##If any drones sends an init, this routine would be called
    def initfromdrone(self, args, handler):
        return

    def run(self):
        while self.check:
            sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (27, 0, ""))
            var = raw_input(self.active_module + "/Command:")
            sys.stdout.flush()
            self.clicommand(var)

    def clicommand(self, args):
        if (args == ""):
            return;

        #default commands
        if args == "quit":
            self.CP.command("TP",self)
            self.writeline("terminating...")
            self.check = False
            return

        #Activate our "new-style" Console
        if (self.internalCommands(args) == True and self.active_module  == ""):
            return

        if (self.active_module  == ""):
            self.writeline("Ya have to select a Module via use")
            return

        self.output = self.CP.GetDictionary(self.active_module, args)
        if (self.output):
            self.CP.command (self.output, self)
        return

    #internalCommands
    def internalCommands(self,args):
        self.omv = args.split(" ")
        self.offset = 1
        if (self.omv[0] == "list"):
            try:
                if (self.omv[1] == "modules"):
                    self.out = "001 1";
                    self.CP.command(self.out,self)
                    return True
                elif (self.omv[1] == "drones"):
                    self.out = "001 7";
                    self.CP.command(self.out,self)
                    return True
            except IndexError:
                self.writeline("List what? Would ya like to see the modules?")
                return True

        if (self.omv[0].strip() == "module"):
            self.out = ""
            try:
                if (self.omv[1].strip() == "stop"):
                    self.out = "001 2 " + self.omv[2];
                elif (self.omv[1].strip() == "start"):
                    self.out = "001 3 " + self.omv[2] ;
                elif (self.omv[1].strip() == "export"):
                    self.out = "001 4 " + self.omv[2];
                elif (self.omv[1].strip() == "export-all"):
                    self.out = "001 6"
                self.CP.command(self.out,self)
                return True
            except IndexError:
                self.writeline("Ya have to type in a modulename")
                return True

        if (args.split(" ")[0] == "use"):
            try:
                self.active_module = "mod_" + args.split(" ")[1].strip()
                return True
            except IndexError:
                self.writeline("Ya have to select a Module via use")
                return True

        if (args.split(" ")[0] == "cli_test"):
            try:
                self.CP.command("001 8 " + args.split(" ")[1] + " "+  args.split(" ")[2], self)
                return True
            except IndexError:
                self.writeline("TestCommand");
                return True

    #write a line to our CLI
    def writeline(self,args):
        print(args)
        return

    def config(self, args, CP):
        return

    def command(self,args, handler):
        return

    def update(self):
        return
    def stop(self):
        Master.check = False
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False
