# encoding: iso-8859-1

#
# Copyright (C) 2011-2014 by Booksize
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

import CP, FILEIO
import time, threading, sys, os, commands
from collections import deque

# BaseAddress
address = "300"
m_version ="0.5"
LOCK = threading.Lock()

FLAG_GLOBAL = int('00000001',2) #Set if we working global
FLAG_LOCAL  = int('00000010',2) #Set if we working local
FLAG_EXPORT = int('00000100',2) #Set if this entry could export

#The FIFO-Buffer for incomming commands
class Fifo:
    def __init__(self):
        self.first_a= deque()
        self.first_b= deque()

    def append(self,data,handler):
        self.first_a.append(data)
        self.first_b.append(handler)

    def pop(self):
        try:
            return self.first_a.popleft(), self.first_b.popleft()
        except (IndexError):
            pass

    def hascontent(self):
        if (len(self.first_a) > 0):
            return True
        return False

class Firewall:
    def __init__(self, CP):
        self.blackrange = [] #Name, range
        self.whitelist  = []
        self.blacklist  = [] #IP, connections, removetime, flag, note
        self.CP = CP

        CP.sLog.outString("Starting Firewall")
        return

    #Blacklist control
    def BlackListInsert(self, ip, connections, removetime, flag, note): #001
        for item in self.whitelist:
            if (item[0] == ip):
                return
        for item in self.blacklist:
            if (item[0] == ip):
                return

        self.blacklist.append([ip, connections, removetime, flag, note])
        self.ipt_b(ip)
        self.CP.ToLog("Debug", "IP: " + str(ip) + " banned.")

        if (bool(FLAG_GLOBAL & int(flag))):
            self.CP.ToSocket(address + " 1 " + str(ip) + " " + str(connections) + " " + removetime + " " + str(flag) + " " + note)
        return

    def BlackListRemove(self, ip): #002
        for item in self.blacklist:
            if (item[0] == ip):
                self.blacklist.remove(item)
                self.ipt_ub(ip)
                self.CP.ToLog("Debug", "IP: " + str(ip) + " unbanned.")
        return

    def BlackListRemoveAll(self):
        for item in self.blacklist:
            self.blacklist.remove(item)
            self.ipt_ub(item[0])
        return

    def ShowBlacklist(self,handler): #003
        for ip, connection, removetime, flag, note in self.blacklist:
            if (handler.ID == "SCK"):
                if (bool(FLAG_GLOBAL & int(flag))):
                    handler.writeline (address + " 1 %s %s %s %s %s" %(ip, connection, removetime, flag, note))
            else:
                if (bool(FLAG_GLOBAL & int(flag))):
                    handler.writeline ("%s %s %s Global %s" %(ip, connection, removetime, note))
                else:
                    handler.writeline ("%s %s %s Local %s" %(ip, connection, removetime, note))

    # Whitelist control
    def WhiteListInsert(self, ip, local): #010
        for item in self.whitelist:
            if (item[0] == ip):
                return
        self.whitelist.append([ip, int(local)])
        self.BlackListRemove(ip)
        self.ipt_whitelist_insert(ip)
        if (local == 0):
            self.CP.ToSocket(address + " 10 " + str(ip) + " " + str(local))

        return

    def WhiteListRemove(self, ip): #011
        for item in self.whitelist:
            if (item[0] == ip):
                self.whitelist.remove(item)
                self.ipt_whitelist_remove(ip)
        return

    def ShowWhitelist(self,handler): #012
        for item in self.whitelist:
            if (handler.ID == "SCK"):
                if (item[1] == 0):
                    handler.writeline (address + " 10 "+ item[0] + " 0")
            else:
                if (item[1] == 0):
                    handler.writeline ("" + str(item[0]) + " Global "+ str(item[1]))
                else:
                    handler.writeline ("" + str(item[0]) + " Local "+ str(item[1]))
        return

    def InsertBlackRange(self, name, range, flag, note):
        uname = name.upper()
        for bname, brange, bflag, bnote in self.blackrange:
            if (uname == bname):
                return
            if (brange == range):
                return

        self.blackrange.append([uname, range, flag, note])
        self.CP.ToLog("Debug", "RANGE: " + str(range) + " blocked.")
        self.ipt_rb(range)
        if (bool(FLAG_GLOBAL & int(flag))):
            self.CP.ToSocket(address + " 30 %s %s %s %s" % (name.upper(), range, flag, note))
        return

    def RemoveBlackRange(self, name, local):
        self.sname = name.upper()
        for self.name, self.range, self.flag, self.note in self.blackrange:
            if (self.name == self.sname):
                self.blackrange.remove([self.name, self.range, self.loc])
                self.CP.ToLog("Debug", "RANGE: " + str(range) + " unblocked.")
                self.ipt_rub(self.range)
                if (local == 0):
                    self.CP.ToSocket(address + " 31 0 " + self.sname)
                return
        return

    def ShowBlackRange(self,handler):
        self.blackrange = sorted(self.blackrange, key=lambda name: name[0])
        for name, range, flag, note in self.blackrange:
            if (handler.ID == "SCK"):
                if (bool(FLAG_GLOBAL & int(flag))):
                    handler.writeline (address + " 30 %s %s %s %s" %(name, range, flag, note))
            else:
                if (bool(FLAG_GLOBAL & int(flag))):
                    handler.writeline ("%s %s Global Note: %s" % (name, range, note))
                else:
                    handler.writeline ("%s %s Local Note: %s" % (name, range, note))
        return

    def ExportBlackRange(self,handler, args):
        fp = open(args, 'w')
        for name, range, flag, note in self.blackrange:
            fp.write(name)
            fp.write(" ")
            fp.write(range)
            fp.write(" ")
            fp.write(str(flag))
            fp.write(" ")
            fp.write(str(note))
            fp.write("\r\n")
        fp.close()
        return

    def ImportBlackRange(self,handler, args):
        fp = open(args, 'r')
        for i in fp.readlines():
            if (i == '\r\n'):
                continue
            i = i.replace('\n', '')
            i = i.replace('\r', '')
            isp = i.split(" ")
            try:
                self.InsertBlackRange(isp[0], isp[1], isp[2], isp[3])
            except IndexError:
                continue
        fp.close()
        return

    def InsertBlackPort(self, port, type):
        port = port.strip()
        if (type == "TCP"):
            self.ipt_bp(port, False)
        else:
            self.ipt_bp(port, True)

        self.CP.ToLog("Debug", "PORT(s): " + str(port) + " " + str(type) + " blocked.")
        return

    def InsertWhitePort(self, port, type):
        port = port.strip()
        if (type == "TCP"):
            self.ipt_wp(port, False)
        else:
            self.ipt_wp(port, True)

        self.CP.ToLog("Debug", "PORT(s): " + str(port) + " " + str(type) + " accepted.")
        return

    def ipt_wp(self,port, udp):
        if (udp == False):
            self.dp = "tcp"
            os.system ("/sbin/iptables -I INPUT -p " + self.dp + " --destination-port " + str(port) + " -j ACCEPT")
        else:
            self.dp = "udp"
            os.system ("/sbin/iptables -I INPUT -p " + self.dp + " --destination-port " + str(port) + " -j ACCEPT")

        os.system ("/sbin/iptables -I FORWARD -p " + self.dp + " --destination-port " + str(port) + " -j ACCEPT")
        os.system ("/sbin/iptables -I OUTPUT -p " + self.dp + " --destination-port " + str(port) + " -j ACCEPT")
        return

    def ipt_bp(self,port, udp):
        if (udp == False):
            self.dp = "tcp"
            os.system ("/sbin/iptables -I INPUT -p " + self.dp + " --destination-port " + str(port) + " -j REJECT --reject-with tcp-reset")
        else:
            self.dp = "udp"
            os.system ("/sbin/iptables -I INPUT -p " + self.dp + " --destination-port " + str(port) + " -j REJECT")

        os.system ("/sbin/iptables -I FORWARD -p " + self.dp + " --destination-port " + str(port) + " -j REJECT")
        #os.system ("/sbin/iptables -I OUTPUT -p " + self.dp + " --destination-port " + str(port) + " -j DROP")
        return

    def ipt_upp(self,port, udp):
        if (udp == False):
            self.dp = "tcp"
            os.system ("/sbin/iptables -D INPUT -p " + self.dp + " --destination-port " + str(port) + " -j REJECT --reject-with tcp-reset")
        else:
            self.dp = "udp"
            os.system ("/sbin/iptables -D INPUT -p " + self.dp + " --destination-port " + str(port) + " -j REJECT")

        os.system ("/sbin/iptables -D FORWARD -p " + self.dp + " --destination-port " + str(port) + " -j REJECT")
        #os.system ("/sbin/iptables -D OUTPUT -p " + self.dp + " --destination-port " + str(port) + " -j DROP")
        return

    def ipt_rb(self,range):
        os.system ("/sbin/iptables -I INPUT -p tcp -m iprange --src-range " + str(range) + " -j REJECT --reject-with tcp-reset")
        os.system ("/sbin/iptables -I INPUT -m iprange --src-range " + str(range) + " -j REJECT")
        os.system ("/sbin/iptables -I FORWARD -m iprange --src-range " + str(range) + " -j REJECT")
        os.system ("/sbin/iptables -I OUTPUT -m iprange --src-range " + str(range) + " -j DROP")
        return

    def ipt_rub(self,range):
        os.system ("/sbin/iptables -D INPUT -p tcp -m iprange --src-range " + str(range) + " -j REJECT --reject-with tcp-reset")
        os.system ("/sbin/iptables -D INPUT -m iprange --src-range " + str(range) + " -j REJECT")
        os.system ("/sbin/iptables -D FORWARD -m iprange --src-range " + str(range) + " -j REJECT")
        os.system ("/sbin/iptables -D OUTPUT -m iprange --src-range " + str(range) + " -j DROP")
        return

    def ipt_ub(self,ip):
        os.system ("/sbin/iptables -D INPUT -p tcp -s " + str(ip) + " -j REJECT --reject-with tcp-reset")
        os.system ("/sbin/iptables -D INPUT -s " + str(ip) + " -j REJECT")
        os.system ("/sbin/iptables -D FORWARD -s " + str(ip) + " -j REJECT")
        os.system ("/sbin/iptables -D OUTPUT -s " + str(ip) + " -j REJECT")
        return

    def ipt_b(self,ip):
        os.system ("/sbin/iptables -I INPUT -p tcp -s " + str(ip) + " -j REJECT --reject-with tcp-reset")
        os.system ("/sbin/iptables -I INPUT -s " + str(ip) + " -j REJECT")
        os.system ("/sbin/iptables -I FORWARD -s " + str(ip) + " -j REJECT")
        os.system ("/sbin/iptables -I OUTPUT -s " + str(ip) + " -j REJECT")
        return

    def ipt_whitelist_insert(self, ip):
        os.system ("/sbin/iptables -A INPUT -p all -s " + str(ip) + " -j ACCEPT")
        os.system ("/sbin/iptables -A FORWARD -p all -s " + str(ip) + " -j ACCEPT")
        os.system ("/sbin/iptables -A OUTPUT -p all -s " + str(ip) + " -j ACCEPT")
        return

    def ipt_whitelist_remove(self,ip):
        os.system ("/sbin/iptables -D INPUT -p all -s " + str(ip) + " -j ACCEPT")
        os.system ("/sbin/iptables -D FORWARD -p all -s " + str(ip) + " -j ACCEPT")
        os.system ("/sbin/iptables -D OUTPUT -p all -s " + str(ip) + " -j ACCEPT")
        return

    def Update(self):
        if LOCK.acquire(False): # Non-blocking
            for self.ip, self.connections, self.removetime, self.local, self.note in self.blacklist:
                if (int(self.removetime) == 0):
                    continue
                if (float(self.removetime) < float(time.time())):
                    self.BlackListRemove(self.ip)
            LOCK.release()
        else:
            self.CP.ToLog("Critical", "Couldn't get the lock. Firewall::Update")
        return

    def ShowStatistics(self, handler):
        if (handler.ID == "SCK"):
            return

        handler.writeline ("Firewall statistic")
        loc = 0
        glob = 0
        all = 0
        for ip, connections, removetime, flag, note in self.blacklist:
            all = all+1
            if (bool(FLAG_GLOBAL & int(flag))):
                glob = glob+1
            else:
                loc = loc+1

        handler.writeline ("Blacklist: All %s - Local %s - Global %s" % (all, loc, glob))
        return

    def GetExports(self, handler, rAdd, rCmd):
        for ip, connections, removetime, flag, note in self.blacklist:
            if (bool(FLAG_EXPORT & int(flag))):
                if (int(rAdd) == 0):
                    handler.writeline ("%s %s %s %s" %(ip, connections, removetime, note))
                else:
                    handler.writeline ("%s %s %s %s %s %s %s" % (rAdd, rCmd, chr(1), ip, connections, removetime, note))

        for name, range, flag, note in self.blackrange:
            if (bool(FLAG_EXPORT & int(flag))):
                if (int(rAdd) == 0):
                    handler.writeline ("%s %s %s" %(name, range, note))
                else:
                    handler.writeline ("%s %s %s %s %s %s" % (rAdd, rCmd, chr(2), name, range, note))
        return

    def Help(self, handler):
        handler.writeline ("")
        handler.writeline ("blacklist insert IP                         = Local  IP ban")
        handler.writeline ("blacklist ginsert IP                        = Global IP ban")
        handler.writeline ("blacklist remove IP                         = Remove local IP-ban")
        handler.writeline ("blacklist gremove IP                        = Remove global IP-ban")
        handler.writeline ("blacklist show                              = Shows the IP-bans")
        handler.writeline ("")
        handler.writeline ("whitelist insert IP                         = whitelist IP local")
        handler.writeline ("whitelist ginsert IP                        = whitelist IP global")
        handler.writeline ("whitelist remove IP                         = Remove the IP from the local whitelist")
        handler.writeline ("whitelist gremove IP                        = Remove the IP from the global whitelist")
        handler.writeline ("whitelist show                              = Shows the Whitelist")
        handler.writeline ("")
        handler.writeline ("status                                      = gives the Firewall statistics")
        handler.writeline ("")
        handler.writeline ("rangeban insert Name Start-End              = Block the whole IP-Range local")
        handler.writeline ("rangeban ginsert Name Start-End             = Block the whole IP-Range global")
        handler.writeline ('rangeban ginsert-export Name Start-End Note = Block the whole IP-Range global with export-flag')
        handler.writeline ("rangeban remove Name                        = Remove rangeban local")
        handler.writeline ("rangeban gremove Name                       = Remove rangeban global")
        handler.writeline ("rangeban show                               = Shows the Rangebans")
        handler.writeline ("rangeban export Filename                    = Export the Rangebans")
        handler.writeline ("rangeban import Filename                    = Import the Rangebans")
        handler.writeline ("")
        handler.writeline ("get exports                                 = Lists all exportable Data")

