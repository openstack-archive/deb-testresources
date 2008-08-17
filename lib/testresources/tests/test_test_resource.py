
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

import pyunit3k

import testresources
from testresources.tests import SampleTestResource


class MockResource(testresources.TestResource):
    """Mock resource that logs the number of cleanResource calls."""

    def __init__(self):
        testresources.TestResource.__init__(self)
        self.cleans = 0

    def cleanResource(self, resource):
        self.cleans += 1

    def makeResource(self):
        return "Boo!"


class TestTestResource(pyunit3k.TestCase):

    def testDefaultResource(self):
        resource_manager = testresources.TestResource()
        self.assertRaises(NotImplementedError, resource_manager.getResource)
        self.failUnless(hasattr(resource_manager, "_currentResource"))
        self.failUnless(hasattr(resource_manager, "_uses"))
        self.failUnless(hasattr(resource_manager, "_dirty"))
        self.assertEqual(resource_manager.setUpCost, 1)
        self.assertEqual(resource_manager.tearDownCost, 1)
        delattr(resource_manager, "_currentResource")
        delattr(resource_manager, "_uses")
        delattr(resource_manager, "_dirty")

    def testNestedGetAndFinish(self):
        self.doTestNestedGetAndFinish(
            SampleTestResource(),
            "You need to implement your own getResource.")

    def doTestNestedGetAndFinish(self, resource_manager, resourcevalue,
                                 markDirty=False):
        resource = resource_manager.getResource()
        resource2 = resource_manager.getResource()
        self.assertEqual(resource2, resourcevalue)
        self.assertIs(resource, resource2)
        self.assertIs(resource2, resource_manager._currentResource)
        if markDirty:
            resource_manager.dirtied(resource2)
        resource_manager.finishedWith(resource2)
        self.assertIs(resource, resource_manager._currentResource)
        resource_manager.finishedWith(resource)
        self.assertEqual(resource_manager._currentResource, None)
        self.assertEqual(resource_manager._uses, 0)

    def testOverridingMakeResource(self):
        self.doTestNestedGetAndFinish(MockResource(), "Boo!")

    def testOverridingCleanResource(self):
        mock_resource = MockResource()
        self.doTestNestedGetAndFinish(mock_resource, "Boo!")
        self.assertEqual(mock_resource.cleans, 1)

    def testDirtied(self):
        mock_resource = MockResource()
        self.doTestNestedGetAndFinish(mock_resource, "Boo!", True)
        self.assertEqual(mock_resource.cleans, 2)

    def testTwoResources(self):
        sample_resource_manager = SampleTestResource()
        mock_resource_manager = MockResource()
        resource = sample_resource_manager.getResource()
        resource2 = mock_resource_manager.getResource()
        self.assertEqual(mock_resource_manager._uses, 1)
        self.assertEqual(sample_resource_manager._uses, 1)
        self.assertIsNot(resource, resource2)
        mock_resource_manager.finishedWith(resource2)
        sample_resource_manager.finishedWith(resource)
        self.assertEqual(mock_resource_manager._uses, 0)
        self.assertEqual(sample_resource_manager._uses, 0)


class TestSampleResource(pyunit3k.TestCase):

    def testSampleResource(self):
        resource_manager = SampleTestResource()
        resource = resource_manager.getResource()
        self.assertEqual(
            resource, "You need to implement your own getResource.")
        self.assertIs(resource, resource_manager._currentResource)
        self.assertEqual(resource_manager.setUpCost, 2)
        self.assertEqual(resource_manager.tearDownCost, 2)
        self.failIf(hasattr(testresources.TestResource, "_currentResource"))
        self.failIf(hasattr(testresources.TestResource, "_uses"))
        self.failIf(hasattr(testresources.TestResource, "_dirty"))
        resource_manager.finishedWith(resource)
        self.assertEqual(resource_manager._currentResource, None)
        self.assertEqual(resource_manager._uses, 0)


def test_suite():
    loader = testresources.tests.TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result
