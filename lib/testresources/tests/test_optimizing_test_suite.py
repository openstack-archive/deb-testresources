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

import pyunit3k
import testresources
from testresources.tests import SampleTestResource
import unittest


class TestOptimizingTestSuite(pyunit3k.TestCase):

    def testAdsorbSuiteWithCase(self):
        suite = testresources.OptimizingTestSuite()
        case = unittest.TestCase("run")
        suite.adsorbSuite(case)
        self.assertEqual(suite._tests, [case])

    def testSingleCaseResourceAcquisition(self):
        class ResourceChecker(testresources.ResourcedTestCase):
            resources = [("_default", SampleTestResource)]
            def getResourceCount(self):
                self.assertEqual(SampleTestResource._uses, 2)

        suite = testresources.OptimizingTestSuite()
        case = ResourceChecker("getResourceCount")
        suite.addTest(case)
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        self.assertEqual(SampleTestResource._uses, 0)

    def testResourceReuse(self):

        class MakeCounter(testresources.TestResource):

            cleans = 0
            makes = 0
            @classmethod
            def cleanResource(cls, resource):
                cls.cleans += 1
            @classmethod
            def makeResource(cls):
                cls.makes += 1
                return "boo"

        class ResourceChecker(testresources.ResourcedTestCase):
            resources = [("_default", MakeCounter)]
            def getResourceCount(self):
                self.assertEqual(MakeCounter._uses, 2)

        suite = testresources.OptimizingTestSuite()
        case = ResourceChecker("getResourceCount")
        case2 = ResourceChecker("getResourceCount")
        suite.addTest(case)
        suite.addTest(case2)
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        self.assertEqual(MakeCounter._uses, 0)
        self.assertEqual(MakeCounter.makes, 1)
        self.assertEqual(MakeCounter.cleans, 1)

    def testOptimisedRunNonResourcedTestCase(self):
        class MockTest(unittest.TestCase):
            def test_nothing(self):
                pass
        suite = testresources.OptimizingTestSuite()
        case = MockTest("test_nothing")
        suite.addTest(case)
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])

    def testSortTestsCalled(self):
        class MockOptimizingTestSuite(testresources.OptimizingTestSuite):
            def sortTests(self):
                self.sorted = True

        suite = MockOptimizingTestSuite()
        suite.sorted = False
        suite.run(None)
        self.assertEqual(suite.sorted, True)


class TestGraphStuff(pyunit3k.TestCase):

    def setUp(self):

        class MockTest(unittest.TestCase):
            def test_one(self):
                pass
            def test_two(self):
                pass
            def test_three(self):
                pass
            def test_four(self):
                pass

        class ResourceOne(testresources.TestResource):
            pass

        class ResourceTwo(testresources.TestResource):
            pass

        class ResourceThree(testresources.TestResource):
            pass

        self.suite = testresources.OptimizingTestSuite()
        self.case1 = MockTest("test_one")
        self.case1.resources = [("_one", ResourceOne), ("_two", ResourceTwo)]
        self.case2 = MockTest("test_two")
        self.case2.resources = [
            ("_two", ResourceTwo), ("_three", ResourceThree)]
        self.case3 = MockTest("test_three")
        self.case3.resources = [("_three", ResourceThree)]
        self.case4 = MockTest("test_four")
        self.suite.addTests([self.case3, self.case1, self.case4, self.case2])
        # acceptable sorted orders are:
        # 1, 2, 3, 4
        # 3, 2, 1, 4

    def testBasicSortTests(self):
        self.suite.sortTests()
        self.failUnless(self.suite._tests == [self.case1, self.case2,
                                              self.case3, self.case4] or
                        self.suite._tests == [self.case3, self.case2,
                                              self.case1, self.case4])

    def testGetGraph(self):
        graph, legacy = self.suite._getGraph()
        case1vertex = {self.case2: 2, self.case3: 3}
        case2vertex = {self.case1: 2, self.case3: 1}
        case3vertex = {self.case1: 3, self.case2: 1}
        self.assertEqual(legacy, [self.case4])
        self.assertEqual(graph[self.case1], case1vertex)
        self.assertEqual(graph[self.case2], case2vertex)
        self.assertEqual(graph[self.case3], case3vertex)
        self.assertEqual(
            graph, {self.case1: case1vertex,
                    self.case2: case2vertex,
                    self.case3: case3vertex})


def test_suite():
    from testresources.tests import TestUtil
    loader = TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result
