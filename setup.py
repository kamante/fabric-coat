#coding: utf-8
import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "fabric-coat",
    version = "0.2.1",
    author = "Rasmus Schlünsen, Mads Sülau Jørgensen",
    author_email = "rs@konstellation.dk, msj@konstellation.dk",
    description = ("Deployment helpers for fabric"),
    license = "BSD",
    keywords = "fabric coat deployment rsync helper",
    url = "https://bitbucket.org/madssj/fabric-coat",
    packages=['coat', ],
    long_description=read('README'),
    package_dir = {'': 'src'},
    install_requires = ['fabric >= 1.3'],
)
