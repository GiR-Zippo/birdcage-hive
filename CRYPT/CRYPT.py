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

from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2


class Crypt:
    def __init__(self):
        return

    def SHA256(self, t):
        h = SHA256.new()
        h.update(b'%s' % t)
        return h

    def PBKDF2(self, argA, argB, digits):
        return PBKDF2(argA, argB, digits)