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

import unittest
from kineticpool.core import DeviceInfo
from kineticpool import exceptions
from kineticpool import ConnectionManager
from kineticpool.maps import MemcachedDeviceMap
from kinetic import Client

class ConnectionManagerTests(unittest.TestCase): 

	def setUp(self):
		c = Client()
		c.connect()
		self.device = c.config.worldWideName
		info = DeviceInfo(wwn=self.device, addresses=["127.0.0.1"])
		m = MemcachedDeviceMap()
		m[self.device] = info

	def test_valid_connection(self):		
		mgr = ConnectionManager()
		c = mgr.get_connection(self.device)
		c.put('hello', 'world')
		
	def test_not_found(self):		
		mgr = ConnectionManager()
		with self.assertRaises(exceptions.DeviceNotFound):
			mgr.get_connection("not_found")
			
	def test_wrong_device(self):		
		info = DeviceInfo(wwn="wrong", addresses=["127.0.0.1"])
		mgr = ConnectionManager()
		mgr.device_map["wrong"] = info	
		with self.assertRaises(exceptions.WrongDeviceConnection):
			mgr.get_connection("wrong")	
			
	def test_device_unavailable(self):
		info = DeviceInfo(wwn="unavailable", addresses=["192.168.0.254"])
		mgr = ConnectionManager(connect_timeout=0.01)
		mgr.device_map["unavailable"] = info				
		with self.assertRaises(exceptions.DeviceNotAvailable):
			mgr.get_connection("unavailable")	
			
	def test_persist_connection(self):		
		mgr = ConnectionManager(persist_connection=True)		
		c1 = mgr.get_connection(self.device)
		c2 = mgr.get_connection(self.device)
		self.assertEqual(c1, c2)
		
	def test_non_persistent_connection(self):		
		mgr = ConnectionManager(persist_connection=False)		
		c1 = mgr.get_connection(self.device)
		c2 = mgr.get_connection(self.device)
		self.assertNotEqual(c1.connection_id, c2.connection_id)		
									
		
		
				
	
		
		