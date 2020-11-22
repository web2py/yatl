import cgi
import copy
import functools
import re
import marshal
from . import sanitizer
from .sanitizer import xmlescape, PY2

try:
    # python 2
    import copy_reg
except ImportError:
    # python 3
    import copyreg as copy_reg

    str, unicode = bytes, str

__all__ = [
    "A",
    "BEAUTIFY",
    "BODY",
    "CAT",
    "CODE",
    "DIV",
    "EM",
    "FORM",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "HEAD",
    "HTML",
    "IMG",
    "INPUT",
    "LABEL",
    "LI",
    "METATAG",
    "OL",
    "OPTION",
    "P",
    "PRE",
    "SELECT",
    "SPAN",
    "STRONG",
    "TABLE",
    "TAG",
    "TAGGER",
    "THEAD",
    "TBODY",
    "TD",
    "TEXTAREA",
    "TH",
    "TT",
    "TR",
    "UL",
    "XML",
    "xmlescape",
    "I",
    "META",
    "LINK",
    "TITLE",
    "STYLE",
    "SCRIPT",
]

INVALID_CHARS = set(" ='\"></")


# ################################################################
# New HTML Helpers
# ################################################################


def _vk(k):
    """validate atribute name of tag
        @k: atribute name
    """
    invalid_chars = set(k) & INVALID_CHARS
    if invalid_chars:
        raise ValueError("Invalid caracters %s in attribute name" % list(invalid_chars))
    return k


