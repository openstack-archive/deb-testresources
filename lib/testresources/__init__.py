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

from pyunit3k import iterate_tests
import unittest


def test_suite():
    import testresources.tests
    return testresources.tests.test_suite()


def cost_of_switching(old_resource_set, new_resource_set):
    """The cost of switching from 'old_resource_set' to 'new_resource_set'.

    This is calculated by adding the cost of tearing down unnecessary
    resources to the cost of setting up the newly-needed resources.
    """
    return len(old_resource_set ^ new_resource_set)


def split_by_resources(tests):
    """Split a list of tests by whether or not they use test resources.

    :return: ([tests_that_dont], [tests_that_do])
    """
    # XXX: We could probably use itertools.groupby for this. Or set
    # difference.
    resource_users = []
    legacy = []
    for test in tests:
        resources = getattr(test, 'resources', None)
        if resources:
            resource_users.append(test)
        else:
            legacy.append(test)
    return legacy, resource_users


class OptimizingTestSuite(unittest.TestSuite):
    """A resource creation optimising TestSuite."""

    def flatAddTest(self, test_case_or_suite):
        """Add `test_case_or_suite`, unwrapping any suites we find.

        This means that any containing TestSuites will be removed. These
        suites might have their own unittest extensions, so be careful with
        this.
        """
        for test in iterate_tests(test_case_or_suite):
            self.addTest(test)

    def run(self, result):
        self.sortTests()
        current_resources = {}
        for test in self._tests:
            if result.shouldStop:
                break
            resources = getattr(test, 'resources', None)
            if resources is not None:
                new_resources = {}
                for attribute, resource in resources:
                    if not resource in current_resources.keys():
                        current_resources[resource] = resource.getResource()
                    new_resources[resource] = current_resources[resource]
                for resource in current_resources.keys():
                    if not resource in new_resources:
                        resource.finishedWith(current_resources[resource])
                current_resources = new_resources
            test(result)
        for resource, value in current_resources.items():
            resource.finishedWith(value)
        return result

    def sortTests(self):
        """Attempt to topographically sort the contained tests.

        Feel free to override to improve the sort behaviour.
        """
        # quick hack on the plane. Need to lookup graph textbook.
        sorted = []
        legacy, tests_with_resources = split_by_resources(self._tests)
        graph = self._getGraph(tests_with_resources)
        # now we have a graph, we can do lovely things like travelling
        # salesman on it. Blech. So we just take the dijkstra for this. I
        # think this will usually generate reasonable behaviour - its just
        # that the needed starting resources are quite arbitrary and can thus
        # make things less than optimal.
        from testresources.dijkstra import Dijkstra
        if len(graph.keys()) > 0:
            # XXX: Arbitrarily select the start node. This can result in
            # sub-optimal sortings. We actually want to include the cost of
            # establishing the start node in the calculation of the distance.
            start_node = graph.keys()[0]
            distances, predecessors = Dijkstra(graph, start_node)
            # and sort by distance
            nodes = distances.items()
            nodes.sort(key=lambda x:x[1])
            for test, distance in nodes:
                sorted.append(test)
        self._tests = sorted + legacy

    def _getGraph(self, tests_with_resources):
        """Build a graph of the resource-using nodes."""
        # build a mesh graph where a node is a test, and and the number of
        # resources to change to another test is the cost to travel straight
        # to that node.
        graph = dict((test, dict()) for test in tests_with_resources)
        while tests_with_resources:
            test = tests_with_resources.pop()
            test_resources = set(test.resources)
            for othertest in tests_with_resources:
                othertest_resources = set(othertest.resources)
                cost = cost_of_switching(test_resources, othertest_resources)
                graph[test][othertest] = cost
                graph[othertest][test] = cost
        return graph


class TestLoader(unittest.TestLoader):
    """Custom TestLoader to set the right TestSuite class."""
    suiteClass = OptimizingTestSuite


class TestResource(object):
    """A resource that can be shared across tests.

    :ivar setUpCost: The relative cost to construct a resource of this type.
         One good approach is to set this to the number of seconds it normally
         takes to set up the resource.
    :ivar tearDownCost: The relative cost to tear down a resource of this
         type. One good approach is to set this to the number of seconds it
         normally takes to tear down the resource.
    """

    setUpCost = 1
    tearDownCost = 1

    def __init__(self):
        self._dirty = False
        self._uses = 0
        self._currentResource = None

    def cleanResource(self, resource):
        """Override this to class method to hook into resource removal."""

    def dirtied(self, resource):
        """Mark the resource as having been 'dirtied'.

        A resource is dirty when it is no longer suitable for use by other
        tests.

        e.g. a shared database that has had rows changed.
        """
        self._dirty = True

    def finishedWith(self, resource):
        """Indicate that 'resource' has one less user.

        If there are no more registered users of 'resource' then we trigger
        the `cleanResource` hook, which should do any resource-specific
        cleanup.

        :param resource: A resource returned by `TestResource.getResource`.
        """
        self._uses -= 1
        if self._uses == 0:
            self.cleanResource(resource)
            self._setResource(None)
        elif self._dirty:
            self._resetResource(resource)

    def getResource(self):
        """Get the resource for this class and record that it's being used.

        The resource is constructed using the `makeResource` hook.

        Once done with the resource, pass it to `finishedWith` to indicated
        that it is no longer needed.
        """
        if self._uses == 0:
            self._setResource(self.makeResource())
        elif self._dirty:
            self._resetResource(self._currentResource)
        self._uses += 1
        return self._currentResource

    def makeResource(self):
        """Override this to construct resources."""
        raise NotImplementedError(
            "Override makeResource to construct resources.")

    def _resetResource(self, old_resource):
        self.cleanResource(old_resource)
        self._setResource(self.makeResource())

    def _setResource(self, new_resource):
        """Set the current resource to a new value."""
        self._currentResource = new_resource
        self._dirty = False


class ResourcedTestCase(unittest.TestCase):
    """A TestCase parent or utility that enables cross-test resource usage.

    :ivar resources: A list of (name, resource) pairs, where 'resource' is a
        subclass of `TestResource` and 'name' is the name of the attribute
        that the resource should be stored on.
    """

    resources = []

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.setUpResources()

    def setUpResources(self):
        """Set up any resources that this test needs."""
        for resource in self.resources:
            setattr(self, resource[0], resource[1].getResource())

    def tearDown(self):
        self.tearDownResources()
        unittest.TestCase.tearDown(self)

    def tearDownResources(self):
        """Tear down any resources that this test declares."""
        for resource in self.resources:
            resource[1].finishedWith(getattr(self, resource[0]))
            delattr(self, resource[0])

# XXX: Needs to be fun to use even if you don't care about optimization.
# XXX:
# - To replace layers, need a resource that runs test in subprocess.
# - alternatively, resource that is never torn down.
# XXX: How to combine resources?
# XXX: Introduce timing hooks for setUpCost and tearDownCost.
# XXX: setUpCost and tearDownCost are not used.
# XXX: Why does finishedWith take a parameter?
