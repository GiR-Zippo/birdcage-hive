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
####                EVENTS                   ####
#################################################
import threading, time

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

