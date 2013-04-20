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

import CP, FILEIO
import time, threading, sys, os, commands
from collections import deque

# BaseAddress
address = "300"
m_version ="0.2"
LOCK = threading.Lock()

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
        self.whitelist = []
        self.blacklist = []
        self.CP = CP

        CP.sLog.outString("Starting Firewall")
        return

    #Blacklist control
    def BlackListInsert(self, ip, connections, removetime, local): #001
        for item in self.whitelist:
            if (item[0] == ip):
                return
        for item in self.blacklist:
            if (item[0] == ip):
                return

        self.blacklist.append([ip, connections, removetime, local])
        self.ipt_b(ip)
        self.CP.ToLog("Debug", "IP: " + str(ip) + " banned.")
        #Send if ins't local
        if (local == 0):
            self.CP.ToSocket("300 1 " + str(ip) + " " + str(connections) + " " + removetime + " " + str(local))

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
        for item in self.blacklist:
            if (handler.ID == "SCK"):
                if (item[3] == 0):
                    handler.writeline ("300 1 "+ str(item[0]) + " " + str(item[1]) + " " + str(item[2]) + " " + str(item[3]))
            else:
                handler.writeline ("" + str(item[0]) + ", " + str(item[1]) + ", " + str(item[2]) + ", " + str(item[3]))

    # Whitelist control
    def WhiteListInsert(self, ip, local): #010
        for item in self.whitelist:
            if (item[0] == ip):
                return
        self.whitelist.append([ip, int(local)])
        self.BlackListRemove(ip)
        self.ipt_whitelist_insert(ip)
        if (local == 0):
            self.CP.ToSocket("300 10 " + str(ip) + " " + str(local))

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
                    handler.writeline ("300 10 "+ item[0] + " 0")
            else:
                if (item[1] == 0):
                    handler.writeline ("" + str(item[0]) + " Global "+ str(item[1]))
                else:
                    handler.writeline ("" + str(item[0]) + " Local "+ str(item[1]))
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
            for self.ip, self.connections, self.removetime, self.local in self.blacklist:
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
        self.loc = 0
        self.glob = 0
        self.all = 0
        for self.ip, self.connections, self.removetime, self.local in self.blacklist:
            self.all = self.all+1
            if self.local == 0:
                self.glob = self.glob+1
            else:
                self.loc = self.loc+1

        handler.writeline ("Blacklist: All %s - Local %s - Global %s" % (self.all, self.loc, self.glob))
        return


