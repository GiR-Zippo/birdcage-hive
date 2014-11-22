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
import boto.ec2
from SYSTEM.CONFIG import Config
import threading
import time

#Base-Address
#Please read the read.me in the root-dir
address = "402"
m_version ="0.1"

#Workerthread to assemble an instance
class AWSThread(threading.Thread):
    def __init__(self, conn, template, address, InstanceName):
        self.connection = conn
        self.template = template
        self.address = address
        self.InstanceName = self.template.get('instance_name')
        threading.Thread.__init__(self)
        return

    def run(self):
        reservation = self.connection.run_instances(
        self.template.get('image_id'),
        key_name=self.template.get('key_name'),
        instance_type=self.template.get('instance_type'),
        security_groups=[self.template.get('security_groups')])

        instance = reservation.instances[0]
        status = instance.update()

        while status == 'pending':
            time.sleep(10)
            status = instance.update()

        if (self.InstanceName):
            instance.add_tag("Name", self.InstanceName)
            instance.update()

        if (self.address):
            self.connection.associate_address(instance.id, self.address.public_ip)
            instance.update()
        print str(instance) + " " + instance.state
        return

class AWS:
    def __init__(self, Master, CP):
        self.connection = None
        self.Master = Master
        self.CP = CP
        self.msg = ''
        return

    def GetInstanceFile(self, file, handler):
        try:
            fp = open('%s/%s' % (self.Master.PATH, file), 'rb')
        except:
            if (handler.ID != 'SCK'):
                handler.writeline("File not found error.")
            return False
        self.msg = fp.readlines()
        fp.close()
        return True

    def SetConnection(self, region, id, key):
        self.connection = boto.ec2.connect_to_region(region, aws_access_key_id = id, aws_secret_access_key = key)
        return

    ##################################################################
    # Pri-Functions
    ##################################################################
    def GetStatus(self, handler):
        reservations = self.connection.get_all_reservations()
        for instances in reservations:
            for inst in instances.instances:
                stat = ("%s %s %s" % (inst.instance_type, inst.ip_address, inst.state))
                handler.writeline (stat)
        return

    ##################################################################
    # Funktionen die NUR von der Addressline kommen können
    ##################################################################
    def CreateInstanceFromParamString(self, handler, image_id, instance_type, security_groups, key_name, instance_name):
        AWSTEMPLATE = {
        'image_id' : image_id,
        'instance_type' : instance_type,
        'security_groups' : security_groups,
        'key_name' : key_name,
        'instance_name' : instance_name,
        }
        helper = AWSThread(self.connection, AWSTEMPLATE, "", "")
        helper.start()
        return

    def StopInstanceByName(self, handler, name):
        inst = self._getInstanceByName(name)
        if (inst != None):
            inst.stop()
            inst.update()
            return
        return

    def TerminateInstanceByName(self, handler, name):
        inst = self._getInstanceByName(name)
        if (inst != None):
            inst.terminate()
            inst.update()
            return
        return

    def GetIPForInstance(self, handler, args):
        iName = args.split(" ")[0].strip()
        if (not 'SCK' in handler.ID ):
            iAck  = args[len(args.split(" ")[0])+1:]
            while True:
                if (self._getInstanceByName(iName) != None):
                    iAck = self.Interpreter(iAck, "IP", self._getInstanceByName(iName).ip_address)
                    break
            self.CP.command(iAck, "NULL")
        return

    #Ersetze den type
    def Interpreter(self, input, type, arg):
        if ("IP" == type):
            input = input.replace('&IP', arg)
        return input

    '''
    Das bedarf einer gaaaaaanz gründlichen Überarbeitung


    def StartInstanceByName(self, name, handler):
        inst = self._getInstanceByName(name)
        if (inst != None):
            inst.start()
            inst.update()
            handler.writeline (inst.tags['Name'] + " " + inst.state)
            return
        return

    def TerminateInstanceByIP(self, ip, handler):
        self.connection.release_address(ip)
        inst = self._getInstanceByName(name)
        if (inst != None):
            inst.terminate()
            inst.update()
            if (handler == "CLI"):
                handler.writeline (inst.tags['Name'] + " " + inst.state)
            return
        return

    def CreateInstanceFromFile(self, name, handler, instanceName = '', radd = '', rsubadd = ''):
        config = CONFIG.Config('%s/%s' % (self.Master.PATH, name))
        if (config.CheckFile() == False):
            handler.writeline ("File not found Error...")
            return
        AWSTEMPLATE = {
        'image_id' : config.GetItem('image_id'),
        'instance_type' : config.GetItem('instance_type'),
        'security_groups' : config.GetItemList('security_groups'),
        'key_name' : config.GetItem('key_name'),
        }

        #Init the helper
        address = self._getUnusedOrCreateAddress()
        #helper = AWSThread(self.connection, AWSTEMPLATE, address)
        #helper.start()

        cargs = ("%s %s %s" %(radd, rsubadd, address.public_ip))
        if (handler.ID == "CLI"):
            handler.writeline ("Instance started...")
        if (handler.ID == "NULL"):
            self.CP.command(cargs, "NULL")
        if (handler.ID == "SCK"):
            handler.writeline(cargs)
        return
    '''

