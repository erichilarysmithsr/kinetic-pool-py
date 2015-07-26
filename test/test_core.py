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
 
class DeviceInfoTests(unittest.TestCase): 
	
	def test_json_decoding_full(self):
		data = '{ "wwn": "123abc", "addresses": [ "192.168.0.121", "192.168.1.121" ], "port": 9999 }'
		info = DeviceInfo.from_json(data)
		
		self.assertEqual(info.wwn, "123abc")
		self.assertEqual(info.addresses, ["192.168.0.121", "192.168.1.121"])
		self.assertEqual(info.port, 9999)
		
	def test_json_decoding_basic(self):
		data = '{ "wwn": "123abc", "addresses": [ "192.168.0.121" ] }'
		info = DeviceInfo.from_json(data)
		
		self.assertEqual(info.wwn, "123abc")
		self.assertEqual(info.addresses, ["192.168.0.121"])
		self.assertEqual(info.port, 8123)		
		
	def test_json_decoding_addresses_empty(self):
		data = '{ "wwn": "123abc", "addresses": [] }'
		with self.assertRaises(ValueError):
			DeviceInfo.from_json(data)	
			
	def test_json_decoding_addresses_missing(self):
		data = '{ "wwn": "123abc" }'
		with self.assertRaises(ValueError):
			DeviceInfo.from_json(data)	
			
	def test_json_decoding_wwn_missing(self):
		data = '{ "addresses": [ "192.168.0.121" ] }'
		with self.assertRaises(ValueError):
			DeviceInfo.from_json(data)								
		
	def test_json_encoding_full(self):
		x = DeviceInfo("123abc",  ["192.168.0.121", "192.168.1.121"], 9999)
		data = x.to_json()
		
		info = DeviceInfo.from_json(data)
		
		self.assertEqual(info.wwn, "123abc")
		self.assertEqual(info.addresses, ["192.168.0.121", "192.168.1.121"])
		self.assertEqual(info.port, 9999)
	
	def test_json_encoding_basic(self):
		x = DeviceInfo("123abc",  ["192.168.0.121"])
		data = x.to_json()
		
		info = DeviceInfo.from_json(data)
		
		self.assertEqual(info.wwn, "123abc")
		self.assertEqual(info.addresses, ["192.168.0.121"])
		self.assertEqual(info.port, 8123)		