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

#Define our Console-Input-Thread
class InputFromConsole(threading.Thread):
    n_cli = False;
    n_cli_acc = None;

    def __init__(self):
        self.check=True
        threading.Thread.__init__(self)
        self.active_module = ""

        #Zum idend. woher die Anfrage kam
        self.ID = "CLI"

    def run(self):

        while self.check:
            if (InputFromConsole.n_cli == False):
                sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (27, 0, ""))
                var = raw_input(self.active_module + "/Command:")
                sys.stdout.flush()
                self.command(var)
            else:
                if(InputFromConsole.n_cli_acc.refresh() == False):
                    InputFromConsole.n_cli = False

    def stop(self):
        self.check = False

    # Convert Humanized Commands to Hive
    def command(self, args):
        if (args == ""):
            return;

        #default commands
        if args == "quit":
            if (InputFromConsole.n_cli == True):
                InputFromConsole.n_cli_acc.exit()

            CP.command("TP",self)
            self.writeline("terminating...")
            return

        #Activate our "new-style" Console
        if args == "menu":
            self.activate_n_cli()
            return

        if (self.internalCommands(args) == True and self.active_module  == ""):
            return

        if (self.active_module  == ""):
            self.writeline("Ya have to select a Module via use")
            return

        self.output = CP.GetDictionary(self.active_module, args)
        if (self.output):
            CP.command (self.output, self)

    #internalCommands
    def internalCommands(self,args):
        self.omv = args.split(" ")
        self.offset = 1
        if (self.omv[0] == "list"):
            try:
                if (self.omv[1] == "modules"):
                    self.out = "001 1";
                    CP.command(self.out,self)
                    return True
                elif (self.omv[1] == "drones"):
                    self.out = "001 7";
                    CP.command(self.out,self)
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
                CP.command(self.out,self)
                return True
            except IndexError:
                self.writeline("Ya have to type in a modulename")
                return True

        if (args.split(" ")[0] == "use"):
            try:
                self.active_module = "mod_" + args.split(" ")[1].strip()
                self.statusbar_n_cli("module", self.active_module)
                return True
            except IndexError:
                self.writeline("Ya have to select a Module via use")
                return True

        if (args.split(" ")[0] == "cli_test"):
            try:
                CP.command("001 8 " + args.split(" ")[1] + " "+  args.split(" ")[2], self)
                return True
            except IndexError:
                self.writeline("TestCommand");
                return True


    def activate_n_cli(self):
        InputFromConsole.n_cli_acc = __import__("N_CLI", globals(), locals(), [], -1).N_CLI()
        InputFromConsole.n_cli_acc.set_master(self)
        InputFromConsole.n_cli = True

    def statusbar_n_cli(self,item,args):
        if(InputFromConsole.n_cli == True):
            InputFromConsole.n_cli_acc.StatusBar(item,args)

    #write a line to our CLI
    def writeline(self,args):
        if (InputFromConsole.n_cli == True):
            InputFromConsole.n_cli_acc.writeline(args)
        else:
            print(args)
