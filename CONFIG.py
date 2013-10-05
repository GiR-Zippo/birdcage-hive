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

class Config:
    def __init__(self, configFile):
        self.file = open(configFile, "r")
        self.str = self.file.read()
        self.file.close()
        return

    def GetItem(self, args):
        temp = self.str.split("\n")
        for self.r_item in temp:
            try:
                if self.r_item[0] == "#":
                    continue
            except IndexError:
                    continue

            self.out = self.r_item.split("=")
            idx = 0
            for item in self.out:
                idx = idx +1
                if item.strip() == args:
                    return self.out[idx].strip()
        return ''

