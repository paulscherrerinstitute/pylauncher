#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'Readme.md')).read()

setup(name='pylauncher',
      version='v0.9.3',
      description="Standard PSI tool for accessing GUIs",
      long_description=README,
      author='Rok Vintar',
      url='https://github.psi.ch/projects/COS/repos/pylauncher/browse',
      keywords='launcher, caqtdm, medm, PSI',
      packages=['pylauncher', 'pylauncher.convert'],
      package_dir={'pylauncher': 'src'},
      package_data={'pylauncher': ['resources/images/*.png', 'resources/qss/*.qss']},
      platforms=["any"],
      )
