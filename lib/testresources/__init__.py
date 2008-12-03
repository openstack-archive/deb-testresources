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


def split_by_resources(tests):
    """Split a list of tests by the resources that the tests use.

    :return: a dictionary mapping sets of resources to lists of tests
    using that combination of resources.  The dictionary always
    contains an entry for "no resources".
    """
    no_resources = frozenset()
    resource_set_tests = {no_resources: []}
    for test in tests:
        resources = getattr(test, "resources", ())
        resource_set = frozenset(resource for name, resource in resources)
        resource_set_tests.setdefault(resource_set, []).append(test)
    return resource_set_tests


class OptimisingTestSuite(unittest.TestSuite):
    """A resource creation optimising TestSuite."""

    def adsorbSuite(self, test_case_or_suite):
        """Add `test_case_or_suite`, unwrapping any suites we find.

        This means that any containing TestSuites will be removed. These
        suites might have their own unittest extensions, so be careful with
        this.
        """
        for test in iterate_tests(test_case_or_suite):
            self.addTest(test)

    def cost_of_switching(self, old_resource_set, new_resource_set):
        """Cost of switching from 'old_resource_set' to 'new_resource_set'.

        This is calculated by adding the cost of tearing down unnecessary
        resources to the cost of setting up the newly-needed resources.

        Note that resources which are always dirtied may skew the predicted
        skew the cost of switching because they are considered common, even
        when reusing them may actually be equivalent to a teardown+setup
        operation.
        """
        new_resources = new_resource_set - old_resource_set
        gone_resources = old_resource_set - new_resource_set
        return (sum(resource.setUpCost for resource in new_resources) +
            sum(resource.tearDownCost for resource in gone_resources))

    def switch(self, old_resource_set, new_resource_set):
        """Switch from 'old_resource_set' to 'new_resource_set'.

        Tear down resources in old_resource_set that aren't in
        new_resource_set and set up resources that are in new_resource_set but
        not in old_resource_set.
        """
        new_resources = new_resource_set - old_resource_set
        old_resources = old_resource_set - new_resource_set
        for resource in old_resources:
            resource.finishedWith(resource._currentResource)
        for resource in new_resources:
            resource.getResource()

    def run(self, result):
        self.sortTests()
        current_resources = set()
        for test in self._tests:
            if result.shouldStop:
                break
            resources = getattr(test, 'resources', None)
            if resources is not None:
                new_resources = set(resource for name, resource in resources)
                self.switch(current_resources, new_resources)
                current_resources = new_resources
            test(result)
        self.switch(current_resources, set())
        return result

    def sortTests(self):
        """Attempt to topographically sort the contained tests.

        Feel free to override to improve the sort behaviour.
        """
        # We group the tests by the resource combinations they use,
        # since there will usually be fewer resource combinations than
        # actual tests and there can never be more.
        resource_set_tests = split_by_resources(self._tests)

        graph = self._getGraph(resource_set_tests.keys())
        no_resources = frozenset()
        # Recursive visit-all-nodes all-permutations.
        def cost(from_set, resource_sets):
            """Get the cost of resource traversal for resource sets.

            :return: cost, order
            """
            if not resource_sets:
                # tear down last resources
                return graph[from_set][no_resources], []
            costs = []
            for to_set in resource_sets:
                child_cost, child_order = cost(
                    to_set, resource_sets - set([to_set]))
                costs.append((graph[from_set][to_set] + child_cost,
                              [to_set] + child_order))
            return min(costs)
        _, order = cost(no_resources,
                        set(resource_set_tests) - set([no_resources]))
        order.append(no_resources)
        self._tests = sum(
            (resource_set_tests[resource_set] for resource_set in order), [])

    def _getGraph(self, resource_sets):
        """Build a graph of the resource-using nodes.

        :return: A complete directed graph of the switching costs
            between each resource combination.
        """
        graph = {}
        for from_set in resource_sets:
            graph[from_set] = {}
            for to_set in resource_sets:
                if from_set is to_set:
                    graph[from_set][to_set] = 0
                else:
                    graph[from_set][to_set] = self.cost_of_switching(
                        from_set, to_set)
        return graph


class TestLoader(unittest.TestLoader):
    """Custom TestLoader to set the right TestSuite class."""
    suiteClass = OptimisingTestSuite


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

    def clean(self, resource):
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
        the `clean` hook, which should do any resource-specific
        cleanup.

        :param resource: A resource returned by `TestResource.getResource`.
        """
        self._uses -= 1
        if self._uses == 0:
            self.clean(resource)
            self._setResource(None)
        elif self._dirty:
            self._resetResource(resource)

    def getResource(self):
        """Get the resource for this class and record that it's being used.

        The resource is constructed using the `make` hook.

        Once done with the resource, pass it to `finishedWith` to indicated
        that it is no longer needed.
        """
        if self._uses == 0:
            self._setResource(self.make())
        elif self._dirty:
            self._resetResource(self._currentResource)
        self._uses += 1
        return self._currentResource

    def make(self):
        """Override this to construct resources."""
        raise NotImplementedError(
            "Override make to construct resources.")

    def _resetResource(self, old_resource):
        self.clean(old_resource)
        self._setResource(self.make())

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
