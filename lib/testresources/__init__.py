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
import testresources.tests.TestUtil as TestUtil

def test_suite():
    import testresources.tests
    return testresources.tests.test_suite()


class TestAdder(TestUtil.TestVisitor):

    def __init__(self, suite):
        self._suite = suite

    def visitCase(self, case):
        self._suite.addTest(case)


class OptimisingTestSuite(unittest.TestSuite):
    """A resource creation optimising TestSuite."""

    def adsorbSuite(self, suite):
        """adsorb all the tests in suite recursively.

        This allows full optimisation of the tests, but will remove
        any containing TestSuites, which might be extending unittest
        around those tests.
        """
        testAdder = TestAdder(self)
        TestUtil.visitTests(suite, testAdder)
        
    def run(self, result):
        for test in self._tests:
            if result.shouldStop:
                break
            current_resources = {}
            for attribute, resource in test._resources:
                if not resource in current_resources.keys():
                    current_resources[resource] = resource.getResource()
            test(result)
            for resource, value in current_resources.items():
                resource.finishedWith(value)
        return result
    
class TestLoader(unittest.TestLoader):
    """Custom TestLoader to set the right TestSuite class."""
    suiteClass = OptimisingTestSuite

class TestResource(object):
    """A TestResource for persistent resources needed across tests."""

    def _cleanResource(cls, resource):
        """Override this to class method to hook into resource removal."""
    _cleanResource = classmethod(_cleanResource)

    def dirtied(cls, resource):
        cls._dirty = True
    dirtied = classmethod(dirtied)

    def finishedWith(cls, resource):
        cls._uses -= 1
        if cls._uses == 0:
            cls._cleanResource(resource)
            cls._currentResource = None
        elif cls._dirty:
            cls._cleanResource(resource)
            cls.setResource()
    finishedWith = classmethod(finishedWith)

    def getResource(cls):
        if not hasattr(cls, "_uses"):
            cls._currentResource = None
            cls._dirty = False
            cls._uses = 0
        if cls._uses == 0:
            cls.setResource()
        cls._uses += 1
        return cls._currentResource
    getResource = classmethod(getResource)

    @classmethod
    def _makeResource(cls):
        """Override this to construct resources."""
        raise NotImplementedError("Override _makeResource to construct "
                                  "resources.")

    def setResource(cls):
        """Set the current resource to a new value."""
        cls._currentResource = cls._makeResource()
        cls._dirty = False
    setResource = classmethod(setResource)

class SampleTestResource(TestResource):

    @classmethod
    def _makeResource(cls):
        return "You need to implement your own getResource."


class ResourcedTestCase(unittest.TestCase):
    """A TestCase parent or utility that enables cross-test resource usage."""

    _resources = []

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.setUpResources(self)

    @staticmethod
    def setUpResources(case):
        for resource in case._resources:
            setattr(case, resource[0], resource[1].getResource())

    def tearDown(self):
        self.tearDownResources(self)
        unittest.TestCase.tearDown(self)

    @staticmethod
    def tearDownResources(case):
        for resource in case._resources:
            resource[1].finishedWith(getattr(case, resource[0]))
            delattr(case, resource[0])

