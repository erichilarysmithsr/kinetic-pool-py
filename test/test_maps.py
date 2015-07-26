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
from kineticpool.maps import MemcachedDeviceMap
from kineticpool import exceptions

class MemcachedDeviceMapTests(unittest.TestCase): 

	def test_set_entry(self):
		info = DeviceInfo(wwn="123abc", addresses=["127.0.0.1"])
		m = MemcachedDeviceMap()				
		m["123abc"] = info
		
	def test_get_entry(self):
		m = MemcachedDeviceMap()				
		info = m["123abc"]
		
		self.assertEqual(info.wwn, "123abc")
		self.assertEqual(info.addresses, ["127.0.0.1"])
		self.assertEqual(info.port, 8123)
	
	def test_verify_entry(self):
		info = DeviceInfo(wwn="123abc", addresses=["127.0.0.1"])
		m = MemcachedDeviceMap()				
		m["123abc"] = info		
		info2 = m["123abc"]
		
		self.assertEqual(info.wwn, info2.wwn)
		self.assertEqual(info.addresses, info2.addresses)
		self.assertEqual(info.port, info2.port)
		
	def test_invalid_wwn(self):
		info = DeviceInfo(wwn="123abc", addresses=["127.0.0.1"])
		m = MemcachedDeviceMap()				
		m["foo"] = info		
		
		with self.assertRaises(exceptions.InvalidEntry):
			m["foo"]
		
				
	
		
		