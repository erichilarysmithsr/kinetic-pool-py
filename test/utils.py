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

import errno
import os
import subprocess
import shutil
import socket
import tempfile
import time
import unittest

KINETIC_JAR = os.environ.get('KINETIC_JAR')
KINETIC_PORT = os.environ.get('KINETIC_PORT', 9123)
KINETIC_HOST = os.environ.get('KINETIC_HOST', 'localhost')

class SimulatorRuntimeError(RuntimeError):

    def __init__(self, stdout, stderr, returncode):
        super(SimulatorRuntimeError, self).__init__(stdout, stderr, returncode)
        # reopen file's in read mode
        self.stdout = open(stdout.name).read()
        self.stderr = open(stderr.name).read()
        self.returncode = returncode

    def __str__(self):
        return '\n'.join([
            'Simulator exited abnormally',
            'STDOUT:\n%s' % self.stdout,
            'STDERR:\n%s' % self.stderr,
            'RETURNCODE: %s' % self.returncode
        ])
        
def _find_kinetic_jar(jar_path):
    jar_path = os.path.abspath(os.path.expanduser(
                os.path.expandvars(jar_path)))
    
    if not os.path.exists(jar_path):
        if 'KINETIC_JAR' not in os.environ:
            raise KeyError('KINETIC_JAR environment variable is not set')
        else:
            msg = "%s: '%s'" % (os.strerror(errno.ENOENT), jar_path)
            raise IOError(errno.ENOENT, msg)
    return jar_path        
 
class Simulator(object):
    
    def __init__(self, port=KINETIC_PORT):
        self.host = "127.0.0.1"
        self.port = port
        self.process = None
        self.jar_path = _find_kinetic_jar(KINETIC_JAR)
        self.datadir = None
        self.stdout = self.stderr = None
        
    def shutdown(self):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
            self.process.wait()
        [f.close() for f in (self.stdout, self.stderr) if f]
        if self.datadir:
            shutil.rmtree(self.datadir)
            
    def start(self):
        try:
            backoff = 0.1
            while True:
                sock = socket.socket()
                try:
                    sock.connect((self.host, self.port))
                except socket.error:
                    if backoff > 2:
                        raise
                else:
                    # k, we can connect
                    sock.close()
                    break
                self._check_simulator()
                time.sleep(backoff)
                backoff *= 2  # double it!
        except:
            if hasattr(self, 'stdout'):
                try:
                    raise SimulatorRuntimeError(self.stdout, self.stderr,
                                                self.process.returncode)
                except:
                    # this is some dodgy shit to setup the re-raise at the bottom
                    pass
            self.shutdown()
            raise  
                
    def _check_simulator(self):
        if not self.process:
            self.datadir = tempfile.mkdtemp()
            self.stdout = open(os.path.join(self.datadir, 'simulator.log'), 'w')
            self.stderr = open(os.path.join(self.datadir, 'simulator.err'), 'w')
            args = ['java', '-jar', self.jar_path, str(self.port), self.datadir]
            self.process = subprocess.Popen(args, stdout=self.stdout.fileno(),
                                            stderr=self.stderr.fileno())
        if self.process.poll():
            raise SimulatorRuntimeError(self.stdout, self.stderr, self.process.returncode)