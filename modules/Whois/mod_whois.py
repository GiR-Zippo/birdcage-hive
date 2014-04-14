# encoding: iso-8859-1
# python3 com
#
# (C) 20011-2014 by Booksize
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

#
#Original Python-File from: http://code.activestate.com/recipes/577364-whois-client/
#

import sys
import socket
import optparse
import CP, time, threading, sys, os, subprocess

#Base-Address
#Please read the read.me in the root-dir
address = "310"
m_version ="0.1"

class NICClient(object) :

    ABUSEHOST           = "whois.abuse.net"
    NICHOST             = "whois.crsnic.net"
    INICHOST            = "whois.networksolutions.com"
    DNICHOST            = "whois.nic.mil"
    GNICHOST            = "whois.nic.gov"
    ANICHOST            = "whois.arin.net"
    LNICHOST            = "whois.lacnic.net"
    RNICHOST            = "whois.ripe.net"
    PNICHOST            = "whois.apnic.net"
    MNICHOST            = "whois.ra.net"
    QNICHOST_TAIL       = ".whois-servers.net"
    SNICHOST            = "whois.6bone.net"
    BNICHOST            = "whois.registro.br"
    NORIDHOST           = "whois.norid.no"
    IANAHOST            = "whois.iana.org"
    GERMNICHOST         = "de.whois-servers.net"
    DEFAULT_PORT        = "nicname"
    WHOIS_SERVER_ID     = "Whois Server:"
    WHOIS_ORG_SERVER_ID = "Registrant Street1:Whois Server:"


    WHOIS_RECURSE       = 0x01
    WHOIS_QUICK         = 0x02

    ip_whois = [ LNICHOST, RNICHOST, PNICHOST, BNICHOST ]

    common_servers = (
        ABUSEHOST,
        ABUSEHOST,
        NICHOST,
        INICHOST,
        DNICHOST,
        GNICHOST,
        ANICHOST,
        LNICHOST,
        RNICHOST,
        PNICHOST,
        MNICHOST,
        SNICHOST,
        BNICHOST,
        NORIDHOST,
        IANAHOST,
        GERMNICHOST
    )

    def __init__(self) :
        self.use_qnichost = False

    def findwhois_server(self, buf, hostname):
        """Search the initial TLD lookup results for the regional-specifc
        whois server for getting contact details.
        """
        nhost = None
        parts_index = 1
        start = buf.find(NICClient.WHOIS_SERVER_ID)
        if (start == -1):
            start = buf.find(NICClient.WHOIS_ORG_SERVER_ID)
            parts_index = 2

        if (start > -1):
            end = buf[start:].find('\n')
            whois_line = buf[start:end+start]
            whois_parts = whois_line.split(':')
            nhost = whois_parts[parts_index].strip()
        elif (hostname == NICClient.ANICHOST):
            for nichost in NICClient.ip_whois:
                if (buf.find(nichost) != -1):
                    nhost = nichost
                    break
        return nhost

    def whois(self, query, hostname, flags):
        """Perform initial lookup with TLD whois server
        then, if the quick flag is false, search that result
        for the region-specifc whois server and do a lookup
        there for contact details
        """
        #pdb.set_trace()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((hostname, 43))
        if (hostname == NICClient.GERMNICHOST):
            s.send("-T dn,ace -C US-ASCII " + query + "\r\n")
        else:
            s.send(query + "\r\n")
        response = ''
        while True:
            d = s.recv(4096)
            response += d
            if not d:
                break
        s.close()
        #pdb.set_trace()
        nhost = None
        if (flags & NICClient.WHOIS_RECURSE and nhost == None):
            nhost = self.findwhois_server(response, hostname)
        if (nhost != None):
            if nhost in NICClient.common_servers:
                response = self.whois(query, nhost, 0)
            else:
                response += self.whois(query, nhost, 0)
        return response

    def choose_server(self, domain):
        """Choose initial lookup NIC host"""
        if (domain.endswith("-NORID")):
            return NICClient.NORIDHOST
        pos = domain.rfind('.')
        if (pos == -1):
            return None
        tld = domain[pos+1:]
        if (tld[0].isdigit()):
            return NICClient.ANICHOST

        return tld + NICClient.QNICHOST_TAIL

    def whois_lookup(self, options, query_arg, flags):
        """Main entry point: Perform initial lookup on TLD whois server,
        or other server to get region-specific whois server, then if quick
        flag is false, perform a second lookup on the region-specific
        server for contact records"""
        nichost = None
        result = None
        #pdb.set_trace()
        # this would be the case when this function is called by other then main
        if (options == None):
            options = {}

        if ( ('whoishost' not in options or options['whoishost'] == None)
            and ('country' not in options or options['country'] == None)):
            self.use_qnichost = True
            options['whoishost'] = NICClient.NICHOST
            if ( not (flags & NICClient.WHOIS_QUICK)):
                flags |= NICClient.WHOIS_RECURSE

        if ('country' in options and options['country'] != None):
            result = self.whois(query_arg, options['country'] + NICClient.QNICHOST_TAIL, flags)
        elif (self.use_qnichost):
            nichost = self.choose_server(query_arg)
            if (nichost != None):
                result = self.whois(query_arg, nichost, flags)
        else:
            result = self.whois(query_arg, options['whoishost'], flags)

        return result


