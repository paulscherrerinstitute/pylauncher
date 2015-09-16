#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'Readme.md')).read()

version = '1.0.00'
setup(name='pylauncher',
      version=version,
      description="Standard PSI tool for accessing GUIs",
      long_description=README,
      classifiers=[
          # Get strings from
          # http://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Testing',
          'Topic :: Utilities',
          'License :: OSI Approved :: MIT License'
      ],
      keywords='launcher, caqtdm, medm, PSI',
      author='PSI',
      url='https://github.psi.ch/projects/COS/repos/pylauncher/browse',
      license='MIT License',
      packages=find_packages(exclude=['*.tests']),
      platforms=["any"],
      )
