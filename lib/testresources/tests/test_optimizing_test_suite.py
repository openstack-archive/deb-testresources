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

import random
import pyunit3k
import testresources
from testresources import cost_of_switching, split_by_resources
import unittest


class MakeCounter(testresources.TestResource):
    """Test resource that counts makes and cleans."""

    def __init__(self):
        testresources.TestResource.__init__(self)
        self.cleans = 0
        self.makes = 0

    def cleanResource(self, resource):
        self.cleans += 1

    def makeResource(self):
        self.makes += 1
        return "boo"


class TestOptimizingTestSuite(pyunit3k.TestCase):

    def makeTestCase(self):
        """Make a normal TestCase."""
        return unittest.TestCase('run')

    def makeResourcedTestCase(self, resource_manager, test_running_hook):
        """Make a ResourcedTestCase."""
        class ResourcedTestCaseForTesting(testresources.ResourcedTestCase):
            def runTest(self):
                test_running_hook()
        test_case = ResourcedTestCaseForTesting('runTest')
        test_case.resources = [('_default', resource_manager)]
        return test_case

    def setUp(self):
        pyunit3k.TestCase.setUp(self)
        self.optimizing_suite = testresources.OptimizingTestSuite()

    def testFlatAddTest(self):
        # Flat-adding a single test case is the same as adding one using
        # addTest.
        case = self.makeTestCase()
        self.optimizing_suite.flatAddTest(case)
        self.assertEqual([case], self.optimizing_suite._tests)

    def testFlatAddTestSuite(self):
        # Flat-adding a test suite will is the same as adding all the tests in
        # that suite.
        case = self.makeTestCase()
        suite = unittest.TestSuite([case])
        self.optimizing_suite.flatAddTest(suite)
        self.assertEqual([case], self.optimizing_suite._tests)

    def testFlatAddFlattensAllSuiteStructure(self):
        # flatAddTest will get rid of all suite structure when adding a test,
        # no matter how much nesting is going on.
        case1 = self.makeTestCase()
        case2 = self.makeTestCase()
        case3 = self.makeTestCase()
        suite = unittest.TestSuite(
            [unittest.TestSuite([case1, unittest.TestSuite([case2])]),
             case3])
        self.optimizing_suite.flatAddTest(suite)
        self.assertEqual([case1, case2, case3], self.optimizing_suite._tests)

    def testSingleCaseResourceAcquisition(self):
        sample_resource = MakeCounter()
        def getResourceCount():
            self.assertEqual(sample_resource._uses, 2)
        case = self.makeResourcedTestCase(sample_resource, getResourceCount)
        self.optimizing_suite.addTest(case)
        result = unittest.TestResult()
        self.optimizing_suite.run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.wasSuccessful(), True)
        self.assertEqual(sample_resource._uses, 0)

    def testResourceReuse(self):
        make_counter = MakeCounter()
        def getResourceCount():
            self.assertEqual(make_counter._uses, 2)
        case = self.makeResourcedTestCase(make_counter, getResourceCount)
        case2 = self.makeResourcedTestCase(make_counter, getResourceCount)
        self.optimizing_suite.addTest(case)
        self.optimizing_suite.addTest(case2)
        result = unittest.TestResult()
        self.optimizing_suite.run(result)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(result.wasSuccessful(), True)
        self.assertEqual(make_counter._uses, 0)
        self.assertEqual(make_counter.makes, 1)
        self.assertEqual(make_counter.cleans, 1)

    def testOptimisedRunNonResourcedTestCase(self):
        case = self.makeTestCase()
        self.optimizing_suite.addTest(case)
        result = unittest.TestResult()
        self.optimizing_suite.run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.wasSuccessful(), True)

    def testSortTestsCalled(self):
        class MockOptimizingTestSuite(testresources.OptimizingTestSuite):
            def sortTests(self):
                self.sorted = True

        suite = MockOptimizingTestSuite()
        suite.sorted = False
        suite.run(None)
        self.assertEqual(suite.sorted, True)


class TestSplitByResources(pyunit3k.TestCase):
    """Tests for split_by_resources."""

    def makeTestCase(self):
        return unittest.TestCase('run')

    def makeResourcedTestCase(self, has_resource=True):
        case = testresources.ResourcedTestCase('run')
        if has_resource:
            case.resources = ['resource', testresources.TestResource()]
        return case

    def testNoTests(self):
        self.assertEqual(([], []), split_by_resources([]))

    def testJustNormalCases(self):
        normal_case = self.makeTestCase()
        have_nots, haves = split_by_resources([normal_case])
        self.assertEqual([normal_case], have_nots)
        self.assertEqual([], haves)

    def testJustResourcedCases(self):
        resourced_case = self.makeResourcedTestCase()
        have_nots, haves = split_by_resources([resourced_case])
        self.assertEqual([], have_nots)
        self.assertEqual([resourced_case], haves)

    def testResourcedCaseWithNoResources(self):
        resourced_case = self.makeResourcedTestCase(has_resource=False)
        have_nots, haves = split_by_resources([resourced_case])
        self.assertEqual([resourced_case], have_nots)
        self.assertEqual([], haves)

    def testMixThemUp(self):
        normal_cases = [self.makeTestCase() for i in range(3)]
        normal_cases.extend([
            self.makeResourcedTestCase(has_resource=False) for i in range(3)])
        resourced_cases = [self.makeResourcedTestCase() for i in range(3)]
        all_cases = normal_cases + resourced_cases
        # XXX: Maybe I shouldn't be using random here.
        random.shuffle(all_cases)
        have_nots, haves = split_by_resources(all_cases)
        self.assertEqual(set(normal_cases), set(have_nots))
        self.assertEqual(set(resourced_cases), set(haves))