def parse_command_line(argv):
    """Options handling mostly follows the UNIX whois(1) man page, except
    long-form options can also be used.
    """
    flags = 0

    usage = "usage: %prog [options] name"

    parser = optparse.OptionParser(add_help_option=False, usage=usage)
    parser.add_option("-a", "--arin", action="store_const",
                      const=NICClient.ANICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.ANICHOST)
    parser.add_option("-A", "--apnic", action="store_const",
                      const=NICClient.PNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.PNICHOST)
    parser.add_option("-b", "--abuse", action="store_const",
                      const=NICClient.ABUSEHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.ABUSEHOST)
    parser.add_option("-c", "--country", action="store",
                      type="string", dest="country",
                      help="Lookup using country-specific NIC")
    parser.add_option("-d", "--mil", action="store_const",
                      const=NICClient.DNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.DNICHOST)
    parser.add_option("-g", "--gov", action="store_const",
                      const=NICClient.GNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.GNICHOST)
    parser.add_option("-h", "--host", action="store",
                      type="string", dest="whoishost",
                       help="Lookup using specified whois host")
    parser.add_option("-i", "--nws", action="store_const",
                      const=NICClient.INICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.INICHOST)
    parser.add_option("-I", "--iana", action="store_const",
                      const=NICClient.IANAHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.IANAHOST)
    parser.add_option("-l", "--lcanic", action="store_const",
                      const=NICClient.LNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.LNICHOST)
    parser.add_option("-m", "--ra", action="store_const",
                      const=NICClient.MNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.MNICHOST)
    parser.add_option("-p", "--port", action="store",
                      type="int", dest="port",
                      help="Lookup using specified tcp port")
    parser.add_option("-Q", "--quick", action="store_true",
                     dest="b_quicklookup",
                     help="Perform quick lookup")
    parser.add_option("-r", "--ripe", action="store_const",
                      const=NICClient.RNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.RNICHOST)
    parser.add_option("-R", "--ru", action="store_const",
                      const="ru", dest="country",
                      help="Lookup Russian NIC")
    parser.add_option("-6", "--6bone", action="store_const",
                      const=NICClient.SNICHOST, dest="whoishost",
                      help="Lookup using host " + NICClient.SNICHOST)
    parser.add_option("-?", "--help", action="help")


    return parser.parse_args(argv)

class Master:
    CP #Pointer for the CP
    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        return

    def start(self):
        return

    def initfromdrone(self, args, handler):
        return

    def config(self, args, CP):
        Master.CP = CP;
        return

    def command(self, args, handler):
        omv = args.split(" ")
        if omv[0] == address:
            if omv[1] == "1":
                flags = 0
                ask = omv[2].strip()
                nic_client = NICClient()
                (options, args) = parse_command_line(sys.argv)
                if (options.b_quicklookup is True):
                    flags = flags|NICClient.WHOIS_QUICK
                output = nic_client.whois_lookup(options.__dict__, ask, flags)
                handler.writeline (output)
        return

    def stop(self):
        return True;

    def Event(self):
        return

#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" ")) - 1
            if (args.split(" ")[0] == "whois"):
                return "310 1 " + args.split(" ")[1]

        except IndexError:
            print(args)
            return
