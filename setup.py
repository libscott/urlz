#!/usr/bin/env python

import os.path
from setuptools import setup, find_packages


description = ('Minimalist immutable REST api client builder; '
               'JQuery for REST apis.')


wd = os.path.dirname(__file__)

# Get requirements
requirements_path = os.path.join(wd, 'requirements.txt')
requirements = open(requirements_path).readlines()

# Get version
initpy_path = os.path.join(wd, 'urlz', '__init__.py')
version = [l for l in open(initpy_path) if l.startswith('__version__')]
version = version[0][:-1].split('=', 1)[1].strip().strip('"')


setup(
    name='urlz',
    description=description,
    version=version,
    author='Scott Sadler',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    test_suite="test",
)