## define Checking-Thread
class Master(threading.Thread):
    check = True
    wait=True
    interval = 1
    CP #Pointer for the CP

    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        self.initialized = False

        ## Setup the Buffer
        self.buffer = Fifo()
        os.system ("/sbin/iptables --flush")
        os.system ("/sbin/iptables -t mangle --flush")

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        self.firewall = Firewall(self.CP)

    def initfromdrone(self, args, handler):
        if (int(args) == int(address)):
            self.firewall.ShowWhitelist(handler)
            self.firewall.ShowBlacklist(handler)
            self.firewall.ShowBlackRange(handler)
        return

    def run(self):
        #Initialize the firewall
        self.CP.ToSocket("INIT " + address)
        while Master.check:
            self.update()
            self.firewall.Update()
            time.sleep(0.5)

    def config(self, args, CP):
        if (self.initialized == True):
            return
        self.initialized = True

        self.m_args = FILEIO.FileIO().ReadLine("./configs/mod_Firewall.conf")

        self.temp = self.m_args.split("\n")
        for self.r_item in self.temp:
            try:
                if self.r_item[0] == "#":
                    continue
            except IndexError:
                continue

            self.out = self.r_item.split("=")
            i=0
            for item in self.out:
                i=i+1
                #Black/Whitelists
                if item.strip() == "whitelist":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.WhiteListInsert(item.strip(), 1)

                if item.strip() == "blacklist":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.BlackListInsert(item.strip(), int(0), int(0), int(1))

                if item.strip() == "whitelistportTCP":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.InsertWhitePort(item, "TCP")

                if item.strip() == "blacklistportTCP":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.InsertBlackPort(item, "TCP")

                if item.strip() == "whitelistportUDP":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.InsertWhitePort(item, "UDP")

                if item.strip() == "blacklistportUDP":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.InsertBlackPort(item, "UDP")

                #MISC-Configurations
                if item.strip() == "tcp_syncookies":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/tcp_syncookies")
                if item.strip() == "ip_forward":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/ip_forward")
                if item.strip() == "icmp_accept_dest_ip":
                    os.system ("/sbin/iptables -A INPUT -d " + self.out[i].strip() + " -p ICMP --icmp-type 8 -j ACCEPT")
                if item.strip() == "icmp_ignore_all":
                    if (self.out[i].strip() == 1):
                        os.system ("/sbin/iptables -A INPUT -p ICMP -j DROP")
                if item.strip() == "icmp_echo_ignore_broadcasts":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
                if item.strip() == "log_martians":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/log_martians")
                if item.strip() == "icmp_ignore_bogus_error_responses":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/icmp_ignore_bogus_error_responses")
                if item.strip() == "log_martians":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/log_martians")
                if item.strip() == "rp_filter":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/rp_filter")
                    os.system ("for i in /proc/sys/net/ipv4/conf/*/rp_filter ; do \necho 1 > $i \ndone")
                if item.strip() == "send_redirects":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/send_redirects")
                if item.strip() == "accept_source_route":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/accept_source_route")
                if item.strip() == "icmp-limit":
                    os.system ("/sbin/iptables -A INPUT  -p icmp -m limit --limit " + self.out[i].strip() + "/second -j ACCEPT")
                    os.system ("/sbin/iptables -A INPUT  -p icmp -j DROP")
                if item.strip() == "portscan-detection":
                    if (self.out[i].strip() == "0"):
                        continue
                    # These rules add scanners to the portscan list, and log the attempt.
                    os.system ("/sbin/iptables -A INPUT   -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP")
                    #os.system ('/sbin/iptables -A INPUT   -p tcp -m tcp --dport 139 -m recent --name portscan --set -j LOG --log-prefix "Portscan:"')
                    os.system ("/sbin/iptables -A FORWARD -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP")
                    #os.system ('/sbin/iptables -A FORWARD -p tcp -m tcp --dport 139 -m recent --name portscan --set -j LOG --log-prefix "Portscan:"')

                if item.strip() == "portscan-ban-time":
                    if (self.out[i].strip() == 0):
                        continue
                    os.system ("/sbin/iptables -A INPUT   -m recent --name portscan --rcheck --seconds %s -j DROP" % (self.out[i].strip()))
                    os.system ("/sbin/iptables -A FORWARD -m recent --name portscan --rcheck --seconds %s -j DROP" % (self.out[i].strip()))
                    os.system ("/sbin/iptables -A INPUT   -m recent --name portscan --remove")
                    os.system ("/sbin/iptables -A FORWARD -m recent --name portscan --remove")
                if item.strip() == "ping":
                    if self.out[i].strip() == "0":
                        os.system ("/sbin/iptables -A INPUT -p icmp --icmp-type echo-request -j REJECT --reject-with icmp-host-unreachable")
                if item.strip() == "synlimit":
                    os.system ("/sbin/iptables -N synflood")
                    os.system ("/sbin/iptables -A synflood -m limit --limit "+ self.out[i].strip() + "/second --limit-burst 24 -j RETURN")
                    os.system ("/sbin/iptables -A synflood -j REJECT")
                    os.system ("/sbin/iptables -A INPUT -p tcp --syn -j synflood")
                if item.strip() == "conn-limit-log":
                    if int(self.out[i].strip()) > 0:
                        os.system ("/sbin/iptables -A INPUT -p udp -m connlimit --connlimit-above " + self.out[i].strip() + " -j LOG --log-level 4 --log-prefix 'UDP-In " + self.out[i].strip() + "/m '")
                        os.system ("/sbin/iptables -A INPUT -p tcp --syn  -m connlimit --connlimit-above " + self.out[i].strip() + " -j LOG --log-level 4 --log-prefix 'TCP-In " + self.out[i].strip() + "/m '")                    
                if item.strip() == "conn-limit":
                    os.system ("/sbin/iptables -A INPUT -p udp -m connlimit --connlimit-above " + self.out[i].strip() + " -j REJECT")
                    os.system ("/sbin/iptables -A INPUT -p tcp --syn  -m connlimit --connlimit-above " + self.out[i].strip() + " -j REJECT --reject-with tcp-reset")
        return

    def command(self,args, handler):
        self.buffer.append(args,handler)
        return

    def update(self):
        while (self.buffer.hascontent() == True):

            args, handler = self.buffer.pop()

            omv = args.split(" ")
            if omv[0] == address:
                #Blacklist
                if omv[1] == "1":
                    if (len(omv) > 6):
                        self.firewall.BlackListInsert(omv[2], int(omv[3]), omv[4], int(omv[5]), omv[6])
                    else:
                        self.firewall.BlackListInsert(omv[2], int(omv[3]), omv[4], int(omv[5]), 'NONE')
                if omv[1] == "2":
                    self.firewall.BlackListRemove(omv[2])
                if omv[1] == "3":
                    self.CP.ToSocket(address + " 2 " + omv[2])
                    self.firewall.BlackListRemove(omv[2])
                if omv[1] == "4":
                    self.firewall.ShowBlacklist(handler)

                #WhiteList
                if omv[1] == "10":
                    self.firewall.WhiteListInsert(omv[2], int(omv[3]))
                if omv[1] == "11":
                    self.firewall.WhiteListRemove(omv[2])
                if omv[1] == "12":
                    self.CP.ToSocket(address + " 11 " + omv[2])
                    self.firewall.WhiteListRemove(omv[2])
                if omv[1] == "13":
                    self.firewall.ShowWhitelist(handler)

                #Statistics
                if omv[1] == "20":
                    self.firewall.ShowStatistics(handler)

                #Range
                if omv[1] == "30":
                    if (len(omv) > 5):
                        self.firewall.InsertBlackRange(omv[2], omv[3], int(omv[4]), omv[5])
                    else:
                        self.firewall.InsertBlackRange(omv[2], omv[3], int(omv[4]), 'NONE')
                if omv[1] == "31":
                    self.firewall.RemoveBlackRange(omv[3], int(omv[2]))
                if omv[1] == "32":
                    self.firewall.ShowBlackRange(handler)
                if omv[1] == "33":
                    self.firewall.ExportBlackRange(handler, omv[2])
                if omv[1] == "34":
                    self.firewall.ImportBlackRange(handler, omv[2])

                if omv[1] == "40":
                    self.firewall.GetExports(handler, omv[2], omv[3])
                if omv[1] == "255":
                    self.firewall.Help(handler)
        return
    def stop(self):
        self.firewall.BlackListRemoveAll()
        os.system ('/sbin/iptables --flush')
        Master.check = False
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False

