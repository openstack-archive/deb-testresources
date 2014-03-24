#!/usr/bin/env python

from setuptools import setup
import os.path

description = open(os.path.join(os.path.dirname(__file__), 'README'), 'rt').read()

setup(name="testresources",
      version="0.2.7",
      description="Testresources, a pyunit extension for managing expensive "
                  "test resources",
      long_description=description,
      maintainer="Testresources developers",
      maintainer_email="https://launchpad.net/~testresources-developers",
      url="https://launchpad.net/testresources",
      packages=['testresources', 'testresources.tests'],
      package_dir = {'':'lib'},
      keywords="unittest testing fixtures",
      classifiers = [
          'Development Status :: 6 - Mature',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Software Development :: Testing',
          ],
      )
