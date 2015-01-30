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

#################################################
####         Interlink for modules           ####
#################################################

class InterStruct:
    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module

class Interlink:
    def __init__(self):
        self.modulesInterlink = []
        return

    def AddModule(self, src, dest, module):
        data = InterStruct(src, dest, module)
        self.modulesInterlink.append(data)
        return

    def CheckModule(self, addr):
        for i in self.modulesInterlink:
            if (i.dest == addr):
                return i.module
        return None