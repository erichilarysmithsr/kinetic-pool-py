import kinetic
import kineticpool
import eventlet
import time
import threading
import socket
from kinetic import AsyncClient
import logging
import struct
import json
from kineticpool.maps import MemcachedDeviceMap
from kineticpool.core import DeviceInfo
import sys 

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
        return DiscoveredDrive(data['world_wide_name'],
                               data['serial_number'], data['manufacturer'],
                               data['firmware_version'], data['protocol_version'],
                               data['port'],
                               [str(iface['ipv4_addr']) for iface in data['network_interfaces']])            

    def __str__(self):
        return 'WWN={5}, SN={0}, Version={1}, Proto={2}, Port={3}, Addresses={4}'.format(
                 self.serial_number, self.firmware_version, self.protocol_version,
                 self.port, self.addresses, self.wwn)

class MemcachedHandler(object):
    
    def __init__(self): 
       self.device_map = MemcachedDeviceMap()
    
    def detected(self, drive): 
        self.device_map[drive.wwn] = drive
        
    def new_drive(self, drive): pass 
    
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
        if logger == None:
            logger = logging.getLogger(__name__)
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
             
            if not (d.wwn in self.drives):                                      
                self.logger.info(d)                 
            else:
                if self.drives[d.wwn].addresses[0] != d.addresses[0]:
                    self.logger.warn('Address changed!! %s' % d)
                                
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
    parser.add_argument('interface', metavar='interface',
                       help='Address of interface to listen on (i.e. 192.168.0.1)')
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
   
    mgr = KineticDiscoveryManager(args.interface, logger=LOG)
    mgr.add_handler(MemcachedHandler())
    if args.drives != None:
        mgr.add_handler(FileHandler(args.drives))
    mgr.run()

if __name__ == '__main__':
    main()
