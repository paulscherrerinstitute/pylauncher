#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'Readme.md')).read()

setup(name='pylauncher',
      version='1.0.00',
      description="Standard PSI tool for accessing GUIs",
      long_description=README,
      author='PSI',
      url='https://github.psi.ch/projects/COS/repos/pylauncher/browse',
      licence='GPLv3+',
      keywords='launcher, caqtdm, medm, PSI',
      classifiers=[
          # Get strings from
          # http://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
      ],
      #packages=find_packages(exclude=['*.tests']),
      packages=['pylauncher'],
      package_dir={'pylauncher': 'pylauncher'},
      package_data={'pylauncher': ['res/images/*.png', 'res/qss/*.qss']},
      platforms=["any"],
      )