class TAGGER(object):
    def __init__(self, name, *children, **attributes):
        self.name = name
        self.children = list(children)
        self.attributes = attributes
        for child in self.children:
            if isinstance(child, TAGGER):
                child.parent = self

    def xml(self):
        name = self.name
        parts = []
        for key in sorted(self.attributes):
            value = self.attributes.get(key)
            if key.startswith("_") and not (value is False or value is None):
                if value is True:
                    value = _vk(key[1:])
                else:
                    value = xmlescape(unicode(value))
                parts.append('%s="%s"' % (_vk(key[1:]), value))
        joined = " ".join(parts)
        if joined:
            joined = " " + joined
        if name.endswith("/"):
            return "<%s%s/>" % (name[0:-1], joined)
        else:
            content = "".join(
                s.xml() if is_helper(s) else xmlescape(unicode(s))
                for s in self.children
            )
            return "<%s%s>%s</%s>" % (name, joined, content, name)

    def __unicode__(self):
        return self.xml()

    def __str__(self):
        data = self.xml()
        if PY2 and isinstance(data, unicode):
            data = data.encode("utf8")
        elif not PY2 and isinstance(data, bytes):
            data = data.decode("utf8")
        return data

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.children[key]
        else:
            return self.attributes.get(key)

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.children[key] = value
        else:
            self.attributes[key] = value

    def insert(self, i, value):
        self.children.insert(i, value)

    def append(self, value):
        self.children.append(value)

    def __delitem__(self, key):
        if isinstance(key, int):
            self.children = self.children[:key] + self.children[key + 1 :]
        else:
            del self.attributes[key]

    def __len__(self):
        return len(self.children)

    def amend(self, *children, **attributes):
        new_children = list(children) if children else copy.copy(self.children)
        new_attributes = copy.copy(self.attributes)
        new_attributes.update(**attributes)
        return TAGGER(self.name, *new_children, **new_attributes)

    regex_tag = re.compile("^[\w\-\:]+")
    regex_id = re.compile("#([\w\-]+)")
    regex_class = re.compile("\.([\w\-]+)")
    regex_attr = re.compile("\[([\w\-\:]+)=(.*?)\]")

    def find(self, query=None, **kargs):
        """
        Find all components that match the supplied attribute dictionary,
        or None if nothing could be found

        All components of the components are searched.

        Examples:

        >>> a = DIV(DIV(SPAN('x'),3,DIV(SPAN('y'))))
        >>> for c in a.find('span', first_only=True): c[0]='z'
        >>> print(a)
        <div><div><span>z</span>3<div><span>y</span></div></div></div>
        >>> for c in a.find('span'): c[0]='z'
        >>> print(a)
        <div><div><span>z</span>3<div><span>z</span></div></div></div>

        It also supports a syntax compatible with jQuery

        Examples:

        >>> a=TAG('<div><span><a id="1-1" u:v=$>hello</a></span><p class="this is a test">world</p></div>')
        >>> for e in a.find('div a#1-1, p.is'): print(e.flatten())
        hello
        world
        >>> for e in a.find('#1-1'): print(e.flatten())
        hello
        >>> a.find('a[u:v=$]')[0].xml()
        '<a id="1-1" u:v="$">hello</a>'
        >>> a=FORM( INPUT(_type='text'), SELECT(list(range(1))), TEXTAREA() )
        >>> for c in a.find('input, select, textarea'): c['_disabled'] = 'disabled'
        >>> a.xml()
        '<form action="#" enctype="multipart/form-data" method="post"><input disabled="disabled" type="text" /><select disabled="disabled"><option value="0">0</option></select><textarea cols="40" disabled="disabled" rows="10"></textarea></form>'

        Elements that are matched can also be replaced or removed by specifying
        a "replace" argument (note, a list of the original matching elements
        is still returned as usual).

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.find('span.abc', replace=P('x', _class='xyz'))
        >>> print(a)  # We should .xml() here instead of print
        <div><div><p class="xyz">x</p><div><p class="xyz">x</p><p class="xyz">x</p></div></div></div>

        "replace" can be a callable, which will be passed the original element and
        should return a new element to replace it.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.find('span.abc', replace=lambda el: P(el[0], _class='xyz'))
        >>> print(a)
        <div><div><p class="xyz">x</p><div><p class="xyz">y</p><p class="xyz">z</p></div></div></div>

        If replace=None, matching elements will be removed completely.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.find('span', text='y', replace=None)
        >>> print(a)
        <div><div><span class="abc">x</span><div><span class="abc">z</span></div></div></div>

        If a "text" argument is specified, elements will be searched for text
        components that match text, and any matching text components will be
        replaced (text is ignored if "replace" is not also specified).
        Like the "find" argument, "text" can be a string or a compiled regex.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.find(text=re.compile('x|y|z'), replace='hello')
        >>> print(a)
        <div><div><span class="abc">hello</span><div><span class="abc">hello</span><span class="abc">hello</span></div></div></div>

        If other attributes are specified along with text, then only components
        that match the specified attributes will be searched for text.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='efg'), SPAN('z', _class='abc'))))
        >>> b = a.find('span.efg', text=re.compile('x|y|z'), replace='hello')
        >>> print(a)
        <div><div><span class="abc">x</span><div><span class="efg">hello</span><span class="abc">z</span></div></div></div>
        """
        if query is not None:
            items = query.split()
            if len(items) > 1:
                subset = [
                    a.find(" ".join(items[1:]), **kargs) for a in self.find(items[0])
                ]
                return functools.reduce(lambda a, b: a + b, subset, [])
            item = items[0]
            if "#" in item or "." in item or "[" in item:
                match_tag = self.regex_tag.search(item)
                match_id = self.regex_id.search(item)
                match_class = self.regex_class.search(item)
                match_attr = self.regex_attr.finditer(item)
                args = []
                if match_tag:
                    args = [match_tag.group()]
                if match_id:
                    kargs["_id"] = match_id.group(1)
                if match_class:
                    kargs["_class"] = re.compile(
                        "(?<!\w)%s(?!\w)"
                        % match_class.group(1)
                        .replace("-", "\\-")
                        .replace(":", "\\:")
                    )
                for item in match_attr:
                    kargs["_" + item.group(1)] = item.group(2)
                return self.find(*args, **kargs)
        # make a copy of the components
        matches = []
        # check if the component has an attribute with the same
        # value as provided
        tag = self.name.replace("/", "")
        check = not (query and tag not in query)
        for (key, value) in kargs.items():
            if key not in ["first_only", "replace", "text"]:
                if isinstance(value, (str, int)):
                    if str(self[key]) != str(value):
                        check = False
                elif key in self.attributes:
                    if not value.search(str(self[key])):
                        check = False
                else:
                    check = False
        if "find" in kargs:
            find = kargs["find"]
            is_regex = not isinstance(find, (str, int))
            for c in self.children:
                if isinstance(c, str) and (
                    (is_regex and find.search(c)) or (str(find) in c)
                ):
                    check = True
        # if found, return the component
        if check:
            matches.append(self)

        first_only = kargs.get("first_only", False)
        replace = kargs.get("replace", False)
        text = replace is not False and kargs.get("text", False)
        is_regex = not isinstance(text, (str, int, bool))
        find_components = not (check and first_only)

        def replace_component(i):
            if replace is None:
                del self[i]
                return i
            else:
                self[i] = replace(self[i]) if callable(replace) else replace
                return i + 1

        # loop the components
        if text or find_components:
            i = 0
            while i < len(self.children):
                c = self[i]
                j = i + 1
                if (
                    check
                    and text
                    and isinstance(c, str)
                    and ((is_regex and text.search(c)) or (str(text) in c))
                ):
                    j = replace_component(i)
                elif find_components and isinstance(c, TAGGER):
                    child_matches = c.find(query, **kargs)
                    if len(child_matches):
                        if not text and replace is not False and child_matches[0] is c:
                            j = replace_component(i)
                        if first_only:
                            return child_matches
                        matches.extend(child_matches)
                i = j
        return matches


