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

from device import MemcachedDeviceMap
from kinetic import Client
from eventlet import sleep, Timeout
from exceptions import WrongDeviceConnection, DeviceNotAvailable

class ConnectionManager(object):
	
    def __init__(self, conf, logger):
        self.logger = logger
        self.persist_connection = bool(conf.get('persist_connection', False))
        self.connect_timeout = int(conf.get('connect_timeout', 3))
        self.response_timeout = int(conf.get('response_timeout', 30))
        self.connect_retry = int(conf.get('connect_retry', 3))
        self.device_map = MemcachedDeviceMap(conf, logger)
        self.conn_pool = {}
        		
    def _new_connection(self, device, **kwargs):
        kwargs.setdefault('connect_timeout', self.connect_timeout)
        kwargs.setdefault('response_timeout', self.response_timeout)
        device_info = self.device_map[device]
        for i in range(1, self.connect_retry + 1):
            try:
                c = Client(device_info.host, device_info.port,**kwargs)
                c.connect()
                if c.config.worldWideName != device_info.wwn: 
                    raise WrongDeviceConnection("Drive at %s is %s, expected %s." % 
                        c, c.config.worldWideName, device_info.wwn)
            except Timeout:
                self.logger.warning('Drive %s connect timeout #%d (%ds)' % (
                    device, i, self.connect_timeout))
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