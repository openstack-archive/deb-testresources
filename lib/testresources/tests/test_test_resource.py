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
import testresources.tests
import unittest

def test_suite():
    loader = testresources.tests.TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result
    

class TestTestResource(unittest.TestCase):

    def testImports(self):
        from testresources import TestResource

    def testDefaultResource(self):
        testresources.TestResource._currentResource = None
        testresources.TestResource._uses = 0
        resource = testresources.TestResource.getResource()
        self.assertEqual(resource, "You need to implement your own "
                                   "getResource.")
        self.assertEqual(id(resource), 
                         id(testresources.TestResource._currentResource))
        testresources.TestResource._currentResource = None
        testresources.TestResource._uses = 0

    def testDefaultFinish(self):
        testresources.TestResource._currentResource = None
        testresources.TestResource._uses = 0
        resource = testresources.TestResource.getResource()
        testresources.TestResource.finishedWith(resource)
        self.assertEqual(testresources.TestResource._currentResource, None)
        self.assertEqual(testresources.TestResource._uses, 0)
        testresources.TestResource._currentResource = None
        testresources.TestResource._uses = 0

    def testNestedGetAndFinish(self):
        self.doTestNestedGetAndFinish(testresources.TestResource,
                                      "You need to implement your own "
                                      "getResource.")                              
    def doTestNestedGetAndFinish(self, cls, resourcevalue):
        cls._currentResource = None
        cls._uses = 0
        resource = cls.getResource()
        resource2 = cls.getResource()
        self.assertEqual(resource2, resourcevalue)
        self.assertEqual(id(resource), id(resource2))
        self.assertEqual(id(resource2), id(cls._currentResource))
        cls.finishedWith(resource2)
        self.assertEqual(id(resource), id(cls._currentResource))
        cls.finishedWith(resource)
        self.assertEqual(cls._currentResource, None)
        self.assertEqual(cls._uses, 0)
        cls._currentResource = None
        cls._uses = 0

    def testOverriding_makeResource(self):
       
        class MockResource(testresources.TestResource):

            def _makeResource(self):
                return "Boo!"
            _makeResource = classmethod(_makeResource)

        self.doTestNestedGetAndFinish(MockResource, "Boo!")    
