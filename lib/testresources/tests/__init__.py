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

import testresources
from testresources.tests import TestUtil

def test_suite():
    import testresources.tests.test_optimizing_test_suite
    import testresources.tests.test_resourced_test_case
    import testresources.tests.test_test_loader
    import testresources.tests.test_test_resource
    result = TestUtil.TestSuite()
    result.addTest(testresources.tests.test_test_loader.test_suite())
    result.addTest(testresources.tests.test_test_resource.test_suite())
    result.addTest(testresources.tests.test_resourced_test_case.test_suite())
    result.addTest(testresources.tests.test_optimizing_test_suite.test_suite())
    return result


class SampleTestResource(testresources.TestResource):

    setUpCost = 2
    tearDownCost = 2

    @classmethod
    def makeResource(cls):
        return "You need to implement your own getResource."