#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" ")) - 1
            if (args.split(" ")[0] == "version"):
                print (m_version)
                return
            if (args.split(" ")[0] == "status"):
                return address + " 20"
            if (args.split(" ")[0] == "blacklist"):
                if (self.maxlen >= 1):
                    #Insert local (ip,connection)
                    if (args.split(" ")[1] == "insert"):
                        try:
                            return address + " 1 " + args.split(" ")[2].strip() + " " + args.split(" ")[3].strip() + " " + str(int((time.time() + int(args.split(" ")[4].strip()))))  + " 2"
                        except IndexError:
                            return address + " 1 " + args.split(" ")[2].strip()  + " 0 0 2"
                    #Insert global (ip,connection)
                    if (args.split(" ")[1] == "ginsert"):
                        try:
                            return address + " 1 " + args.split(" ")[2].strip() + " " + args.split(" ")[3].strip() + " " + str(int((time.time() + int(args.split(" ")[4].strip()))))  + " 1 " + args.split(" ")[5].strip()
                        except IndexError:
                            return address + " 1 " + args.split(" ")[2].strip() + " 0 0 1"

                    #Remove local (ip)
                    if (args.split(" ")[1] == "remove"):
                        return address + " 2 " + args.split(" ")[2].strip()
                    #Remove global (ip)gremove
                    if (args.split(" ")[1] == "gremove"):
                        return address + " 3 " + args.split(" ")[2].strip()
                    #show the blacklist
                    if (args.split(" ")[1] == "show"):
                        return address + " 4"

            if (args.split(" ")[0] == "whitelist"):
                if (self.maxlen >= 1):
                    if (args.split(" ")[1] == "insert"):
                        return address + " 10 " + args.split(" ")[2].strip() + " 1"
                    if (args.split(" ")[1] == "ginsert"):
                        return address + " 10 " + args.split(" ")[2].strip() + " 0"
                    if (args.split(" ")[1] == "remove"):
                        return address + " 11 " + args.split(" ")[2].strip()
                    if (args.split(" ")[1] == "gremove"):
                        return address + " 12 " + args.split(" ")[2].strip()
                    #show the whitelist
                    if (args.split(" ")[1] == "show"):
                            return address + " 13"
            if (args.split(" ")[0].strip() == "rangeban"):
                if (self.maxlen >= 1):
                    if (args.split(" ")[1].strip() == "insert"):
                        return address + " 30 %s %s 2" %(args.split(" ")[2].strip(), args.split(" ")[3].strip())
                    if (args.split(" ")[1].strip() == "ginsert"):
                        return address + " 30 %s %s 1" %(args.split(" ")[2].strip(), args.split(" ")[3].strip())
                    if (args.split(" ")[1].strip() == "ginsert-export"):
                        return address + " 30 %s %s 5 %s" %(args.split(" ")[2].strip(), args.split(" ")[3].strip(), args.split(" ")[4].strip())
                    if (args.split(" ")[1] == "remove"):
                        return address + " 31 1 " + (args.split(" ")[2].strip())
                    if (args.split(" ")[1] == "gremove"):
                        return address + " 31 0 " + (args.split(" ")[2].strip())
                    if (args.split(" ")[1] == "show"):
                        return address + " 32"
                    if (args.split(" ")[1] == "export"):
                        return address + " 33 " + (args.split(" ")[2].strip())
                    if (args.split(" ")[1] == "import"):
                        return address + " 34 " + (args.split(" ")[2].strip())
            if (args.split(" ")[0].strip() == "get"):
                    if (args.split(" ")[1].strip() == "exports"):
                        return address + " 40 0 0"
            if (args.split(" ")[0].strip() == "help"):
                return address + " 255"
        except IndexError:
            print args
            return

#########################################
############# Commands ##################
#########################################

# Perm Blacklist
# 300 01 (IP, Con, BanTime, flag, Note) = blacklist insert | ginsert
# 300 02 (IP)                           = blacklist remove
# 300 03 (IP)                           = blacklist gremove
# 300 04                                = blacklist show

# 300 10 (IP, 0|1)                      = whitelist insert | ginsert
# 300 11 (IP, 0|1)                      = whitelist remove
# 300 12 (IP, 0|1)                      = whitelist gremove
# 300 13                                = whitelist show

# 300 20                                = Statistics

# 300 30 (NAME, IP-Range, flag, note)   = rangeban insert | ginsert (Name Range)
# 300 31                                = rangeban remove | gremove (Name)
# 300 32                                = rangeban show
# 300 33                                = rangeban export filename
# 300 34                                = rangeban import filename