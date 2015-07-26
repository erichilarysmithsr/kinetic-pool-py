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

import logging
from eventlet import sleep, Timeout
from kinetic import Client

from exceptions import WrongDeviceConnection, DeviceNotAvailable
from maps import MemcachedDeviceMap

LOG = logging.getLogger(__name__)

class ConnectionManager(object):
	
    def __init__(self, 
            persist_connection = False, 
            connect_timeout = 3, 
            connect_retry = 3, 
            map_obj = None, 
            logger = LOG):
        self.logger = logger
        self.persist_connection = persist_connection
        self.connect_timeout = connect_timeout
        self.connect_retry = connect_retry
        if map_obj == None:
            self.device_map = MemcachedDeviceMap()
        else: self.device_map = map_obj
        self.conn_pool = {}
        		
    def _new_connection(self, device, **kwargs):
        kwargs.setdefault('connect_timeout', self.connect_timeout)
        info = self.device_map[device]
        for i in range(1, self.connect_retry + 1):
            try:
                c = Client(info.addresses[0], info.port,**kwargs)
                c.connect()
                if c.config.worldWideName != info.wwn: 
                    raise WrongDeviceConnection("Drive at %s is %s, expected %s." % 
                        (c, c.config.worldWideName, info.wwn))
                return c                        
            except Timeout:
                self.logger.warning('Drive %s connect timeout #%d (%ds)' % (
                    device, i, self.connect_timeout))
            except WrongDeviceConnection: 
                self.logger.exception('Drive %s has an incorrect WWN' % (device))
                self.faulted_device(device)      
                raise        
            except Exception:
                self.logger.exception('Drive %s connection error #%d' % (
                    device, i))
            if i < self.connect_retry:
                sleep(1)
        msg = 'Unable to connect to drive %s after %s attempts' % (
            device, i)
        self.logger.error(msg)
        self.faulted_device(device)        
        raise DeviceNotAvailable(msg)    

    def get_connection(self, device):
        conn = None
        if self.persist_connection:        
            try:
                conn = self.conn_pool[device]
            except KeyError:
                pass
            if conn and conn.faulted:
                conn.close()
                conn = None
            if not conn:
                conn = self.conn_pool[device] = self._new_connection(device)
        else:
            conn = self._new_connection(device)                        
        return conn              
        
    def faulted_device(self, device): 
        del self.device_map[device]
        if self.persist_connection:
            del self.conn_pool[device]    