##################################################################
# Sec-Functions
##################################################################
    def _getInstanceByName(self, Name):
        reservations = self.connection.get_all_reservations()
        for instances in reservations:
            for inst in instances.instances:
                try:
                    if Name in inst.tags['Name']:
                        return inst
                except KeyError:
                    pass
        return None

'''
    def _getInstanceStatusByName(self, name):
        instances = self.connection.get_all_instances()
        r = instances[0]
        for inst in r.instances:
            if (inst.tags['Name'].strip() == name):
                return inst.state
        return None

    def _getUnusedOrCreateAddress(self):
        addlist = self.connection.get_all_addresses()
        for address in addlist:
            if (address.instance_id == None):
                return address
        address = self.connection.allocate_address()
        return address
'''
##################################################################
# MASTER
##################################################################

class Master:
    CP #Pointer for the CP
    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        self.AWS = AWS(self, CP)
        self.PATH = ''
        self.region = ''
        self.aws_access_key_id = ''
        self.aws_secret_access_key = ''
        return

    def start(self):
        self.AWS.SetConnection(self.region, self.aws_access_key_id, self.aws_secret_access_key)
        return

    def initfromdrone(self, args, handler):
        return

    def config(self, args, CP):
        config = Config("./CONFIGS/mod_AWS.conf")
        #self.PATH = config.GetItem('data-folder')
        self.region = config.GetItem("region")
        self.aws_access_key_id = config.GetItem("aws_access_key_id")
        self.aws_secret_access_key = config.GetItem("aws_secret_access_key")
        return

    def command(self, args, handler):
        omv = args.split(" ")
        if omv[0] == address:
            if omv[1] == "1":
                self.AWS.GetStatus(handler)
                return

            #Die Commands können nicht von der Console abgearbeitet werden, würde tödlich ausgehen
            elif omv[1] == "10":                                #Image          Type            Rule            Key             Name
                self.AWS.CreateInstanceFromParamString(handler, omv[2].strip(), omv[3].strip(), omv[4].strip(), omv[5].strip(), omv[6].strip())
            elif omv[1] == "12":                     #Name
                self.AWS.StopInstanceByName(handler, omv[2].strip())
            elif omv[1] == "13":                          #Name
                self.AWS.TerminateInstanceByName(handler, omv[2].strip())
            elif omv[1] == "20":                   #ArgsList
                self.AWS.GetIPForInstance(handler, args[len(omv[0].strip()) + len(omv[1].strip()) + 2:])
                return
        return

    def stop(self):
        return True

    def Event(self):
        return

#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" "))
            if (args.split(" ")[0] == "status"):
                return "402 1"
            #if (args.split(" ")[0] == "start"):
            #    return "402 2 " + args.split(" ")[1]
            #if (args.split(" ")[0] == "stop"):
            #    return "402 3 " + args.split(" ")[1]
            #if (args.split(" ")[0] == "terminate"):
            #    return "402 4 " + args.split(" ")[1]
            #if (args.split(" ")[0] == "load"):
            #    return "402 5 " + args.split(" ")[1]
        except IndexError:
            print args
            return

#####################################################
# Commands
#####################################################
#
#Wenn erfoderlich können Werte zurueckkommen
#####################################################
# 1   =  status
# 2   =  start prepared instance by Name
# 3   =  stop running instance by Name
# 4   =  sterminate an instance
# 5   =  load instance template from file (File, {Name}, {ADDRESS}, {SUBADDRESS}) ret (IP)
# 6   =  create instance

#####################################################
#Interne Addressen
#####################################################
# 10  =  Instanz via Parameter erstellen
