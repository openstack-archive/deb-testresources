#!/usr/bin/env python

from distutils.core import setup

setup(name="testresources",
      version="0.1",
      description="Testresources, a pyunit extension for managing expensive "
                  "test resources",
      maintainer="Robert Collins",
      maintainer_email="robertc@robertcollins.net",
      url="http://www.robertcollins.net/unittest/testresources",
      packages=['testresources', 'testresources.tests'],
      package_dir = {'':'lib'}
      )
