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

from copy import copy
import unittest


def test_suite():
    import testresources.tests
    return testresources.tests.test_suite()


def iterate_tests(test_suite_or_case):
    """Iterate through all of the test cases in `test_suite_or_case`."""
    try:
        suite = iter(test_suite_or_case)
    except TypeError:
        yield test_suite_or_case
    else:
        for test in suite:
            for subtest in iterate_tests(test):
                yield subtest


class OptimizingTestSuite(unittest.TestSuite):
    """A resource creation optimising TestSuite."""

    def adsorbSuite(self, suite):
        """adsorb all the tests in suite recursively.

        This allows full optimisation of the tests, but will remove any
        containing TestSuites, which might be extending unittest around those
        tests.
        """
        for test in iterate_tests(suite):
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
        graph, legacy = self._getGraph()
        # now we have a graph, we can do lovely things like travelling
        # salesman on it. Blech. So we just take the dijkstra for this. I
        # think this will usually generate reasonable behaviour - its just
        # that the needed starting resources are quite arbitrary and can thus
        # make things less than optimal.
        from testresources.dijkstra import Dijkstra
        if len(graph.keys()) > 0:
            distances, predecessors = Dijkstra(graph, graph.keys()[0])
            # and sort by distance
            nodes = distances.items()
            nodes.sort(key=lambda x:x[1])
            for test, distance in nodes:
                sorted.append(test)
        self._tests = sorted + legacy

    def _getGraph(self):
        """Build a graph of the resource using nodes."""
        # build a mesh graph where a node is a test, and and the number of
        # resources to change to another test is the cost to travel straight
        # to that node.
        legacy = []
        graph = {}
        pending = []
        temp_pending = copy(self._tests)
        if len(temp_pending) == 0:
            return {}, []
        for test in temp_pending:
            if getattr(test, 'resources', None) is None:
                legacy.append(test)
                continue
            pending.append(test)
            graph[test] = {}
        while len(pending):
            test = pending.pop()
            test_resources = set(test.resources)
            for othertest in pending:
                othertest_resources = set(othertest.resources)
                cost = len(test_resources.symmetric_difference(
                                othertest_resources))
                graph[test][othertest] = cost
                graph[othertest][test] = cost
        return graph, legacy


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
            self._currentResource = None
        elif self._dirty:
            self.cleanResource(resource)
            self._setResource()

    def getResource(self):
        """Get the resource for this class and record that it's being used.

        The resource is constructed using the `makeResource` hook.

        Once done with the resource, pass it to `finishedWith` to indicated
        that it is no longer needed.
        """
        uses = getattr(self, '_uses', None)
        if uses is None:
            self._currentResource = None
            self._dirty = False
            self._uses = 0
        if self._uses == 0:
            self._setResource()
        self._uses += 1
        return self._currentResource

    def makeResource(self):
        """Override this to construct resources."""
        raise NotImplementedError(
            "Override makeResource to construct resources.")

    def _setResource(self):
        """Set the current resource to a new value."""
        self._currentResource = self.makeResource()
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
# XXX: Get rid of class-level shenanigans with TestResource.