## define Checking-Thread
class Master(threading.Thread):
    check = True;
    wait=True;
    interval = 1;
    CP #Pointer for the CP

    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        self.initialized = False

        ## Setup the Buffer
        self.buffer = Fifo()

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        os.system ("/sbin/iptables --flush")
        self.firewall = Firewall(self.CP)

    def initfromdrone(self, args, handler):
        self.firewall.ShowWhitelist(handler);
        self.firewall.ShowBlacklist(handler);
        return

    def run(self):
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
                if item.strip() == "whitelist":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.WhiteListInsert(item.strip(), 1)

                if item.strip() == "blacklist":
                    t_ip = self.out[i].split(",")
                    for item in t_ip:
                        self.firewall.BlackListInsert(item.strip(), int(0), int(0), int(1))

                if item.strip() == "tcp_syncookies":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/tcp_syncookies")
                if item.strip() == "ip_forward":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/ip_forward")
                if item.strip() == "icmp_echo_ignore_broadcasts":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
                if item.strip() == "log_martians":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/log_martians")
                if item.strip() == "icmp_ignore_bogus_error_responses":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/icmp_ignore_bogus_error_responses")
                if item.strip() == "rp_filter":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/rp_filter")
                if item.strip() == "send_redirects":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/send_redirects")
                if item.strip() == "accept_source_route":
                    os.system ("echo " + self.out[i].strip() + " > /proc/sys/net/ipv4/conf/all/accept_source_route")
                if item.strip() == "icmp-limit":
                    os.system ("/sbin/iptables -A INPUT  -p icmp -m limit --limit " + self.out[i].strip() + "/second -j ACCEPT")
                    os.system ("/sbin/iptables -A INPUT  -p icmp -j DROP")
                if item.strip() == "portscan-detection":
                    # These rules add scanners to the portscan list, and log the attempt.
                    os.system ('/sbin/iptables -A INPUT   -p tcp -m tcp --dport 139 -m recent --name portscan --set -j LOG --log-prefix "Portscan:"')
                    os.system ("/sbin/iptables -A INPUT   -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP")
                    os.system ('/sbin/iptables -A FORWARD -p tcp -m tcp --dport 139 -m recent --name portscan --set -j LOG --log-prefix "Portscan:"')
                    os.system ("/sbin/iptables -A FORWARD -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP")
                if item.strip() == "portscan-ban-time":
                    os.system ("/sbin/iptables -A INPUT   -m recent --name portscan --rcheck --seconds %s -j DROP" % (self.out[i].strip()))
                    os.system ("/sbin/iptables -A FORWARD -m recent --name portscan --rcheck --seconds %s -j DROP" % (self.out[i].strip()))
                    os.system ("/sbin/iptables -A INPUT   -m recent --name portscan --remove")
                    os.system ("/sbin/iptables -A FORWARD -m recent --name portscan --remove")
                if item.strip() == "ping":
                    if self.out[i].strip() == "0":
                        os.system ("/sbin/iptables -A INPUT -p icmp --icmp-type echo-request -j REJECT --reject-with icmp-host-unreachable")
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
                    self.firewall.BlackListInsert(omv[2], int(omv[3]), omv[4], int(omv[5]))
                if omv[1] == "2":
                    self.firewall.BlackListRemove(omv[2])
                if omv[1] == "3":
                    self.CP.ToSocket("300 2 " + omv[2])
                    self.firewall.BlackListRemove(omv[2])
                if omv[1] == "4":
                    self.firewall.ShowBlacklist(handler);

                #WhiteList
                if omv[1] == "10":
                    self.firewall.WhiteListInsert(omv[2], int(omv[3]))
                if omv[1] == "11":
                    self.firewall.WhiteListRemove(omv[2])
                if omv[1] == "12":
                    self.CP.ToSocket("300 11 " + omv[2])
                    self.firewall.WhiteListRemove(omv[2])
                if omv[1] == "13":
                    self.firewall.ShowWhitelist(handler)

                #Statistics
                if omv[1] == "20":
                    self.firewall.ShowStatistics(handler)

        return
    def stop(self):
        self.firewall.BlackListRemoveAll()
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
                return "300 20"
            if (args.split(" ")[0] == "blacklist"):
                if (self.maxlen >= 1):
                    #Insert local (ip,connection)
                    if (args.split(" ")[1] == "insert"):
                        try:
                            return "300 1 " + args.split(" ")[2].strip() + " " + args.split(" ")[3].strip() + " " + str(int((time.time() + int(args.split(" ")[4].strip()))))  + " 1";
                        except IndexError:
                            return "300 1 " + args.split(" ")[2].strip()  + " 0 " + str(int((time.time() +86400))) + " 1";
                    #Insert global (ip,connection)
                    if (args.split(" ")[1] == "ginsert"):
                        try:
                            return "300 1 " + args.split(" ")[2].strip() + " " + args.split(" ")[3].strip() + " " + str(int((time.time() + int(args.split(" ")[4].strip()))))  + " 0";
                        except IndexError:
                            return "300 1 " + args.split(" ")[2].strip() + " 0 " + str(int((time.time() +86400))) + " 0";

                    #Remove local (ip)
                    if (args.split(" ")[1] == "remove"):
                        return "300 2 " + args.split(" ")[2].strip();
                    #Remove global (ip)gremove
                    if (args.split(" ")[1] == "gremove"):
                        return "300 3 " + args.split(" ")[2].strip();
                    #show the blacklist
                    if (args.split(" ")[1] == "show"):
                        return "300 4"

            if (args.split(" ")[0] == "whitelist"):
                if (self.maxlen >= 1):

                    if (args.split(" ")[1] == "insert"):
                        return "300 10 " + args.split(" ")[2].strip() + " 1";
                    if (args.split(" ")[1] == "ginsert"):
                        return "300 10 " + args.split(" ")[2].strip() + " 0";
                    if (args.split(" ")[1] == "remove"):
                        return "300 11 " + args.split(" ")[2].strip();
                    if (args.split(" ")[1] == "gremove"):
                        return "300 12 " + args.split(" ")[2].strip();
                    #show the whitelist
                    if (args.split(" ")[1] == "show"):
                            return "300 13"

        except IndexError:
            return

#########################################
############# Commands ##################
#########################################

# Perm Blacklist
# 300 01 (IP, NULL|CON, 0|1)    = blacklist insert | ginsert
# 300 02 (IP)                   = blacklist remove
# 300 03 (IP)                   = blacklist gremove
# 300 04                        = blacklist show

# Timed Blacklist
# 300 05 (IP, TimeStamp, 0|1)   = timedlist insert | ginsert
# 300 06 (IP)                   = timedlist remove
# 300 07 (IP)                   = timedlist gremove
# 300 08                        = timedlist show

# 300 10 (IP, 0|1)              = whitelist insert | ginsert
# 300 11 (IP, 0|1)              = whitelist remove
# 300 12 (IP, 0|1)              = whitelist gremove
# 300 13                        = whitelist show

# 300 20                        = Statistics
