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


class Interlink:
    def __init__(self):
        self.modulesInterlink = []
        return

    def AddModule(self, module):
        return

    def CheckModule(self, address, module):
        if [address,module] in self.modulesInterlink:
            return True
        return False
        #self.modulesInterlink.append(module)
        return
