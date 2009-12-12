#!/usr/bin/env python

from distutils.core import setup

setup(name="testresources",
      version="0.2.1",
      description="Testresources, a pyunit extension for managing expensive "
                  "test resources",
      maintainer="Test Resources developers",
      maintainer_email="https://launchpad.net/~testresources-developers",
      url="https://launchpad.net/testresources",
      packages=['testresources', 'testresources.tests'],
      package_dir = {'':'lib'}
      )
