from setuptools import setup, find_packages

with open('requirements.txt', 'r') as f:
    requires = [x.strip() for x in f if x.strip()]

from kineticpool import __version__

setup(
    # overview    
    name = 'kineticpool',
    description = "A python connections manager for Kinetic devices",

    # technical info
    version = __version__,
    packages=find_packages(exclude=['test']),
    #requires = requires,
    install_requires=requires,

    # features
     entry_points = {
        'console_scripts': [ 'kinetic-discovery = kineticpool.cmd:main' ],
    },

    # copyright
    author='Ignacio Corderi',
    license='MIT',

    # more info
    url = 'https://github.com/Seagate/kinetic-pool-py',

    # categorization
    keywords = ('kinetic connection pool storage key/value seagate'),
    classifiers  = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
     ],
)
