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

import mako.template

from maml.parser import Parser

_mako_compile_text = mako.template._compile_text
_mako_compile_module_file = mako.template._compile_module_file

def _maml_compile_text(template, text, filename):
    if filename and filename.rsplit('.', 1)[-1] == 'maml':
        text = Parser().parse(text).render_string()
    return _mako_compile_text(template, text, filename)

def _maml_compile_module_file(template, text, filename, outputpath):
    if filename and filename.rsplit('.', 1)[-1] == 'maml':
        text = Parser().parse(text).render_string()
    return _mako_compile_module_file(template, text, filename, outputpath)

def patch_into_mako():
    mako.template._compile_text = _maml_compile_text
    mako.template._compile_module_file = _maml_compile_module_file
