# **Kinetic-pool-py**
[![Travis](https://img.shields.io/travis/Seagate/kinetic-pool-py.svg)](https://travis-ci.org/Seagate/kinetic-pool-py)
[![PyPI](https://img.shields.io/pypi/v/kineticpool.svg)](https://pypi.python.org/pypi/kineticpool/)
[![PyPI](https://img.shields.io/pypi/l/kineticpool.svg)](https://github.com/Seagate/kinetic-pool-py/blob/master/LICENSE/mit.md)

Introduction
============
This library is a connection pool manager for **Kinetic** devices. 
You can find more information on the [kinetic-protocol] or the [kinetic-py] client on their respective repos. 

[kinetic-protocol]:(https://github.com/Seagate/kinetic-protocol)
[kinetic-py]:(https://github.com/Seagate/kinetic-py)


Requirements
============

This project requires `memcached`


Installing latest stable release
================================
    pip install kineticpool


Installing from Source
======================

    git clone https://github.com/Seagate/kinetic-pool-py.git
    cd kinetic-pool-py
    python setup.py develop


Getting Started
===============

There are two components, the _library_ and the `kinetic-discovery` daemon.

## The library

```python
import kineticpool

mgr = kineticpool.ConnectionManager()
c = mgr.get_connection('some-wwn')
c.put('hello', 'world')
c.close()
```

## The `kinetic-discovery` daemon
This daemon will listen for multicasts coming from the kinetic devices and will register them on _memcached_.

    kinetic-discovery en0 


License
-------

This project is licensed under The MIT License (MIT)
* [Markdown](LICENSE/MIT.md) version
* [Original](LICENSE/MIT.txt) version
