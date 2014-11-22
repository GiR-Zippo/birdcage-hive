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

import zlib
import StringIO
import struct
from Crypto.Cipher import ARC4
from Crypto.Cipher import CAST
from Crypto import Random

#################################################
####      Decompressor for Input Stream      ####
#################################################
class ZipInputStream:

    def __init__(self, file):
        self.file = file
        self.__rewind()

    def __rewind(self):
        self.zip = zlib.decompressobj()
        self.pos = 0 # position in zipped stream
        self.offset = 0 # position in unzipped stream
        self.data = ""

    def __fill(self, bytes):
        if self.zip:
            # read until we have enough bytes in the buffer
            while not bytes or len(self.data) < bytes:
                self.file.seek(self.pos)
                data = self.file.read(16384)
                if not data:
                    self.data = self.data + self.zip.flush()
                    self.zip = None # no more data
                    break
                self.pos = self.pos + len(data)
                try:
                    self.data = self.data + self.zip.decompress(data)
                except:
                    return

    def seek(self, offset, whence=0):
        if whence == 0:
            position = offset
        elif whence == 1:
            position = self.offset + offset
        else:
            raise IOError, "Illegal argument"
        if position < self.offset:
            raise IOError, "Cannot seek backwards"

        # skip forward, in 16k blocks
        while position > self.offset:
            if not self.read(min(position - self.offset, 16384)):
                break

    def tell(self):
        return self.offset

    def read(self, bytes = 0):
        self.__fill(bytes)
        if bytes:
            data = self.data[:bytes]
            self.data = self.data[bytes:]
        else:
            data = self.data
            self.data = ""
        self.offset = self.offset + len(data)
        return data

#################################################
####            Header and Packet            ####
#################################################
class Packet:
    def __init__(self):
        self.TargetDrone = "ALL"
        self.Address = 0
        self.Command = 0
        self.pck_size = 0
        self.content = ""
        return

    #HEADER I/O
    def GetPacketWithHeader(self):
        self.pck_size = len(self.content)
        data1 = 0xFF &(self.pck_size>>24)
        data2 = 0xFF &(self.pck_size>>16)
        data3 = 0xFF &(self.pck_size>>8)
        data4 = 0xFF & self.pck_size
        self.content = chr(data1)+ chr(data2) + chr(data3) + chr(data4) + self.content
        return self.content

    def SetHeader(self, buff):
        reqsize =  (0xFF & ord(buff[0])) << 24
        reqsize += (0xFF & ord(buff[1])) << 16
        reqsize += (0xFF & ord(buff[2])) << 8
        reqsize += (0xFF & ord(buff[3]))
        self.pck_size = reqsize
        return

    #En-/De-Cryption
    def Encrypt(self, digestA, pbk):
        cryp = ARC4.new(digestA)
        data = zlib.compress(self.content)
        data = cryp.encrypt(data)
        iv = Random.new().read(CAST.block_size)
        cipher = CAST.new(pbk, CAST.MODE_OPENPGP, iv)
        self.content = cipher.encrypt(data)
        return

    def Decrypt(self, digestA, pbk):
        cryp = ARC4.new(digestA)
        eiv = self.content[:CAST.block_size+2]
        ciphertext = self.content[CAST.block_size+2:]
        cipher = CAST.new(pbk, CAST.MODE_OPENPGP, eiv)
        data = cipher.decrypt(ciphertext)
        data = cryp.decrypt(data)
        data = ZipInputStream(StringIO.StringIO(data)).read()
        self.content = data
        return

    #PacketFlow-Control#
    def SetTargetDrone(self, arg):
        self.TargetDrone = arg
        return
    def GetTargetDrone(self):
        return self.TargetDrone

    def SetAddress(self, arg):
        self.Address = arg
        return
    def GetAddress(self):
        return self.Address

    def SetCommand(self, arg):
        self.Command = arg
        return
    def GetCommand(self):
        return self.Command

    #PacketControl
    def GetPacketSize(self):
        return self.pck_size

    #content control
    def SetData(self, data):
        self.content = data
        return

    def GetData(self):
        return self.content

    def AppendString(self, data):
        self.content += data
        return

    ###########################
    # TODO: Write into packet #
    ###########################
    def uint8(self, u):
        self.content = self.content + struct.pack('!B', u)
        return

    def uint16(self, u):
        self.content = self.content + struct.pack('<H', u)
        return

    def uint32(self, u):
        self.content = self.content + struct.pack('<I', u)
        return

    def string(self, s):
        self.content = chr(len(s)) + s
        return

    #get from packet
    def GetUint8(self):
        self.out = self.content[0]
        self.content = self.content[1:]
        return struct.unpack('!B', self.out)[0]

    def GetUint16(self):
        self.out = ''
        for data in range(0,2):
            self.out = self.out + self.content[data]
        self.content = self.content[2:]
        return struct.unpack('!H', self.out)

    def GetUint32(self):
        self.out = ''
        for data in range(0,4):
            self.out = self.out + self.content[data]
        self.content = self.content[4:]
        return struct.unpack('!I', self.out)

    def GetString(self):
        strlen = ord(self.content[0])
        self.content = self.content[1:]
        print self.content[:strlen]
        self.content = self.content[strlen:]
        return

    def SkipRead(self, len):
        self.content = self.content[len:]
        return