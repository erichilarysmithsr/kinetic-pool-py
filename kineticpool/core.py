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

import json
from datetime import datetime
from dateutil import parser 
 
def json_serialize(obj):
    if isinstance(obj, datetime):
        s = obj.isoformat()
        return s
    raise TypeError ("Type is not serializable")  
  
class DeviceInfo(object):
    
    def __init__(self, wwn, addresses, port=8123):
        if addresses == None: raise ValueError("Addresses can't be None")
        if len(addresses) == 0: raise ValueError("Addresses can't be None")
        self.wwn = wwn
        self.addresses = list(set(addresses)) # remove duplicates
        self.port = port 
        self.last_seen = datetime.now()
       
    @staticmethod        
    def from_json(s): 
        x = json.loads(s)
        if not "wwn" in x: raise ValueError("Missing wwn information") 
        if not "addresses" in x: raise ValueError("Missing address information") 
        info = DeviceInfo(x["wwn"], x["addresses"], int(x.get("port", 8123)))
        if 'last_seen' in x:
            info.last_seen = parser.parse(x['last_seen'])
        return info
                 
    def to_json(self):
        return json.dumps(self.__dict__, default=json_serialize)      
        
    def __str__(self):
        info = { "wwn": self.wwn, "addresses": self.addresses } 
        if self.port != 8123: info["port"] = self.port
        return json.dumps(info)