# Copyright (c) 2015 Seagate Technology

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#@author: Ignacio Corderi

import kinetic
import kineticpool
import eventlet
import time
import threading
import socket
from kinetic import Client
import logging
import struct
import json
from kineticpool.maps import MemcachedDeviceMap
from kineticpool.core import DeviceInfo
from kineticpool.exceptions import DeviceNotFound, InvalidEntry
import sys 
from dateutil import parser
import netifaces

eventlet.monkey_patch()

class DiscoveredDrive(DeviceInfo):

    def __init__(self, wwn, serial_number, manufacturer, firmware_version, protocol_version, port, addresses):
        super(DiscoveredDrive, self).__init__(wwn, addresses, port)
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.firmware_version = firmware_version
        self.protocol_version = protocol_version
        
    @staticmethod
    def from_json(raw): 
        data = json.loads(raw)
        info = DiscoveredDrive(data['world_wide_name'],
                               data['serial_number'], data['manufacturer'],
                               data['firmware_version'], data['protocol_version'],
                               data['port'],
                               [str(iface['ipv4_addr']) for iface in data['network_interfaces']])            
        if 'last_seen' in data:
            info.last_seen = parser.parse(data['last_seen'])
            
        return info                                           

class MemcachedHandler(object):
    
    def __init__(self, verify_addresses=True, logger=None): 
       if logger == None: logger = logging.getLogger(__name__)
       self.logger = logger
       self.verify_addresses = verify_addresses
        
       self.device_map = MemcachedDeviceMap()

    def detected(self, drive): 
        # Check existing data
        try:
            info = self.device_map[drive.wwn]
            
            # Verify connection issues     
            #
            # Interfaces coming from the drive will be trusted as correct
            # although they might not be accesible
            # if #known > #announced, all extra addresses will be dropped
            if self.verify_addresses:    
                known = set(info.addresses)
                announced = set(drive.addresses) 
                if known != announced:
                    # This can happen when the device can't be accessed
                    # through all of its interfaces                  
                    missing = announced - known
                    for a in missing: 
                        try:
                            c = Client(a, drive.port)
                            c.connect()
                            # interface is back up 
                            self.logger.info('Device interface %s is back online: %s',
                                a, drive)   
                            c.close()                                 
                        except: 
                            # Interface still down
                            drive.addresses.remove(a)     
            
        except InvalidEntry as ex:
            # Might happen that some script/test/old version 
            # wrote some garbage, no need to clean, we will overwrite 
            self.logger.warn('Corrupted entry detected: %s' % ex)
        except DeviceNotFound:
            # This happens when a device goes offline
            # and then comes back up
            self.logger.info('Device back online: %s' % drive)            
                
        self.device_map[drive.wwn] = drive
        
    def new_drive(self, drive): 
        self.logger.info('Device found: %s' % drive)
        self.device_map[drive.wwn] = drive
        
class FileHandler(object):
    
    def __init__(self, path): 
        self.fd = open(path, 'w')            
    
    def new_drive(self, drive): 
        self.fd.write("%s\n" % drive.to_json())
        self.fd.flush()  

class KineticDiscoveryManager(object):
    
    MCAST_ADDR = '239.1.2.3'
    MCAST_PORT = 8123
    
    def __init__(self, interface, logger=None): 
        self.interface = interface
        self.drives = {}     
        self.handlers = []   
        if logger == None: logger = logging.getLogger(__name__)
        self.logger = logger
    
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def run(self): 
        s = joinMcast(self.MCAST_ADDR, self.MCAST_PORT, self.interface)
        t = threading.Thread(target=self._listen, args=(s,))
        t.daemon = True
        t.start()
        t.join()
        s.close()
             
    def _listen(self, s):
        while True:
            raw = s.recv(64 * 2 ** 10)            
        
            d = DiscoveredDrive.from_json(raw)
                
            # notify handlers
            for h in self.handlers:
                if hasattr(h, "detected"): h.detected(d)
                if not (d.wwn in self.drives): 
                    h.new_drive(d)                 
                                
            # update record     
            self.drives[d.wwn] = d

def joinMcast(mcast_addr,port,if_ip):
    """
    Returns a live multicast socket
    mcast_addr is a dotted string format of the multicast group
    port is an integer of the UDP port you want to receive
    if_ip is a dotted string format of the interface you will use
    """

    #create a UDP socket
    mcastsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    #allow other sockets to bind this port too
    mcastsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    #explicitly join the multicast group on the interface specified
    mcastsock.setsockopt(socket.SOL_IP,socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(mcast_addr)+socket.inet_aton(if_ip))

    #finally bind the socket to start getting data into your socket
    mcastsock.bind((mcast_addr,port))

    return mcastsock

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Kinetic Multicast Discovery Tool')
    parser.add_argument('interface', metavar='interface', default=None,
                       help='Interface to listen on (i.e. en0)')
    parser.add_argument('--drives', dest='drives', default=None,
                       help='Output discovered devices to a file')
    parser.add_argument('--log', dest='loglevel', default="info",
                       help='Logging level (default=warning)')
    parser.add_argument('--version', action='version', version='%(prog)s ' + kineticpool.__version__)
    
    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(asctime)-8s %(levelname)s: %(message)s', 
                        datefmt="%H:%M:%S", 
                        level=logging.INFO)

    LOG = logging.getLogger(__name__)
   
    if args.interface != None:
        address = netifaces.ifaddresses(args.interface)[netifaces.AF_INET][0]['addr']       
    else: 
        LOG.error("Interface required!")
        return 1
        
    LOG.info('Listening on %s (%s)' % (args.interface, address))        
   
    mgr = KineticDiscoveryManager(address, logger=LOG)
    mgr.add_handler(MemcachedHandler(logger=LOG))
    if args.drives != None:
        mgr.add_handler(FileHandler(args.drives))
    
    try:
        mgr.run()
    except KeyboardInterrupt:
        LOG.info("Process terminated by user.")
                    
if __name__ == '__main__':
    main()
