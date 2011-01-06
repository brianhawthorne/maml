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

import sys
from cStringIO import StringIO
from pyparsing import *

# python identifiers
identifier = Word(alphas+'_', alphanums+'_')

# for DOM ids and css classes (allow dashes)
html_identifier = Word(alphas+'_-', alphanums+'_-')

# html tag
tag_name = '%' + identifier
tag_class = '.' + html_identifier
tag_id = '#' + html_identifier
tag_literal_attrs = '(' + SkipTo(')') + ')'
tag_dynamic_attrs = '{' + SkipTo('}') + '}'
tag_attrs = ZeroOrMore(tag_literal_attrs) + ZeroOrMore(tag_dynamic_attrs)
tag_decl = ((tag_name + ZeroOrMore( tag_class | tag_id )) | OneOrMore( tag_class | tag_id )) + Optional(tag_attrs) + Optional('=') + SkipTo(StringEnd())

# mako *def*
def_decl = "-def" + SkipTo(StringEnd())

# mako *for*
for_decl = ( '-for' + SkipTo(StringEnd()) )

# mako *if*
if_decl = ( '-if' + SkipTo(StringEnd()) )

# mako *namespace*
namespace_decl = ( '-namespace' + SkipTo(StringEnd()) )


def attrs(*attrnames):
    def makeprop(name):
        return property(lambda self: getattr(self, '_%s'% name))
    caller_locals = sys._getframe(1).f_locals
    for attrname in attrnames:
        caller_locals[attrname] = makeprop(attrname)


################################################################################
class IndentingStreamWrapper (object):

    def __init__(self, stream, indent='  '):
        self._stream = stream
        self._indent = indent
        self._indent_level = 0

    def indent(self):
        self._indent_level += 1

    def dedent(self):
        self._indent_level -= 1

    def write(self, s):
        self._stream.write(self._indent_level*self._indent + s)

    def writeln(self, s):
        self._stream.writeln(self._indent_level*self._indent + s)

    def __getattr__(self, attr):
        "Delegate to wrapped stream for everything else."
        return getattr(self._stream, attr)


################################################################################
class ParseNode (object):
    attrs(
      'parent',
      'name',
      'children',
    )

    def __init__(self, parent=None, name='', children=None):
        self._parent = parent
        self._name = name
        self._children = children or []
        if isinstance(self.children, basestring):
            raise Exception()

    @property
    def root(self):
        if self._parent is None:
            return self
        return self._parent.root

    def render(self, outs):
        raise NotImplementedError(
          'the render method must be implemented by a subclass')

    def render_string(self):
        outs = StringIO()
        self.render(outs)
        return outs.getvalue()


################################################################################
class Literal (ParseNode):

    def __init__(self, parent, text):
        ParseNode.__init__(self, parent, text)

    @property
    def children(self):
        return ()

    def render(self, outs):
        print >> outs, self.name


################################################################################
class Expression (ParseNode):

    def __init__(self, parent, text):
        ParseNode.__init__(
          self, parent, text.replace('{','\{').replace('}','\}'))

    def render(self, outs):
        print >> outs, '${%s}'% self._name

    def __repr__(self):
        return '<%s:%s>'% (self.__class__.__name__, self.name)


################################################################################
class Block (ParseNode):
    attrs(
      'decl',
    )

    def __init__(self, parent=None, name='', decl=''):
        self._decl = decl
        ParseNode.__init__(self, parent, name, [])

    def __repr__(self):
        return '<%s:%s %s>'% (self.__class__.__name__, self.name, `self.decl`)

    def render_start(self, outs):
        pass

    def render_children(self, outs):
        for child in self.children:
            if isinstance(child, basestring):
                print >> outs, child
            else:
                child.render(outs)
 
    def render_end(self, outs):
        pass

    def render(self, outs):
        is_root = not bool(self._parent)

        if is_root:
            outs = IndentingStreamWrapper(outs)

        self.render_start(outs)
        if not is_root: outs.indent()
        self.render_children(outs)
        if not is_root: outs.dedent()
        self.render_end(outs)


class HtmlTagAttrs (Expression):
    pass

class DynamicHtmlTagAttrs (Expression):


    def __init__(self, parent, text):
        text = "' '.join('%%s=\"%%s\"'%% item for item in {%s}.items())"% text
        Expression.__init__(self, parent=parent, text=text)


