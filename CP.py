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

# encoding: iso-8859-1
## The CommandProcessor

import threading
import signal

import FILEIO
import LOG
import NET.API
from SYSTEM.CONFIG import Config
from SYSTEM.EVENTS import Events
from SYSTEM.FIFO import Fifo
from SYSTEM.MODULE import MODULESYSTEM
from WEB.WEBSERVER import WebServer
LOCK = threading.Lock()

#################################################
####             ControlProcessor            ####
#################################################
class CP(object):
    _instance = None
    _lock = threading.Lock()    

    def signal_handler(self, signal, frame):
        self.sLog.outString("")
        self.sLog.outString("terminating...")
        self.command("TP", self)
        return

    def __init__(self):
        #Init für die helfenden Elfen
        self.m_buffer = Fifo()
        self.m_Events = Events()
        self.m_SockAPI = NET.API.SocketApi(self)
        self.m_Modules = MODULESYSTEM(self)

        self.m_WebServer = None

        #config laden
        self.configfile = "./CONFIGS/bird.conf"

        #signalhandler einbauen
        signal.signal(signal.SIGINT, self.signal_handler)

        #LogSystem braucht die Config sofort
        self.m_args = FILEIO.FileIO().ReadLine(self.configfile)
        self.sLog = LOG.sLog()
        self.sLog.config(self.m_args,self)

        #Der Name unserer Drone
        self.Drone_Name = ""

        #Module initialisieren
        self.InitMods()
        self.ReadConfig()
        self.StartUP()

    #Load, Register and Start mods
    def InitMods(self):
        #MainRoutines
        self.m_SockAPI.start()
        self.m_Events.start()

        self.Drone_Name = Config(self.configfile).GetItem("droneid")
        if Config(self.configfile).GetItem("Enable_WebServer") == "1":
            self.m_WebServer = WebServer(self)

        #UserMods
        self.m_Modules.Initialize()


    ## Read the config
    def ReadConfig(self):
        self.m_args = FILEIO.FileIO().ReadLine(self.configfile)
        self.m_SockAPI.config(self.m_args)

        ##send config to our mods
        #for item in self.installed_mods_master:
        self.m_Modules.ReadConfig(self.m_args)

    #Here we define our Startup-Setup
    def StartUP(self):
        self.m_SockAPI.writeline("002 2 " + self.Drone_Name)
        self.m_SockAPI.writeline("INIT")
        self.m_Modules.StartUp()
        if self.m_WebServer:
            self.m_WebServer.start()

    ## Threads and Mods stop here
    def StopMods(self):
        #StopEvents
        self.m_Events.stop()
        self.m_Modules.TerminateALLModules()
        if self.m_WebServer is not None:
            self.m_WebServer.stop()
        self.m_SockAPI.stop()
        self.sLog.outString("Bye.")

    #################################################
    ####                EVENTS                   ####
    #################################################
    def InsertEvent(self, e_time, handler):
        self.m_Events.Insert(e_time, handler)
        return

    ## Alter Drones
    def ToSocket(self, args):
        self.m_SockAPI.writeline(args)

    def ToDrone(self, name, args):
        self.m_SockAPI.writeTo(name, args)

    def ToLog(self, Logfilter, args):
        if Logfilter == "Info":
            self.sLog.outString(args)
        if Logfilter == "Debug":
            self.sLog.outDebug(args)
        if Logfilter == "Critical":
            self.sLog.outCritical(args)
        return

    #Put incomming cmds on buffer
    def command(self, args, handler):
        self.m_buffer.append(args, handler)

        #if LOCK.acquire(False): # Non-blocking -- return whether we got it
        #    LOCK.release()
        #else:
        #    self.sLog.outCritical("Couldn't get the lock. Maybe next time")

    def refresh(self):
        while self.m_buffer.hascontent():
            try:
                args, handler = self.m_buffer.pop()
            except TypeError:
                continue

            # Dummy Mode
            if handler is None:
                handler = self
                handler.ID = "NULL"

            if args == "TP":
                self.StopMods()
                return False

            ''' If we get a init from network '''
            try:
                if args.split(" ")[0] == "INIT":
                    for item in self.m_Modules.m_Installed_Mods:
                        item[1].initfromdrone(int(args.split(" ")[1]), handler)
                    return
            except IndexError:
                if args == "INIT":
                    ''' Send our Name '''
                    self.ToSocket("002 2 " + self.Drone_Name)
                    for item in self.m_Modules.m_Installed_Mods:
                        item[1].initfromdrone(0, handler)
                    return

            try:
                #Check if we've got an address instead of junk
                if int(args.split(" ")[0]) == 1:
                    self.Internal_Commands(args, handler)

                #module commandhandler
                for item in self.m_Modules.m_Installed_Mods:
                    if item[1] is not None:
                        item[1].command(args, handler)
            except ValueError:
                pass

        return

            #Im Notfall wieder einbauen
            #if LOCK.acquire(False): # Non-blocking -- return whether we got it
                #LOCK.release()
            #else:
                #self.sLog.outCritical("Couldn't get the lock. Maybe next time")

    ##############################################
    # Addressline 001 fuer den internen Gebrauch #
    ##############################################

    def Internal_Commands(self, args, handler):

        if args.split(" ")[1] == "1":
            self.m_Modules.ListAllModules(handler)

        #Stop module X
        if args.split(" ")[1] == "2":
            self.m_Modules.TerminateModule(args.split(" ")[2])

        #Reload and Start Module X
        if args.split(" ")[1] == "3":
            _out = self.GetModulebyName(args.split(" ")[2])
            self.m_Modules.ReloadModule(_out)
            return

        #Push mod X to da Hive
        if args.split(" ")[1] == "4":
            out = self.GetModulebyName(args.split(" ")[2])
            self.SendModule(out)
            return

        #recive Module from Hive
        if args.split(" ")[1] == "5":
            out = self.GetModulebyName(args.split(" ")[2])

            if out is None:
                return

            if float(args.split(" ")[3]) > float(out[0].m_version):
                _all = len(args.split(" ")[0]) + len(args.split(" ")[1]) + len(args.split(" ")[2]) + len(args.split(" ")[3]) + 4
                self.RecModule(out, args[_all:])

        #Push all mods to da Hive
        if args.split(" ")[1] == "6":
            for out in self.m_Modules.m_Installed_Mods:
                self.SendModule(out)

        #List all Authed and Connected Drones
        if args.split(" ")[1] == "7":
            for out in self.m_SockAPI.GetSessionList():
                handler.writeline(out.Name)

        #SendFile to Drone
        #Drone, Source, Target
        if args.split(" ")[1] == "8":
            FILEIO.FileIO(self).SendFile(args.split(" ")[3], args.split(" ")[4], args.split(" ")[2])

        #rec file
        #Flag, TargetName, Data
        if args.split(" ")[1] == "9":
            length = len(args.split(" ")[0]) + len(args.split(" ")[1]) + len(args.split(" ")[2]) + len(args.split(" ")[3]) + 4
            if int(args.split(" ")[2]) == 0:
                FILEIO.FileIO().WriteToFileSync(args.split(" ")[3], args[length:], "wb")
            elif int(args.split(" ")[2]) == 1:
                FILEIO.FileIO().WriteToFileSync(args.split(" ")[3], args[length:], "ab")
        #SubAddresse 10 liegt im Socket

    def SendModule(self, args):
        name = str(args[3])
        rev = args[0].m_version
        data = FILEIO.FileIO().ReadLine("./MODS_AVAILABLE/" + name + "/" + name + ".py")
        self.ToSocket("001 5 " + name + " " + str(rev) + " " + data)

    def RecModule(self, entry, args):
        name = "./MODS_AVAILABLE/" + str(entry[3]) + "/" + str(entry[3]) + ".py"
        try:
            FILEIO.FileIO().WriteToFileAsync(name, args, 'w')
            self.m_Modules.ReloadModule(entry)
            self.sLog.outString("Received newer Version of Module: " + name)
        except IOError:
            pass

    def GetDictionary(self, module, args):
        for out in self.m_Modules.m_Installed_Mods:
            if out[3] == module:
                try:
                    _dict = out[2].get(args)
                    if _dict:
                        return _dict
                except AttributeError:
                    self.sLog.outString("This Module has no Commands!", False)


    ##############################################
    #               API Routines                 #
    ##############################################

    def GetInstalledMods(self):
        return self.m_Modules.m_Installed_Mods

    def GetModulebyName(self, name):
        return self.m_Modules.GetModulebyName(name)

    def GetModulebyMaster(self, master):
        return self.m_Modules.GetModulebyMaster(master)

    def GetDroneName(self):
        return self.Drone_Name