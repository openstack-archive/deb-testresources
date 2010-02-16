#
#  testresources: extensions to python unittest to allow declaritive use
#  of resources by test cases.
#  Copyright (C) 2010  Robert Collins <robertc@robertcollins.net>
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

"""Test _resource_graph(resource_sets)."""

import testtools
import testresources
from testresources import split_by_resources, _resource_graph
from testresources.tests import ResultWithResourceExtensions
import unittest


def test_suite():
    from testresources.tests import TestUtil
    loader = TestUtil.TestLoader()
    result = loader.loadTestsFromName(__name__)
    return result


class TestResourceGraph(testtools.TestCase):

    def test_empty(self):
        no_resources = frozenset()
        resource_sets = [no_resources]
        self.assertEqual({no_resources:set([])}, _resource_graph(resource_sets))

    def test_discrete(self):
        resset1 = frozenset([testresources.TestResourceManager()])
        resset2 = frozenset([testresources.TestResourceManager()])
        resource_sets = [resset1, resset2]
        result = _resource_graph(resource_sets)
        self.assertEqual({resset1:set([]), resset2:set([])}, result)

    def test_overlapping(self):
        res1 = testresources.TestResourceManager()
        res2 = testresources.TestResourceManager()
        resset1 = frozenset([res1])
        resset2 = frozenset([res2])
        resset3 = frozenset([res1, res2])
        resource_sets = [resset1, resset2, resset3]
        result = _resource_graph(resource_sets)
        self.assertEqual(
            {resset1:set([resset3]),
             resset2:set([resset3]),
             resset3:set([resset1, resset2])},
            result)
