
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

import testtools

import testresources


def test_suite():
    loader = testresources.tests.TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result


class MockResource(testresources.TestResource):
    """Mock resource that logs the number of make and clean calls."""

    def __init__(self):
        testresources.TestResource.__init__(self)
        self.makes = 0
        self.cleans = 0

    def clean(self, resource):
        self.cleans += 1

    def make(self, dependency_resources):
        self.makes += 1
        return "Boo!"


class TestTestResource(testtools.TestCase):

    def testUnimplementedGetResource(self):
        # By default, TestResource raises NotImplementedError on getResource
        # because make is not defined initially.
        resource_manager = testresources.TestResource()
        self.assertRaises(NotImplementedError, resource_manager.getResource)

    def testInitiallyNotDirty(self):
        resource_manager = testresources.TestResource()
        self.assertEqual(False, resource_manager._dirty)

    def testInitiallyUnused(self):
        resource_manager = testresources.TestResource()
        self.assertEqual(0, resource_manager._uses)

    def testInitiallyNoCurrentResource(self):
        resource_manager = testresources.TestResource()
        self.assertEqual(None, resource_manager._currentResource)

    def testneededResourcesDefault(self):
        # Calling neededResources on a default TestResource returns the
        # resource.
        resource = testresources.TestResource()
        self.assertEqual([resource], resource.neededResources())

    def testneededResourcesDependenciesFirst(self):
        # Calling neededResources on a TestResource with dependencies puts the
        # dependencies first.
        resource = testresources.TestResource()
        dep1 = testresources.TestResource()
        dep2 = testresources.TestResource()
        resource.resources.append(("dep1", dep1))
        resource.resources.append(("dep2", dep2))
        self.assertEqual([dep1, dep2, resource], resource.neededResources())

    def testneededResourcesClosure(self):
        # Calling neededResources on a TestResource with dependencies includes
        # the needed resources of the needed resources.
        resource = testresources.TestResource()
        dep1 = testresources.TestResource()
        dep2 = testresources.TestResource()
        resource.resources.append(("dep1", dep1))
        dep1.resources.append(("dep2", dep2))
        self.assertEqual([dep2, dep1, resource], resource.neededResources())

    def testDefaultCosts(self):
        # The base TestResource costs 1 to set up and to tear down.
        resource_manager = testresources.TestResource()
        self.assertEqual(resource_manager.setUpCost, 1)
        self.assertEqual(resource_manager.tearDownCost, 1)

    def testGetResourceReturnsMakeResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(resource_manager.make({}), resource)

    def testGetResourceIncrementsUses(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        self.assertEqual(1, resource_manager._uses)
        resource_manager.getResource()
        self.assertEqual(2, resource_manager._uses)

    def testGetResourceDoesntDirty(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        self.assertEqual(resource_manager._dirty, False)

    def testGetResourceSetsCurrentResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertIs(resource_manager._currentResource, resource)

    def testGetResourceTwiceReturnsIdenticalResource(self):
        resource_manager = MockResource()
        resource1 = resource_manager.getResource()
        resource2 = resource_manager.getResource()
        self.assertIs(resource1, resource2)

    def testGetResourceCallsMakeResource(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)

    def testRepeatedGetResourceCallsMakeResourceOnceOnly(self):
        resource_manager = MockResource()
        resource_manager.getResource()
        resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)

    def testFinishedWithDecrementsUses(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource = resource_manager.getResource()
        self.assertEqual(2, resource_manager._uses)
        resource_manager.finishedWith(resource)
        self.assertEqual(1, resource_manager._uses)
        resource_manager.finishedWith(resource)
        self.assertEqual(0, resource_manager._uses)

    def testFinishedWithResetsCurrentResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertIs(None, resource_manager._currentResource)

    def testFinishedWithCallsCleanResource(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertEqual(1, resource_manager.cleans)

    def testUsingTwiceMakesAndCleansTwice(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertEqual(2, resource_manager.makes)
        self.assertEqual(2, resource_manager.cleans)

    def testFinishedWithCallsCleanResourceOnceOnly(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertEqual(0, resource_manager.cleans)
        resource_manager.finishedWith(resource)
        self.assertEqual(1, resource_manager.cleans)

    def testFinishedWithMarksNonDirty(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.dirtied(resource)
        resource_manager.finishedWith(resource)
        self.assertEqual(False, resource_manager._dirty)

    def testResourceAvailableBetweenFinishedWithCalls(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        self.assertIs(resource, resource_manager._currentResource)

    def testDirtiedSetsDirty(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(False, resource_manager._dirty)
        resource_manager.dirtied(resource)
        self.assertEqual(True, resource_manager._dirty)

    def testDirtyingResourceTriggersClean(self):
        resource_manager = MockResource()
        resource1 = resource_manager.getResource()
        resource2 = resource_manager.getResource()
        resource_manager.dirtied(resource2)
        resource_manager.finishedWith(resource2)
        self.assertEqual(1, resource_manager.cleans)
        resource_manager.finishedWith(resource1)
        self.assertEqual(2, resource_manager.cleans)

    def testDirtyingResourceTriggersRemake(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        self.assertEqual(1, resource_manager.makes)
        resource_manager.dirtied(resource)
        resource_manager.getResource()
        self.assertEqual(1, resource_manager.cleans)
        self.assertEqual(2, resource_manager.makes)
        self.assertEqual(False, resource_manager._dirty)

    def testDirtyingWhenUnused(self):
        resource_manager = MockResource()
        resource = resource_manager.getResource()
        resource_manager.finishedWith(resource)
        resource_manager.dirtied(resource)
        self.assertEqual(1, resource_manager.makes)
        resource = resource_manager.getResource()
        self.assertEqual(2, resource_manager.makes)
