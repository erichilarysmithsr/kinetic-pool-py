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

import memcache 
from exceptions import DeviceNotFound, InvalidEntry
from core import DeviceInfo


class MemcachedDeviceMap(object):
    
    AVAILABLE_PREFIX = 'kinetic/available/'
    MEMCACHE_SERVERS = ['127.0.0.1:11211']       
        
    def __init__(self, 
            prefix = AVAILABLE_PREFIX, 
            servers = MEMCACHE_SERVERS):   
        
        self.memcache_client = memcache.Client(servers, debug=0)
        self.available_prefix = prefix
    
    
    def __getitem__(self, device):
        # Spaces are repalced for '-' when adding the WWN to memcached     
        device = device.replace(" ", "-")     
        
        # Caching this will make normal behavior 1ms or 2 faster but 
        # will increase the cost of detecting a fail drive on all 
        # object-servers
        data = self.memcache_client.get(self.available_prefix + str(device))
        
        if data is None:
            raise DeviceNotFound("No entry for device %s." % device)
        
        info = DeviceInfo.from_json(data)
                    
        # sanitizing for memcached
        device = device.replace("-", " ")        
        wwn = info.wwn.replace("-", " ")
        
        # verify key matches entry 
        if wwn != device: raise InvalidEntry("WWN in entry does not match key.")
        
        return info
        
        
    def __setitem__(self, device, info):
        # Spaces are repalced for '-' when adding the WWN to memcached     
        device = device.replace(" ", "-")                  
                
        self.memcache_client.set(self.available_prefix + str(device), info.to_json())
        
        
    def __delitem__(self, device):
        # Spaces are repalced for '-' when adding the WWN to memcached     
        device = device.replace(" ", "-")     
        
        self.memcache_client.delete(self.available_prefix + str(device))

   