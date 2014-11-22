__author__ = 'dasumba'

from Crypto.Cipher import ARC4
from Crypto.Hash import SHA256
from Crypto.Cipher import CAST
from Crypto import Random
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