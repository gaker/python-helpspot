#!/usr/bin/env python

import os
from setuptools import setup, find_packages

def long_description():
    output = []
    for filename in ('README.rst', ):
        f = open(os.path.join(os.path.dirname(__file__), filename))
        try:
            output.append(f.read())
        except FileNotFoundError:
            pass
        finally:
            f.close()
    return '\n\n'.join(output)


setup(
    name='helpspot',
    version='1.0',
    description='Python HelpSpot API Wrapper',
    long_description=long_description(),
    packages=['helpspot']
)

