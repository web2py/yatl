import cgi
import copy
from . import sanitizer
from . sanitizer import xmlescape, PY2

try:
    # python 2
    import copy_reg
except ImportError:
    # python 3
    import copyreg as copy_reg
    str, unicode = bytes, str

__all__ = [
    'A', 'BEAUTIFY', 'BODY', 'CAT', 'CODE', 'DIV', 'EM', 'FORM', 
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'HEAD', 'HTML', 'IMG', 
    'INPUT', 'LABEL', 'LI', 'METATAG', 'OL', 'OPTION', 'P', 'PRE', 
    'SELECT', 'SPAN', 'STRONG', 'TABLE', 'TAG', 'TAGGER', 'THEAD', 
    'TBODY', 'TD', 'TEXTAREA', 'TH', 'TT', 'TR', 'UL', 'XML', 
    'xmlescape', 'I', 'META', 'LINK', 'TITLE', 'STYLE', 'SCRIPT']

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
            value = self.attributes[key]
            if key.startswith('_') and not (value is False or value is None):
                if value is True:
                    value = _vk(key[1:])
                else:
                    value = xmlescape(unicode(value))
                parts.append('%s="%s"' % (_vk(key[1:]), value))
        joined = ' '.join(parts)
        if joined:
            joined = ' '+joined
        if name.endswith('/'):
            return '<%s%s/>' % (name[0:-1], joined)
        else:
            content = ''.join(
                s.xml() if is_helper(s) 
                else xmlescape(unicode(s))
                for s in self.children)
            return '<%s%s>%s</%s>' %(name, joined, content, name)
    
    def __unicode__(self):
        return self.xml()

    def __str__(self):
        data = self.xml()
        if PY2 and isinstance(data, unicode):
            data = data.encode('utf8')
        elif not PY2 and isinstance(data, bytes):
            data = data.decode('utf8')
        return data

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.children[key]
        else:
            return self.attributes[key]

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.children[key] = value
        else:
            self.attributes[key] =  value

    def insert(self, i, value):
        self.children.insert(i,value)
            
    def append(self, value):
        self.children.append(value)

    def __delitem__(self,key):
        if isinstance(key, int):
            self.children = self.children[:key]+self.children[key+1:]
        else:
            del self.attributes[key]

    def __len__(self):
        return len(self.children)

    def find(self, query):
        raise NotImplementedError

    def amend(self, *children, **attributes):
        new_children = list(children) if children else copy.copy(self.children)
        new_attributes = copy.copy(self.attributes)
        new_attributes.update(**attributes)
        return TAGGER(self.name, *new_children, **new_attributes)


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
        return ''.join(s.xml() if isinstance(s,TAGGER) else xmlescape(unicode(s)) for s in self.children)


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
SCRIPT = TAG.script
STYLE = TAG.style
STRONG = TAG.strong
SELECT = TAG.select
OPTION = TAG.option
TEXTAREA = TAG.textarea
TITLE = TAG.title
IMG = TAG['img/']
INPUT = TAG['input/']
META = TAG['meta/']
LINK = TAG['link/']


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
            'a','b','blockquote','br/','i','li','ol','ul','p','cite',
            'code','pre','img/','h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'table', 'tr', 'td', 'div','strong', 'span'],
        allowed_attributes={
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt'],
            'blockquote': ['type'],
            'td': ['colspan']},
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
            text = text.encode('utf8', 'xmlcharrefreplace')
        elif not PY2 and isinstance(text, bytes):
            text = text.decode('utf8')
        self.text = text

    def xml(self):
        return unicode(self.text)

    def __str__(self):
        return self.text

    def __add__(self, other):
        return '%s%s' % (self, other)

    def __radd__(self, other):
        return '%s%s' % (other, self)

    def __cmp__(self, other):
        return cmp(str(self), str(other))

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
    return hasattr(helper, 'xml') and callable(helper.xml)

def XML_unpickle(data):
    return XML(marshal.loads(data))

def XML_pickle(data):
    return XML_unpickle, (marshal.dumps(str(data)),)
copy_reg.pickle(XML, XML_pickle, XML_unpickle)


# ################################################################
# BEAUTIFY everything
# ################################################################

def BEAUTIFY(obj): # FIX ME, dealing with very large objects
    if is_helper(obj):
        return obj
    elif isinstance(obj, list):
        return UL(*[LI(BEAUTIFY(item)) for item in  obj])
    elif isinstance(obj, dict):
        return TABLE(TBODY(*[TR(TH(key),TD(BEAUTIFY(value))) for key, value in obj.items()]))
    elif isinstance(obj, (str, unicode)):
        return XML(obj)
    else:
        return repr(obj)