class METATAG(object):

    __all_tags__ = set()

    @classmethod
    def _add_tag(cls, name):
        cls.__all_tags__.add(name)

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, name):
        return lambda *children, **attributes: TAGGER(name, *children, **attributes)


class CAT(TAGGER):
    def __init__(self, *children):
        self.children = children

    def xml(self):
        return "".join(
            s.xml() if isinstance(s, TAGGER) else xmlescape(unicode(s))
            for s in self.children
        )


TAG = METATAG()
DIV = TAG.div
SPAN = TAG.span
LI = TAG.li
OL = TAG.ol
UL = TAG.ul
I = TAG.i
A = TAG.a
P = TAG.p
H1 = TAG.h1
H2 = TAG.h2
H3 = TAG.h3
H4 = TAG.h4
H5 = TAG.h5
H6 = TAG.h6
EM = TAG.em
TR = TAG.tr
TD = TAG.td
TH = TAG.th
TT = TAG.tt
PRE = TAG.pre
CODE = TAG.code
FORM = TAG.form
HEAD = TAG.head
HTML = TAG.html
BODY = TAG.body
TABLE = TAG.table
THEAD = TAG.thead
TBODY = TAG.tbody
LABEL = TAG.label
STYLE = TAG.style
STRONG = TAG.strong
SELECT = TAG.select
OPTION = TAG.option
TEXTAREA = TAG.textarea
TITLE = TAG.title
IMG = TAG["img/"]
INPUT = TAG["input/"]
META = TAG["meta/"]
LINK = TAG["link/"]
SCRIPT = lambda body, **attr: TAG.script(XML(body), **attr)


# ################################################################
# New XML Helpers
# ################################################################


class XML(TAGGER):
    """
    use it to wrap a string that contains XML/HTML so that it will not be
    escaped by the template

    Examples:

    >>> XML('<h1>Hello</h1>').xml()
    '<h1>Hello</h1>'
    """

    def __init__(
        self,
        text,
        sanitize=False,
        permitted_tags=[
            "a",
            "b",
            "blockquote",
            "br/",
            "i",
            "li",
            "ol",
            "ul",
            "p",
            "cite",
            "code",
            "pre",
            "img/",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "table",
            "tr",
            "td",
            "div",
            "strong",
            "span",
        ],
        allowed_attributes={
            "a": ["href", "title", "target"],
            "img": ["src", "alt"],
            "blockquote": ["type"],
            "td": ["colspan"],
        },
    ):
        """
        Args:
            text: the XML text
            sanitize: sanitize text using the permitted tags and allowed
                attributes (default False)
            permitted_tags: list of permitted tags (default: simple list of
                tags)
            allowed_attributes: dictionary of allowed attributed (default
                for A, IMG and BlockQuote).
                The key is the tag; the value is a list of allowed attributes.
        """

        if sanitize:
            text = sanitizer.sanitize(text, permitted_tags, allowed_attributes)
        if PY2 and isinstance(text, unicode):
            text = text.encode("utf8", "xmlcharrefreplace")
        elif not PY2 and isinstance(text, bytes):
            text = text.decode("utf8")
        self.text = text

    def xml(self):
        return unicode(self.text)

    def __str__(self):
        return self.text

    def __add__(self, other):
        return "%s%s" % (self, other)

    def __radd__(self, other):
        return "%s%s" % (other, self)

    def __cmp__(self, other):
        a, b = str(self), str(other)
        return (a > b) - (a < b)

    def __hash__(self):
        return hash(str(self))

    def __getitem__(self, i):
        return str(self)[i]

    def __getslice__(self, i, j):
        return str(self)[i:j]

    def __iter__(self):
        for c in str(self):
            yield c

    def __len__(self):
        return len(self.text)


def is_helper(helper):
    return hasattr(helper, "xml") and callable(helper.xml)


def XML_unpickle(data):
    return XML(marshal.loads(data))


def XML_pickle(data):
    return XML_unpickle, (marshal.dumps(str(data)),)


copy_reg.pickle(XML, XML_pickle, XML_unpickle)


# ################################################################
# BEAUTIFY everything
# ################################################################


def BEAUTIFY(obj):  # FIX ME, dealing with very large objects
    if is_helper(obj):
        return obj
    elif isinstance(obj, list):
        return UL(*[LI(BEAUTIFY(item)) for item in obj])
    elif isinstance(obj, dict):
        return TABLE(
            TBODY(*[TR(TH(key), TD(BEAUTIFY(value))) for key, value in obj.items()])
        )
    elif isinstance(obj, (str, unicode)):
        return XML(obj)
    else:
        return repr(obj)
