#  testresources: extensions to python unittest to allow declaritive use
#  of resources by test cases.
#  Copyright (C) 2005-2008  Robert Collins <robertc@robertcollins.net>
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

"""Example TestResource."""

from testresources import TestResource


class SampleTestResource(TestResource):

    setUpCost = 2
    tearDownCost = 2

    def make(self, dependency_resources):
        return "You need to implement your own getResource."


class MyResource(object):
    """My pet resource."""


class SampleWithDependencies(TestResource):

    resources = [('foo', SampleTestResource()), ('bar', SampleTestResource())]

    def make(self, dependency_resources):
        # dependency_resources will be {'foo': result_of_make_in_foo, 'bar':
        # result_of_make_in_bar}
        return MyResource()
