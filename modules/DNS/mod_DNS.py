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

import CP
import urllib
import urllib2
import cookielib
import FILEIO
import CONFIG

#Base-Address
#Please read the read.me in the root-dir
address = "401"
m_version ="0.1"

class DNS:
    def __init__(self, Master):
        self.Master = Master
        self.handler = None
        self.msg = ''
        self.domain = ''
        self.domainID = ''
        self.zonefile = ''
        # Store the cookies and create an opener that will hold them
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders = [('User-agent', 'HIVE')] # Add our headers
        urllib2.install_opener(self.opener)
        return

    def SendData(self, url, Payload = None):
        if not Payload:
            req = urllib2.Request(url)
        else:
            # Use urllib to encode the payload
            data = urllib.urlencode(Payload)
            # Build our Request object (supplying 'data' makes it a POST)
            req = urllib2.Request(url, data)

        # Make the request and read the response
        resp = urllib2.urlopen(req)
        contents = resp.read()

        if (contents.find('value="Zone file successfully replaced"') != -1):
            if (self.handler.ID != 'SCK'):
                self.handler.writeline("Zonefile wurde erfolgreich ersetzt.")
        if (contents.find('value="Zonefile wurde erfolgreich ersetzt"') != -1):
            if (self.handler.ID != 'SCK'):
                self.handler.writeline("Zonefile wurde erfolgreich ersetzt.")
        print contents
        return

    def Login(self):
        url = self.Master.URL + 'login.php'
        payload = {
          'login_user_inputbox': '%s' % self.Master.USER,
          'login_pass_inputbox': '%s' % self.Master.PASS,
          }
        self.SendData(url, payload)
        return

    def WriteDNSData(self):
        url = self.Master.URL + 'frame_menu.php?hosting=Addon%20Domain&domain='+self.domain+'&domain_number='+self.domainID+'&status=Ready'
        self.SendData(url)
        authentication_url = self.Master.URL + 'dns_shared.php'
        payload = {
          'domain_to_use': '%s' % self.domain,
          'dnsaction': 'dns',
          'dnsaction2': 'zonereplace',
          'zone_file1' : '%s' % self.zonefile,
          }
        self.SendData(authentication_url, payload)
        return

    def GetFile(self, handler, file):
        self.zonefile = ''
        replace = ''
        start = False
        try:
            fp = open('%s/%s' % (self.Master.PATH, file), 'rb')
        except:
            if (handler.ID != 'SCK'):
                handler.writeline("File not found error.")
            return False

        try:
            self.msg = fp.readlines()
            for data in self.msg:
                if (data.find('#BEGIN') != -1):
                    start=True
                    continue
                if (data.find('#END') != -1):
                    start=False
                    continue
                if (data[0] == '#'):
                    continue
                if (data.find('domain_number=') != -1):
                    self.domainID = data.split('=')[1].strip()
                    continue
                if (data.find('domain=') != -1):
                    self.domain = data.split('=')[1].strip()
                    continue
                if (data.find('replace=') != -1):
                    replace = (data.split('=')[1].strip(), data.split('=')[2].strip())
                    continue
                else:
                    if (start == True):
                        self.zonefile = self.zonefile + data
        except:
            if (handler.ID != 'SCK'):
                handler.writeline("Error in file.")
            fp.close()
            return False

        fp.close()

        if (len(replace) > 0):
            self.zonefile = self.zonefile.replace(replace[0].strip(), replace[1].strip())

        return True

    def LoadDefault(self, handler, args):
        self.handler = handler
        if (args == 'all'):
            self.Login()
            for data in self.Master.ALLDEFAULT:
                if (self.GetFile(handler, data.strip() + "_default.dns") == False):
                    continue
                self.WriteDNSData()
            return

        if (self.GetFile(handler, args.strip() + "_default.dns") == False):
            return

        self.Login()
        self.WriteDNSData()
        if (handler.ID != 'SCK'):
            handler.writeline("DNS-Table replaced...")
        return

    def Load(self, handler, args):
        self.handler = handler
        if (self.GetFile(handler, args.strip() + ".dns") == False):
            return

        self.Login()
        self.WriteDNSData()
        if (handler.ID != 'SCK'):
            handler.writeline("DNS-Table replaced...")
        return

class Master:
    CP #Pointer for the CP
    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        self.PATH = ''
        self.URL = ''
        self.USER = ''
        self.PASS = ''
        return

    def start(self):
        print "DNS-Init"
        return

    def initfromdrone(self, args, handler):
        return

    def config(self, args, CP):
        Master.CP = CP
        config = CONFIG.Config("./configs/mod_DNS.conf")
        self.URL = config.GetItem("url")
        self.USER = config.GetItem("login-User")
        self.PASS = config.GetItem("login-Pass")
        self.PATH = config.GetItem("file-path")
        self.ALLDEFAULT = config.GetItem("default-Tables").split(",")
        return

    def command(self, args, handler):
        omv = args.split(" ")
        self.DNS = DNS(self)
        if omv[0] == address:
            if omv[1] == "1":
                template = omv[2].strip()
                self.DNS.ChangeZoneFile(handler, template)
                return
            if omv[1] == "2":
                template = omv[2].strip()
                self.DNS.LoadDefault(handler, template)
                return
        return

    def stop(self):
        return True;

    def Event(self):
        return

#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" "))
            if (args.split(" ")[0] == "load"):
                if (self.maxlen == 2):
                    return "401 1 " + args.split(" ")[1]
                else:
                    if (args.split(" ")[1] == "default"):
                        return "401 2 " + args.split(" ")[2]
        except IndexError:
            print args
            return
