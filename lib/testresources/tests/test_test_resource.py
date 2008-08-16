
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

import testresources
from testresources.tests import SampleTestResource
import unittest


class TestTestResource(unittest.TestCase):

    def testImports(self):
        from testresources import TestResource

    def testDefaultResource(self):
        self.assertRaises(NotImplementedError,
                          testresources.TestResource.getResource)
        self.failUnless(
            hasattr(testresources.TestResource, "_currentResource"))
        self.failUnless(hasattr(testresources.TestResource, "_uses"))
        self.failUnless(hasattr(testresources.TestResource, "_dirty"))
        self.assertEqual(testresources.TestResource.setUpCost, 1)
        self.assertEqual(testresources.TestResource.tearDownCost, 1)
        delattr(testresources.TestResource, "_currentResource")
        delattr(testresources.TestResource, "_uses")
        delattr(testresources.TestResource, "_dirty")

    def testSampleResource(self):
        resource = SampleTestResource.getResource()
        self.assertEqual(resource, "You need to implement your own "
                                   "getResource.")
        self.assertEqual(id(resource),
                         id(SampleTestResource._currentResource))
        self.assertEqual(SampleTestResource.setUpCost, 2)
        self.assertEqual(SampleTestResource.tearDownCost, 2)
        self.failIf(hasattr(testresources.TestResource, "_currentResource"))
        self.failIf(hasattr(testresources.TestResource, "_uses"))
        self.failIf(hasattr(testresources.TestResource, "_dirty"))
        SampleTestResource.finishedWith(resource)
        self.assertEqual(SampleTestResource._currentResource, None)
        self.assertEqual(SampleTestResource._uses, 0)

    def testNestedGetAndFinish(self):
        self.doTestNestedGetAndFinish(
            SampleTestResource, "You need to implement your own getResource.")

    def doTestNestedGetAndFinish(self, cls, resourcevalue, markDirty=False):
        resource = cls.getResource()
        resource2 = cls.getResource()
        self.assertEqual(resource2, resourcevalue)
        self.assertEqual(id(resource), id(resource2))
        self.assertEqual(id(resource2), id(cls._currentResource))
        if markDirty:
            cls.dirtied(resource2)
        cls.finishedWith(resource2)
        self.assertEqual(id(resource), id(cls._currentResource))
        cls.finishedWith(resource)
        self.assertEqual(cls._currentResource, None)
        self.assertEqual(cls._uses, 0)

    def testOverridingMakeResource(self):

        class MockResource(testresources.TestResource):

            @classmethod
            def makeResource(self):
                return "Boo!"

        self.doTestNestedGetAndFinish(MockResource, "Boo!")

    def testOverridingCleanResource(self):

        class MockResource(testresources.TestResource):

            cleans = 0
            @classmethod
            def cleanResource(self, resource):
                self.cleans += 1

            @classmethod
            def makeResource(self):
                return "Boo!"

        self.doTestNestedGetAndFinish(MockResource, "Boo!")
        self.assertEqual(MockResource.cleans, 1)

    def testDirtied(self):
        class MockResource(testresources.TestResource):

            cleans = 0

            @classmethod
            def cleanResource(self, resource):
                self.cleans += 1

            @classmethod
            def makeResource(self):
                return "Boo!"

        self.doTestNestedGetAndFinish(MockResource, "Boo!", True)
        self.assertEqual(MockResource.cleans, 2)

    def testTwoResources(self):

        class MockResource(testresources.TestResource):

            @classmethod
            def makeResource(self):
                return "Boo!"

        resource = SampleTestResource.getResource()
        resource2 = MockResource.getResource()
        self.assertEqual(MockResource._uses, 1)
        self.assertEqual(SampleTestResource._uses, 1)
        self.assertNotEqual(id(resource), id(resource2))
        MockResource.finishedWith(resource2)
        SampleTestResource.finishedWith(resource)
        self.assertEqual(MockResource._uses, 0)
        self.assertEqual(SampleTestResource._uses, 0)


def test_suite():
    loader = testresources.tests.TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result