class TestCostOfSwitching(pyunit3k.TestCase):
    """Tests for cost_of_switching."""

    def makeResource(self, setUpCost=1, tearDownCost=1):
        resource = testresources.TestResource()
        resource.setUpCost = setUpCost
        resource.tearDownCost = tearDownCost
        return resource

    def testNoResources(self):
        # The cost of switching from no resources to no resources is 0.
        self.assertEqual(0, cost_of_switching(set(), set()))

    def testSameResources(self):
        # The cost of switching to the same set of resources is also 0.
        a = self.makeResource()
        b = self.makeResource()
        self.assertEqual(0, cost_of_switching(set([a]), set([a])))
        self.assertEqual(0, cost_of_switching(set([a, b]), set([a, b])))

    # XXX: The next few tests demonstrate the current behaviour of the system.
    # We'll change them later.

    def testNewResources(self):
        a = self.makeResource()
        b = self.makeResource()
        self.assertEqual(1, cost_of_switching(set(), set([a])))
        self.assertEqual(1, cost_of_switching(set([a]), set([a, b])))
        self.assertEqual(2, cost_of_switching(set(), set([a, b])))

    def testOldResources(self):
        a = self.makeResource()
        b = self.makeResource()
        self.assertEqual(1, cost_of_switching(set([a]), set()))
        self.assertEqual(1, cost_of_switching(set([a, b]), set([a])))
        self.assertEqual(2, cost_of_switching(set([a, b]), set()))

    def testCombo(self):
        a = self.makeResource()
        b = self.makeResource()
        c = self.makeResource()
        self.assertEqual(2, cost_of_switching(set([a]), set([b])))
        self.assertEqual(2, cost_of_switching(set([a, c]), set([b, c])))


class TestCostGraph(pyunit3k.TestCase):
    """Tests for calculating the cost graph of resourced test cases."""

    def getGraph(self, tests_with_resources):
        suite = testresources.OptimizingTestSuite()
        return suite._getGraph(tests_with_resources)

    def makeResource(self, setUpCost=1, tearDownCost=1):
        resource = testresources.TestResource()
        resource.setUpCost = setUpCost
        resource.tearDownCost = tearDownCost
        return resource

    def makeTestWithResources(self, resources):
        case = testresources.ResourcedTestCase('run')
        case.resources = [
            (self.getUniqueString(), resource) for resource in resources]
        return case

    def testEmptyGraph(self):
        self.assertEqual({}, self.getGraph([]))

    def testSingletonGraph(self):
        case = self.makeTestWithResources([self.makeResource()])
        self.assertEqual({case: {}}, self.getGraph([case]))

    def testTwoCasesInGraph(self):
        a = self.makeTestWithResources(
            [self.makeResource(), self.makeResource()])
        b = self.makeTestWithResources([self.makeResource()])
        self.assertEqual(
            {a: {b: cost_of_switching(set(a.resources), set(b.resources))},
             b: {a: cost_of_switching(set(a.resources), set(b.resources))}},
            self.getGraph([a, b]))


class TestGraphStuff(pyunit3k.TestCase):

    def setUp(self):

        class MockTest(unittest.TestCase):
            def __repr__(self):
                """The representation is the tests name.

                This makes it easier to debug sorting failures.
                """
                return self.id().split('.')[-1]
            def test_one(self):
                pass
            def test_two(self):
                pass
            def test_three(self):
                pass
            def test_four(self):
                pass

        resource_one = testresources.TestResource()
        resource_two = testresources.TestResource()
        resource_three = testresources.TestResource()

        self.suite = testresources.OptimizingTestSuite()
        self.case1 = MockTest("test_one")
        self.case1.resources = [
            ("_one", resource_one), ("_two", resource_two)]
        self.case2 = MockTest("test_two")
        self.case2.resources = [
            ("_two", resource_two), ("_three", resource_three)]
        self.case3 = MockTest("test_three")
        self.case3.resources = [("_three", resource_three)]
        self.case4 = MockTest("test_four")
        self.suite.addTests([self.case3, self.case1, self.case4, self.case2])
        # acceptable sorted orders are:
        # 1, 2, 3, 4
        # 3, 2, 1, 4

    def testBasicSortTests(self):
        # XXX: The outcome of this test depends on exactly how Python orders a
        # dictionary. This makes it unreliable.
        return
        self.suite.sortTests()
        self.assertIn(
            self.suite._tests, [
                [self.case1, self.case2, self.case3, self.case4],
                [self.case3, self.case2, self.case1, self.case4]])


def test_suite():
    from testresources.tests import TestUtil
    loader = TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result