################################################################################
class HtmlTag (Block):
    attrs(
      'tagname',
      'classes',
      'identifier',
      'attrs'
    )

    SELF_CLOSING_TAGS = (
      'area',
      'base',
      'basefont',
      'br',
      'hr',
      'input',
      'img',
      'link',
      'meta',
    )

    def __init__(self, parent, line):
        parts = tag_decl.parseString(line) #line.split(' ', 1)

        self._tagname = 'div'
        self._classes = []
        self._identifier = None
        self._attrs = []
        child = None

        while parts:
            kind = parts.pop(0)
            if not parts:
                content = kind
            else:
                content = parts.pop(0)

            if kind == '%':
                self._tagname = content
            elif kind == '.':
                self._classes.append(content)
            elif kind == '#':
                self._identifier = content
            elif kind == '{':
                assert parts.pop(0) == '}'
                self._attrs.append(DynamicHtmlTagAttrs(None, content))
            elif kind == '(':
                assert parts.pop(0) == ')'
                self._attrs.append(Literal(None, content))
            elif kind == '=':
                child = Expression(self, content)
            elif content:
                child = Literal(self, content)

        Block.__init__(self, parent, self._tagname, line)

        if child:
            if self.is_self_closing:
                raise ParseException(
                  "oops, can't add child content to a self-closing tag")
            self.children.append(child)

    @property
    def is_self_closing(self):
        return self._tagname.lower() in self.SELF_CLOSING_TAGS

    def render_start(self, outs):
        class_str = ' class="%s"'% ' '.join(self.classes) if self.classes else ''
        ident_str = ' id="%s"'% self.identifier if self.identifier else ''
        attrs_str = ' %s' % ' '.join(a.render_string() for a in self.attrs) if self.attrs else ''
        closing_str = ' /' if self.is_self_closing else ''
        print >> outs, '<%s%s%s%s%s>'% \
          (self._tagname, ident_str, class_str, attrs_str, closing_str)

    def render_end(self, outs):
        if not self.is_self_closing:
            print >> outs, '</%s>'% self._tagname


################################################################################
class Statement (Block):

    MAKO_TAGS = (
      'page',
      'include',
      'def',
      'namespace',
      'inherit',
      'namespacename',
      'call',
      'doc',
      'text',
      'return',
    )
    MAKO_CONTROLS = (
      'if',
      'elif',
      'else',
      'for',
    )

    def __init__(self, parent, line):
        parts = line.split(' ', 1)
        decl = parts[1] if len(parts)>1 else ''
        name = parts[0][1:]
        Block.__init__(self, parent, name, decl)

        if name == 'def':
            self.parsed = def_decl.parseString(line)
        elif name == 'for':
            self.parsed = for_decl.parseString(line)
        elif name == 'if':
            self.parsed = if_decl.parseString(line)
        elif name == 'namespace':
            self.parsed = namespace_decl.parseString(line)
        else:
            self.parsed = []

    def __repr__(self):
        return '<%s:%s %s>'% (self.__class__.__name__, self.name, `self.parsed`)

    def render_start(self, outs):
        name = self.name
        decl = self.decl.replace('"','\"')

        if name == 'page':
            opentag = '<%%%s args="%s">'% (name, decl)
        elif name == 'def':
            opentag = '<%%%s name="%s">'% (name, decl)
        elif name == 'include':
            opentag = '<%%%s file="%s">'% (name, decl)
        elif name == 'namespace':
            args = decl.split()
            filename = args[0]
            importname = args[1] if len(args)>1 else None
            importstr = ' import="%s"'% importname if importname else ''
            opentag = '<%%%s file="%s"%s />'% (name, filename, importstr)
        elif name == 'inherit':
            opentag = '<%%%s file="%s">'% (name, decl)
        elif name == 'return':
            opentag = '<% return %>'
        elif name == 'namespacename':
            opentag = ''
        elif name in self.MAKO_TAGS:
            opentag = '<%%%s %s>'% (name, self.parsed[-1])
        elif name in self.MAKO_CONTROLS:
            opentag = '%% %s %s:'% (name, self.parsed[-1])
        else:
            opentag = '<%%%s>'% name

        print >> outs, opentag

    def render_end(self, outs):
        name = self.name

        if name in ('return', 'namespace'):
            closetag = ''
        elif name in self.MAKO_TAGS:
            closetag = '</%%%s>'% name
        elif name in ('if', 'for'):
            closetag = '%% end%s'% name
        else:
            closetag = ''

        print >> outs, closetag


################################################################################
class Parser (object):

    class Stack (list):

        @property
        def indent(self):
            return self[-1][0]

        @property
        def block(self):
            return self[-1][1]

        def pop(self):
            if len(self)==1:
                raise IndexError("can't pop the final item")
            return list.pop(self)

        def push(self, item):
            self.append(item)

    def __init__(self):
        self._block = Block()
        self._indent_stack = self.Stack([(0, self._block)])
        self._stmt = None
        self._tag = None

    def parse(self, document):
        stack = self._indent_stack

        for line in [l for l in document.splitlines() if l]:

            line_indent, node = self.parse_line(line)

            # a new indent block has started
            if line_indent > stack.indent:
                stack.push((line_indent, self._block.children[-1]))

            # one or more indent blocks may have finished
            while line_indent < stack.indent:
                stack.pop()

            self._block = stack.block
            self._block.children.append(node)

        return self._block.root

    def parse_line(self, indented_line):
        line = indented_line.lstrip()
        line_indent = len(indented_line) - len(line)
        first_char = line[0]

        node = line
        block = self._block

        if first_char in ('%', '.', '#'):
            node = HtmlTag(block, line)
        elif first_char == '=':
            node = Expression(block, line[1:])
        elif first_char == '-':
            node = Statement(block, line)
        else:
            node = Literal(block, line)

        return line_indent, node


