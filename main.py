#!/usr/bin/env python
# python3 com
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

__author__="dasumba"
__date__ ="$17.09.2011 17:31:44$"

if __name__ == "__main__":
    ##Startup
    print("  Birdcage V0.7a Hive-Edition")
    print("")
    print("          ___(__)___")
    print("         /          \     ")
    print("        |     ___    |  ")
    print("        |    ('v')   | ")
    print("        |   ((___))  |  ")
    print("        |--/-'---'---| ")
    print("")
    print("(c) Booksize")
    print("Do anythin what you want to do...")
    print("")

import SOCKS, CP, FILEIO

m_CP = CP.CP()
m_Runnable = True

while (m_Runnable == True):
    time.sleep(0.003) #Take a short nap :)
    if (m_CP.refresh() ==False):
        m_Runnable = False
