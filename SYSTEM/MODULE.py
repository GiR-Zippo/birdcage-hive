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

import sys
import os
import FILEIO


class MODULESYSTEM:
    def __init__(self, master):
        self.m_Master = master

        #Installed Mods
        # 0 = Root of Module
        # 1 = Module().Master()
        # 2 = Module().CLI_Dict()
        # 3 = Name
        # 4 = Module().WEB()
        self.m_Installed_Mods = []
        return

    def Initialize(self):
        sys.path.append("./MODS_ENABLED")

        #Module laden
        for _file in os.listdir("./MODS_ENABLED"):
            if _file.endswith(".py"):
                if _file == "__init__.py": #Der nicht
                    continue
                _file = _file.strip().replace(".py", "")
                self.m_Master.sLog.outString("Found Module: " + _file)
                handler = __import__(_file)

                #Woerterbuch suchen...
                try:
                    mod_cli = handler.CLI_Dict()
                except AttributeError:
                    mod_cli = None

                #WebDaten suchen
                try:
                    mod_web = handler.WEB()
                except AttributeError:
                    mod_web = None

                print _file
                self.m_Installed_Mods.append([handler, handler.Master(self.m_Master), mod_cli, _file, mod_web])
                self.m_Master.sLog.outString("Using Module:" + _file)
        return

    def ReadConfig(self, args):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            mMaster.config(args, self.m_Master)
        return

    def StartUp(self):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            mMaster.start()
        return

    def TerminateModule(self, module):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            if mName == module:
                if mMaster.stop():
                    self.m_Master.sLog.outString("Module " + mName + " stopped.")
                    return
        return

    def TerminateALLModules(self):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            if mMaster.stop():
                self.m_Master.sLog.outString("Stopped: " + mName)
                continue
        return

    def ReloadModule(self, args):
        _accessor = None
        _handler = None
        _mod_cli = None
        try:
            _accessor = args[1]
        except TypeError:
            self.m_Master.sLog.outCritical("Module not found.")
            return

        if _accessor.stop():
            self.m_Master.sLog.outString("Module " + args[3].strip() + " stopped.")

        _modname = args[3].strip()
        index = self.m_Installed_Mods.index(args)
        try:
            _accessor.join()
            _handler = reload(self.m_Installed_Mods[index][0])
        except AttributeError, RuntimeError:
            _handler = reload(self.m_Installed_Mods[index][0])

        del self.m_Installed_Mods[index]

        #Woerterbuch suchen...
        try:
            _mod_cli = _handler.CLI_Dict()
        except AttributeError:
            _mod_cli = "None"

        _args = FILEIO.FileIO().ReadLine("./CONFIGS/bird.conf")
        self.m_Installed_Mods.append([_handler, _handler.Master(self.m_Master), _mod_cli, _modname])

        _accessor = self.GetModulebyName(_modname)
        _accessor[1].config(_args, self.m_Master)
        _accessor[1].start()
        self.m_Master.sLog.outString("Module reloaded: " + self.m_Installed_Mods[self.m_Installed_Mods.index(_accessor)][3])
        return

    #Commands

    #List all Mods we are using
    def ListAllModules(self, handler):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            handler.writeline(mName)
        return

    #Helfer
    def GetInstalledMods(self):
        return self.m_Installed_Mods

    def GetModulebyName(self, name):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            if mName == name:
                return [mHandler, mMaster, mCLI, mName]
        return None

    def GetModulebyMaster(self, master):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            if mMaster == master:
                return [mHandler, mMaster, mCLI, mName, mWEB]
        return None

    def GetModulebyAddress(self, address):
        for mHandler, mMaster, mCLI, mName, mWEB in self.m_Installed_Mods:
            try:
                if mMaster.GetAddress() == address:
                    return [mHandler, mMaster, mCLI, mName, mWEB]
            except:
                pass
        return None