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

class Config:
    def __init__(self, configFile):
        try:
            self.file = open(configFile, "r")
        except:
            self.content = ''
            return
        self.content = self.file.read()
        self.file.close()
        return

    def CheckFile(self):
        if len(self.content) > 0:
            return True
        return False

    def GetItem(self, args):
        _lines = self.content.split("\n")
        for _line in _lines:
            try:
                if _line[0] == "#":
                    continue
            except IndexError:
                    continue

            _items = _line.split("=")
            idx = 0
            for _item in _items:
                idx = idx +1
                if _item.strip() == args:
                    return _items[idx].strip()
        return ''

    def GetItemList(self, args):
        _list = []
        _lines = self.content.split("\n")
        for _line in _lines:
            try:
                if _line[0] == "#":
                    continue
            except IndexError:
                    continue

            _out = _line.split("=")
            if _out[0].strip() == args:
                try:
                    for _item in _out[1].split(','):
                        _list.append(_item.strip())
                except:
                    _list.append(_out[1].strip())
        return _list