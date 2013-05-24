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

import time
# encoding: iso-8859-1
## The CommandProcessor

import SOCKS, FILEIO, LOG
import sys, os, commands, threading
import signal
from collections import deque

LOCK = threading.Lock()

#################################################
####                EVENTS                   ####
#################################################
class Events(threading.Thread):
    def __init__(self):
        self.container = []
        self.check = True
        threading.Thread.__init__(self)
        return

    def Insert(self, eTime, eClass):
        self.container.append([eTime, eClass])
        return

    def Execute(self):
        for self.eTime, self.eClass in self.container:
            if (float(self.eTime) <= float(time.time())):
                self.eClass.Event()
                del self.container[self.container.index([self.eTime, self.eClass])]

    def run(self):
        while self.check:
            #print self.container
            self.Execute()
            time.sleep(0.5)
        return

    def stop(self):
        self.check = False
        return True

#################################################
####    FIFO-Buffer for incomming commands   ####
#################################################
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

#################################################
####             ControlProcessor            ####
#################################################
class CP(object):
    _instance = None
    _lock = threading.Lock()    

    def signal_handler(self, signal, frame):
        self.sLog.outString("");
        self.sLog.outString("terminating...")
        self.command("TP",self) 
        return
    def __init__(self):
        self.buffer = Fifo()
        self.configfile= "./configs/bird.conf"

        signal.signal(signal.SIGINT, self.signal_handler)

        #LogSystem braucht die Config sofort
        self.m_args = FILEIO.FileIO().ReadLine(self.configfile)
        self.sLog = LOG.sLog()
        self.sLog.config(self.m_args,self)

        #Installed Mods
        # 0 = Root of Module 
        # 1 = Module().Master()
        # 2 = Module().CLI_Dict()
        # 3 = Name
        self.installed_mods = []

        #EventSystem
        self.m_Events = Events()

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
        self.m_Events.start()

        #UserMods
        self.m_args = FILEIO.FileIO().ReadLine(self.configfile)

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
                        self.sLog.outString("Loading Modules: " + item.strip())
                        self.handler = __import__(item.strip())

                        #Woerterbuch suchen...
                        try:
                            self.mod_cli = self.handler.CLI_Dict()
                        except AttributeError:
                            self.mod_cli = "None"

                        self.installed_mods.append([self.handler,self.handler.Master(self), self.mod_cli, item.strip()])
                        self.sLog.outString("Using Module:" + item.strip())


    ## Read the config
    def ReadConfig(self):
        self.m_args = FILEIO.FileIO().ReadLine(self.configfile)
        self.m_Sock_listen.config(self.m_args,self)

        ##send config to our mods
        #for item in self.installed_mods_master:
        for item in self.installed_mods:
            item[1].config(self.m_args, self)

    #Here we define our Startup-Setup
    def StartUP(self):
        self.m_Sock_out.writeline("002 2 " + self.Drone_Name)
        self.m_Sock_out.writeline("INIT")

        for item in self.installed_mods:
            item[1].start();

    ## Threads and Mods stop here
    def StopMods(self):
        #StopEvents
        self.m_Events.stop()
        #UserMods
        for item in self.installed_mods:
            if item[1].stop() == True:
                self.sLog.outString("Stopped: " + item[3])
                continue

        self.m_Sock_listen.stop()
        self.m_Sock_out.stop()
        self.sLog.outString("Bye.")

    #################################################
    ####                EVENTS                   ####
    #################################################
    def InsertEvent(self,eTime,handler):
        self.m_Events.Insert(eTime, handler)
        return

    #Alert CLI
    def ToConsole(self,args):
        self.m_CLI.writeline(args)

    ## Alter Drones
    def ToSocket(self, args):
        self.m_Sock_out.writeline(args)

    def ToDrone(self, name, args):
        self.m_Sock_out.writeTo(name, args)

    def ToLog(self, Logfilter, args):
        if (Logfilter=="Info"):
            self.sLog.outString(args)
        if (Logfilter=="Debug"):
            self.sLog.outDebug(args)
        if (Logfilter=="Critical"):
            self.sLog.outCritical(args)
        return

    #Put incomming cmds on buffer
    def command(self, args,handler):
        self.buffer.append(args,handler)

        #if LOCK.acquire(False): # Non-blocking -- return whether we got it
        #    LOCK.release()
        #else:
        #    self.sLog.outCritical("Couldn't get the lock. Maybe next time")

    def refresh(self):
        while (self.buffer.hascontent() == True):
            try:
                args, handler = self.buffer.pop()
            except TypeError:
                continue

            # Dummy Mode
            if (handler == "NULL"):
                handler = self
                handler.ID = "NULL"

            if args == "TP":
                self.StopMods()
                return False

                #If we get a init from network
            if args == "INIT":
                self.ToSocket("002 2 " + self.Drone_Name) #Send our Name
                for item in self.installed_mods:
                    item[1].initfromdrone(args, handler)

            #Check if we've got an address instead of junk
            try:
                if (int(args.split(" ")[0]) == 1):
                    self.Internal_Commands(args, handler)

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

    def GetInstalledMods(self):
        return self.installed_mods

    def GetModulebyName(self, name):
        for self.out in self.installed_mods:
            if self.out[3] == name:
                return self.out
        return None

    def GetModulebyMaster(self, master):
        for self.out in self.installed_mods:
            if (self.out[1] == name):
                return self.out
        return None

    def GetDroneName(self):
        return self.Drone_Name

    ##############################################
    # Addressline 001 fuer den internen Gebrauch #
    ##############################################

    def Internal_Commands(self,args,handler):
        #List all Mods we are using
        if (args.split(" ")[1] == "1"):
            for self.out in self.installed_mods:
                 handler.writeline(self.out[3])

        #Stop module X
        if (args.split(" ")[1] == "2"):
            self.i=0
            for self.out in self.installed_mods:
                if (self.out[3] == args.split(" ")[2]):
                    if self.out[1].stop():
                        self.sLog.outString("Module " + out[3].strip() + " stopped.")
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
            for self.out in self.m_Sock.DroneUpdater.KnownDronesName:
                handler.writeline(self.out)

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
        try:
            self.accessor = args[1]
        except TypeError:
            self.sLog.outCritical("Module not found.")
            return

        if self.accessor.stop():
            self.sLog.outString("Module " + args[3].strip() + " stopped.")

        self.modname = args[3].strip()
        self.index = self.installed_mods.index(args)
        try:
            self.accessor.join()
            self.handler = reload(self.installed_mods[self.index][0])
        except AttributeError, RuntimeError:
            self.handler = reload(self.installed_mods[self.index][0])

        del self.installed_mods[self.index]

        #Woerterbuch suchen...
        try:
            self.mod_cli = self.handler.CLI_Dict()
        except AttributeError:
            self.mod_cli = "None"

        self.m_args = FILEIO.FileIO().ReadLine("./configs/bird.conf")
        self.installed_mods.append([self.handler,self.handler.Master(self), self.mod_cli, self.modname])

        self.accessor = self.GetModulebyName(self.modname)
        self.accessor[1].config(self.m_args, self)
        self.accessor[1].start();
        self.sLog.outString("Module reloaded: " + self.installed_mods[self.installed_mods.index(self.accessor)][3])
        return

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
            self.sLog.outString("Recived newer Version of Module: " + self.name)
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
                    self.sLog.outString("This Module has no Commands!", False)

            self.i=self.i+1

