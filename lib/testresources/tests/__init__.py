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

from unittest import TestResult

import testresources
from testresources.tests import TestUtil

def test_suite():
    import testresources.tests.test_optimising_test_suite
    import testresources.tests.test_resourced_test_case
    import testresources.tests.test_test_loader
    import testresources.tests.test_test_resource
    import testresources.tests.test_resource_graph
    result = TestUtil.TestSuite()
    result.addTest(testresources.tests.test_test_loader.test_suite())
    result.addTest(testresources.tests.test_test_resource.test_suite())
    result.addTest(testresources.tests.test_resourced_test_case.test_suite())
    result.addTest(testresources.tests.test_resource_graph.test_suite())
    result.addTest(
        testresources.tests.test_optimising_test_suite.test_suite())
    return result


class ResultWithoutResourceExtensions(object):
    """A test fake which does not have resource extensions."""


class ResultWithResourceExtensions(TestResult):
    """A test fake which has resource extensions."""

    def __init__(self):
        TestResult.__init__(self)
        self._calls = []

    def startCleanResource(self, resource):
        self._calls.append(("clean", "start", resource))

    def stopCleanResource(self, resource):
        self._calls.append(("clean", "stop", resource))

    def startMakeResource(self, resource):
        self._calls.append(("make", "start", resource))

    def stopMakeResource(self, resource):
        self._calls.append(("make", "stop", resource))
