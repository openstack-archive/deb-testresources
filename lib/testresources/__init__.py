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

from copy import copy
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


class OptimizingTestSuite(unittest.TestSuite):
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
        self.sortTests()
        current_resources = {}
        for test in self._tests:
            if result.shouldStop:
                break
            resources = getattr(test, '_resources', None)
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
        # build a mesh graph where a node is a test, and
        # and the number of resources to change to another test
        # is the cost to travel straight to that node.
        legacy = []
        graph = {}
        pending = []
        temp_pending = copy(self._tests)
        if len(temp_pending) == 0:
            return {}, []
        for test in temp_pending:
            if getattr(test, '_resources', None) is None:
                legacy.append(test)
                continue
            pending.append(test)
            graph[test] = {}
        while len(pending):
            test = pending.pop()
            test_resources = set(test._resources)
            for othertest in pending:
                othertest_resources = set(othertest._resources)
                cost = len(test_resources.symmetric_difference(
                                othertest_resources))
                graph[test][othertest] = cost
                graph[othertest][test] = cost
        return graph, legacy


class TestLoader(unittest.TestLoader):
    """Custom TestLoader to set the right TestSuite class."""
    suiteClass = OptimizingTestSuite


class TestResource(object):
    """A TestResource for persistent resources needed across tests."""
    # XXX: Everything here is class-level. Why?
    # XXX: Fuller docstring.

    # XXX: Document ways to estimate cost.
    # XXX: Introduce timing hooks.
    setUpCost = 1
    """The relative cost to construct a resource of this type."""
    tearDownCost = 1
    """The relative cost to tear down a resource of this type."""

    # XXX: This shouldn't have an underscore prefix.
    @classmethod
    def _cleanResource(cls, resource):
        """Override this to class method to hook into resource removal."""

    # XXX: Docstring.
    @classmethod
    def dirtied(cls, resource):
        cls._dirty = True

    # XXX: Docstring.
    @classmethod
    def finishedWith(cls, resource):
        cls._uses -= 1
        if cls._uses == 0:
            cls._cleanResource(resource)
            cls._currentResource = None
        elif cls._dirty:
            cls._cleanResource(resource)
            cls.setResource()

    # XXX: Docstring.
    @classmethod
    def getResource(cls):
        uses = getattr(cls, '_uses', None)
        if uses is None:
            cls._currentResource = None
            cls._dirty = False
            cls._uses = 0
        if cls._uses == 0:
            cls.setResource()
        cls._uses += 1
        return cls._currentResource

    @classmethod
    # XXX: This shouldn't have an underscore prefix.
    def _makeResource(cls):
        """Override this to construct resources."""
        raise NotImplementedError("Override _makeResource to construct "
                                  "resources.")

    # XXX: No way should this be public.
    @classmethod
    def setResource(cls):
        """Set the current resource to a new value."""
        cls._currentResource = cls._makeResource()
        cls._dirty = False


# XXX: This shouldn't be in the file.
class SampleTestResource(TestResource):

    setUpCost = 2
    tearDownCost = 2

    @classmethod
    def _makeResource(cls):
        return "You need to implement your own getResource."


class ResourcedTestCase(unittest.TestCase):
    """A TestCase parent or utility that enables cross-test resource usage."""

    # XXX: No underscore prefix.
    # XXX: Document contents.
    _resources = []

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.setUpResources(self)

    # XXX: Why is this a staticmethod not a classmethod?
    # XXX: Docstring.
    @staticmethod
    def setUpResources(case):
        for resource in case._resources:
            setattr(case, resource[0], resource[1].getResource())

    def tearDown(self):
        self.tearDownResources(self)
        unittest.TestCase.tearDown(self)

    # XXX: Why is this a staticmethod not a classmethod?
    # XXX: Docstring.
    @staticmethod
    def tearDownResources(case):
        for resource in case._resources:
            resource[1].finishedWith(getattr(case, resource[0]))
            delattr(case, resource[0])

# XXX: Needs to be fun to use even if you don't care about optimization.
# XXX:
# - To replace layers, need a resource that runs test in subprocess.
# - alternatively, resource that is never torn down.
# XXX: How to combine resources?
