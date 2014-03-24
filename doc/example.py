#  testresources: extensions to python unittest to allow declaritive use
#  of resources by test cases.
#
#  Copyright (c) 2005-2010 Testresources Contributors
#  
#  Licensed under either the Apache License, Version 2.0 or the BSD 3-clause
#  license at the users choice. A copy of both licenses are available in the
#  project source as Apache-2.0 and BSD. You may not use this file except in
#  compliance with one of these two licences.
#  
#  Unless required by applicable law or agreed to in writing, software distributed
#  under these licenses is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#  CONDITIONS OF ANY KIND, either express or implied.  See the license you chose
#  for the specific language governing permissions and limitations under that
#  license.
#

"""Example TestResourceManager."""

from testresources import TestResourceManager


class SampleTestResource(TestResourceManager):

    setUpCost = 2
    tearDownCost = 2

    def make(self, dependency_resources):
        return "You need to implement your own getResource."


class MyResource(object):
    """My pet resource."""


class SampleWithDependencies(TestResourceManager):

    resources = [('foo', SampleTestResource()), ('bar', SampleTestResource())]

    def make(self, dependency_resources):
        # dependency_resources will be {'foo': result_of_make_in_foo, 'bar':
        # result_of_make_in_bar}
        return MyResource()
