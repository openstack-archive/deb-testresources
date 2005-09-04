#
#  testresources: extensions to python unittest to allow declaritive use
#  of resources by test cases.
#  Copyright (C) 2005  Robert Collins <robertc@robertcollins.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import unittest

def test_suite():
    import testresources.tests
    return testresources.tests.test_suite()


class OptimisingTestSuite(unittest.TestSuite):
    """A resource creation optimising TestSuite."""
    
class TestLoader(unittest.TestLoader):
    """Custom TestLoader to set the right TestSuite class."""
    suiteClass = OptimisingTestSuite

class TestResource(object):
    """A TestResource for persistent resources needed across tests."""

    _currentResource = None
    _uses = 0

    def _cleanResource(cls, resource):
        """Override this to class method to hook into resource removal."""
    _cleanResource = classmethod(_cleanResource)

    def finishedWith(cls, resource):
        cls._uses -= 1
        if cls._uses == 0:
            cls._cleanResource(resource)
            cls._currentResource = None
    finishedWith = classmethod(finishedWith)

    def getResource(cls):
        if cls._uses == 0:
            cls._currentResource = cls._makeResource()
        cls._uses += 1
        return cls._currentResource
    getResource = classmethod(getResource)

    def _makeResource(cls):
        return "You need to implement your own getResource."
    _makeResource = classmethod(_makeResource)
