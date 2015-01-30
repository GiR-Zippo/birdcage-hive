import zlib
import StringIO

#################################################
####         Handle Zip-Data Streams         ####
#################################################


class ZipInputStream:

    def __init__(self, tfile, encrypt=False, ratio=6):
        self.file = tfile
        self.pos = 0     # position in zipped stream
        self.offset = 0  # position in unzipped stream
        self.ratio = ratio
        self.data = ""
        if encrypt == False:
            self.__rewind()

    def __rewind(self):
        self.zip = zlib.decompressobj()
        self.pos = 0     # position in zipped stream
        self.offset = 0  # position in unzipped stream
        self.data = ""

    def __fill(self, tbytes):
        if self.zip:
            # read until we have enough bytes in the buffer
            while not tbytes or len(self.data) < tbytes:
                self.file.seek(self.pos)
                data = self.file.read(16384)
                if not data:
                    self.data = self.data + self.zip.flush()
                    self.zip = None  # no more data
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

    def read(self, tbytes = 0):
        self.__fill(tbytes)
        if tbytes:
            data = self.data[:tbytes]
            self.data = self.data[tbytes:]
        else:
            data = self.data
            self.data = ""
        self.offset = self.offset + len(data)
        return data

    def compress(self):
        return zlib.compress(self.file, self.ratio)