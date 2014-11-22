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

import threading
import sys, os, commands

class FileIO:
    CP = None
    def __init__(self, CP = None):
        FileIO.CP = CP
        return

    def ReadLine(self, FileName):
        self.file = open(FileName, "r")
        self.str = self.file.read()
        self.file.close()
        return self.str

    # FileName, Content, Mode
    # Sollte nur benutzt werden, wenn der Content nicht fortgesetzt wird
    def WriteToFileAsync(self,FileName, Content, args):
        FileWriter_Task(FileName, Content, args).start()

    def WriteToFileSync(self,FileName, Content, args):
        self.file = open(FileName, args)
        self.file.write(Content)
        self.file.close()

    # FileName, Drone
    def SendFile(self, SourceFileName, TargetName, Drone = None):
        FileTransfer_Task(SourceFileName, TargetName, Drone).start()


# HelperThread um Files zu schreiben ohne den CP unnoetig zu blockieren
class FileWriter_Task(threading.Thread):
    def __init__(self,FileName,content,args):
        threading.Thread.__init__(self)
        self.filename = FileName
        self.content = content
        self.mode = args

    def run(self):
        self.file = open(self.filename, self.mode)
        self.file.write(self.content)
        self.file.close()


# HelperThread um Files zu uebertragen ohne den CP unnoetig zu blockieren
class FileTransfer_Task(threading.Thread):
    def __init__(self, SourceFileName, TargetFileName, Drone = None):
        # Do initialization what you have to do
        threading.Thread.__init__(self)
        self.s_filename = SourceFileName
        self.t_filename = TargetFileName
        self.target_drone = Drone

    def read_in_chunks(self, file_object, chunk_size=1024):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    def run(self):
        self.file = open(self.s_filename)
        self.Block = False
        if (self.target_drone == None):
           pass
        else:
            for self.out_Block in self.read_in_chunks(self.file,5000):
                if (self.Block == False):
                    FileIO.CP.ToDrone(self.target_drone, "1 9 0 " + self.t_filename + " " + self.out_Block)
                    self.Block = True
                else:
                    FileIO.CP.ToDrone(self.target_drone, "1 9 1 " + self.t_filename + " " + self.out_Block)
                    
            self.file.close()



