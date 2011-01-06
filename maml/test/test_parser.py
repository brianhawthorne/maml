"""
This file is part of Maml.

    Maml is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Maml is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Maml.  If not, see <http://www.gnu.org/licenses/>.

    Copyright 2010 Brian Hawthorne
"""
from unittest import TestCase

from maml.parser import *


example1 = """
-def A(z)
  %ul
    %li

%html
  %body
    %h3
"""

example2 = """
-def A(z)
  %ul
    -for x in range(z)
      .list-item#item_id
        = x
        foo

%html
  %body
    %h3 yup
    = A(6)
"""

class TestParser (TestCase):


    def test_tag_attrs(self):
        good_results = {
          '()': ('(', '', ')'),
          '{}': ('{', '', '}'),
          '(borp="baz" dorp="daz" blarp="blaz")':
            ('(', 'borp="baz" dorp="daz" blarp="blaz"', ')'),
          '{borp:"baz", dorp:"daz", blarp:"blaz"}':
            ('{', 'borp:"baz", dorp:"daz", blarp:"blaz"', '}'),
        }
        for input, output in good_results.items():
            self.assertEqual(tuple(tag_attrs.parseString(input)), output)

    def test_tag_decl(self):
        good_results = {
          '%html':
            ('%', 'html', ''),
          '%html foo':
            ('%', 'html', 'foo'),
          '%html= foo':
            ('%', 'html', '=', 'foo'),
          '%html()= foo':
            ('%', 'html', '(', '', ')', '=', 'foo'),
          '%html.class-name()= foo':
            ('%', 'html', '.', 'class-name', '(', '', ')', '=', 'foo'),
          '%html.class-name(borp="baz")= foo':
            ('%', 'html', '.', 'class-name', '(', 'borp="baz"', ')', '=', 'foo'),
          '#foo.boo':
            ('#', 'foo', '.', 'boo', ''),
          '.foo(){}':
            ('.', 'foo', '(', '', ')', '{', '', '}', ''),
        }
        for input, output in good_results.items():
            self.assertEqual(tuple(tag_decl.parseString(input)), output)

    def test_namespace(self):
        namespace_example = "-namespace(/common/defs.mak, bnorp)"
        assert Parser().parse(namespace_example).render_string()

