#
# A few thing worth noting:
# - Read-only cython attributes are emulated with read-only properties
# - Some basic types split into _types.pyi and shared among other files
# - Some inclusion files split into its own for easier management:
#   xmlerror, xpath
#

import logging
import sys
from typing import (
    IO,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Sized,
    SupportsBytes,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from ._types import (
    SupportsItems,
    _Dict_Tuple2AnyStr_Any,
    _DictAnyStr,
    _ExtensionArg,
    _ListAnyStr,
    _NonDefaultNSMapArg,
    _NSMapArg,
    basestring,
)
from ._xmlerror import _BaseErrorLog, _ErrorLog, _LogEntry
from ._xpath import _XPathEvaluatorBase, _XPathObject, _XPathVarArg
from .cssselect import _CSSTransArg

if sys.version_info < (3, 8):
    from typing_extensions import Literal, Protocol
else:
    from typing import Literal, Protocol

#
# Basic variables and constants
#

_T = TypeVar("_T")

_KnownEncodings = Literal[
    "ASCII",
    "ascii",
    "UTF-8",
    "utf-8",
    "UTF8",
    "utf8",
    "US-ASCII",
    "us-ascii",
]

#
# Smart string
#

class _ElementUnicodeResult(str):
    @property
    def is_attribute(self) -> bool: ...
    @property
    def is_tail(self) -> bool: ...
    @property
    def is_text(self) -> bool: ...
    @property
    def attrname(self) -> Optional[str]: ...
    def getparent(self) -> Optional[_Element]: ...

# Python 2.x only
class _ElementStringResult(bytes):
    @property
    def is_attribute(self) -> bool: ...
    @property
    def is_tail(self) -> bool: ...
    @property
    def is_text(self) -> bool: ...
    @property
    def attrname(self) -> Optional[bytes]: ...
    def getparent(self) -> Optional[_Element]: ...

#
# Qualified Name helper
#

class QName:
    def __init__(
        self,
        text_or_uri_or_element: Optional[Union[basestring, _Element]],
        tag: Optional[basestring] = ...,
    ) -> None: ...
    @property
    def localname(self) -> str: ...
    @property
    def namespace(self) -> Optional[str]: ...
    @property
    def text(self) -> str: ...
    # Emulate __richcmp__()
    def __ge__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __lt__(self, other: Any) -> bool: ...

_TagName = Union[basestring, QName]
_TagValue = Union[basestring, QName]  # FIXME Also accepts CDATA
# FIXME Tag filter is quite an oddball that it requires not the
# element classes, but the element factory *functions* themselves
# as value. Probably not typable.
_TagFilter = Union[
    Callable[..., _Element],
    _Element,
    QName,
    str,
]

# The base of _Element is *almost* an amalgam of MutableSequence[_Element]
# and mixin methods of Mapping[_Attrib], only missing bits here and there.
# Following the order of _Element methods code listing as much as possible
# for easier management.
class _Element(Iterable[_Element], Sized):
    #
    # Accessors
    #
    @overload
    def __setitem__(self, x: int, value: _Element) -> None: ...
    @overload
    def __setitem__(self, x: slice, value: Iterable[_Element]) -> None: ...
    @overload
    def __delitem__(self, x: int) -> None: ...
    @overload
    def __delitem__(self, x: slice) -> None: ...
    def set(self, key: _TagName, value: _TagName) -> None: ...
    def append(self, element: _Element) -> None: ...
    def addnext(self, element: _Element) -> None: ...
    def addprevious(self, element: _Element) -> None: ...
    def extend(self, elements: Iterable[_Element]) -> None: ...
    def clear(self, keep_tail: bool = ...) -> None: ...
    def insert(self, index: int, element: _Element) -> None: ...
    def remove(self, element: _Element) -> None: ...
    def replace(self, old_element: _Element, new_element: _Element) -> None: ...
    #
    # Common properties
    #
    # Most writable properties accept some incompatible types as
    # input argument, and they are canonicalized under the hook.
    # But both mypy and pyright aren't happy about this.
    #
    @property
    def tag(self) -> str: ...
    @tag.setter
    def tag(self, value: _TagValue) -> None: ...  # type: ignore
    @property
    def attrib(self) -> _Attrib: ...
    @property
    def text(self) -> Optional[str]: ...
    @text.setter
    def text(self, value: Optional[_TagValue]) -> None: ...  # type: ignore
    @property
    def tail(self) -> Optional[str]: ...
    @tail.setter
    def tail(self, value: Optional[_TagValue]) -> None: ...  # type: ignore
    #
    # _Element-only properties
    #
    # Following props are marked as read-only in comment,
    # but 'sourceline' and 'base' provide __set__ method
    # --- and they do work.
    #
    @property
    def prefix(self) -> Optional[str]: ...
    @property
    def sourceline(self) -> Optional[int]: ...
    @sourceline.setter
    def sourceline(self, value: int) -> None: ...
    @property
    def nsmap(self) -> Dict[Optional[str], str]: ...
    @property
    def base(self) -> Optional[str]: ...
    @base.setter
    def base(self, value: Optional[basestring]) -> None: ...  # type: ignore
    #
    # Accessors
    #
    @overload
    def __getitem__(self, x: int) -> _Element: ...
    @overload
    def __getitem__(self, x: slice) -> List[_Element]: ...
    def __len__(self) -> int: ...
    # For Python 2
    # def __nonzero__(self) -> bool: ...
    def __contains__(self, element: _Element) -> bool: ...
    # There are a hoard of element iterators used in lxml, with different
    # init arguments and different set of elements, but they all have one
    # thing in common: as iterator of elements. May as well just use most
    # generic type until specific need arises,
    def __iter__(self) -> Iterator[_Element]: ...
    def __reversed__(self) -> Iterator[_Element]: ...
    def index(
        self, child: _Element, start: Optional[int] = ..., end: Optional[int] = ...
    ) -> int: ...
    @overload
    def get(self, key: _TagName) -> Optional[str]: ...
    @overload
    def get(self, key: _TagName, default: _T) -> Union[str, _T]: ...
    def keys(self) -> List[str]: ...
    def values(self) -> List[str]: ...
    def items(self) -> List[Tuple[str, str]]: ...
    #
    # Remaining part of ElementTree API
    #
    def getparent(self) -> Optional[_Element]: ...
    def getnext(self) -> Optional[_Element]: ...
    def getprevious(self) -> Optional[_Element]: ...
    @overload
    def itersiblings(
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
        preceding: bool = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def itersiblings(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
        preceding: bool = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def iterancestors(
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def iterancestors(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
    ) -> Iterator[_Element]: ...
    @overload
    def iterdescendants(
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def iterdescendants(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
    ) -> Iterator[_Element]: ...
    @overload
    def iterchildren(
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
        reversed: bool = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def iterchildren(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
        reversed: bool = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def iter(
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def iter(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
    ) -> Iterator[_Element]: ...
    @overload
    def itertext(
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
        with_tail: bool = ...,
    ) -> Iterator[str]: ...
    @overload
    def itertext(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
        with_tail: bool = ...,
    ) -> Iterator[str]: ...
    def getroottree(self) -> _ElementTree: ...
    def makeelement(
        self,
        _tag: _TagName,
        # Final result is sort of like {**attrib, **_extra}
        attrib: Optional[SupportsItems[basestring, basestring]] = ...,
        nsmap: _NSMapArg = ...,
        **_extra: basestring,
    ) -> _Element: ...
    # XXX Note that the path str in find() and friends are NOT processed,
    # so feeding bytes would fail on py3
    def find(
        self, path: Union[str, QName], namespaces: _NSMapArg = ...
    ) -> Optional[_Element]: ...
    def findtext(
        self,
        path: Union[str, QName],
        default: Optional[str] = ...,
        namespaces: _NSMapArg = ...,
    ) -> Optional[str]: ...
    def findall(
        self,
        name: str,
        namespaces: _NSMapArg = ...,
    ) -> List[_Element]: ...
    def iterfind(
        self,
        path: Union[str, QName],
        namespaces: _NSMapArg = ...,
    ) -> Iterator[_Element]: ...
    def xpath(
        self,
        _path: basestring,
        namespaces: _NonDefaultNSMapArg = ...,
        extensions: Any = ...,
        smart_strings: bool = ...,
        **_variables: _XPathVarArg,
    ) -> _XPathObject[_Element]: ...
    def cssselect(
        self,
        expression: str,
        *,
        translator: _CSSTransArg = ...,
    ) -> List[_Element]: ...  # See CSSSelector class
    #
    # Following methods marked as deprecated upstream
    #
    def getchildren(self) -> List[_Element]: ...  # = list(self)
    @overload
    def getiterator(  # = self.iter()
        self,
        tag: Optional[Sequence[_TagFilter]] = ...,
    ) -> Iterator[_Element]: ...
    @overload
    def getiterator(
        self,
        tag: _TagFilter,
        *tags: _TagFilter,
    ) -> Iterator[_Element]: ...

class ElementBase(_Element): ...

class _ElementTree:
    parser = ...  # type: XMLParser
    def getpath(self, element: _Element) -> str: ...
    def getroot(self) -> _Element: ...
    def write(
        self,
        file: Union[basestring, IO[Any]],
        encoding: basestring = ...,
        method: basestring = ...,
        pretty_print: bool = ...,
        xml_declaration: Any = ...,
        with_tail: Any = ...,
        standalone: bool = ...,
        compression: int = ...,
        exclusive: bool = ...,
        with_comments: bool = ...,
        inclusive_ns_prefixes: _ListAnyStr = ...,
    ) -> None: ...
    def write_c14n(
        self,
        file: Union[basestring, IO[Any]],
        with_comments: bool = ...,
        compression: int = ...,
        inclusive_ns_prefixes: Iterable[basestring] = ...,
    ) -> None: ...
    def _setroot(self, root: _Element) -> None: ...
    def xpath(
        self,
        _path: basestring,
        namespaces: _NonDefaultNSMapArg = ...,
        extensions: Any = ...,
        smart_strings: bool = ...,
        **_variables: _XPathVarArg,
    ) -> _XPathObject[_Element]: ...
    def xslt(
        self,
        _xslt: XSLT,
        extensions: Optional[_Dict_Tuple2AnyStr_Any] = ...,
        access_control: Optional[XSLTAccessControl] = ...,
        **_variables: Any,
    ) -> _ElementTree: ...

class __ContentOnlyElement(_Element): ...
class _Comment(__ContentOnlyElement): ...

class _ProcessingInstruction(__ContentOnlyElement):
    target: basestring

class _Attrib:
    def __setitem__(self, key: basestring, value: basestring) -> None: ...
    def __delitem__(self, key: basestring) -> None: ...
    def update(
        self,
        sequence_or_dict: Union[
            _Attrib,
            Mapping[basestring, basestring],
            Sequence[Tuple[basestring, basestring]],
        ],
    ) -> None: ...
    def pop(self, key: basestring, default: basestring) -> basestring: ...
    def clear(self) -> None: ...
    def __repr__(self) -> str: ...
    def __copy__(self) -> _DictAnyStr: ...
    def __deepcopy__(self, memo: Dict[Any, Any]) -> _DictAnyStr: ...
    def __getitem__(self, key: basestring) -> basestring: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
    def get(
        self, key: basestring, default: basestring = ...
    ) -> Optional[basestring]: ...
    def keys(self) -> _ListAnyStr: ...
    def __iter__(self) -> Iterator[basestring]: ...  # actually _AttribIterator
    def iterkeys(self) -> Iterator[basestring]: ...
    def values(self) -> _ListAnyStr: ...
    def itervalues(self) -> Iterator[basestring]: ...
    def items(self) -> List[Tuple[basestring, basestring]]: ...
    def iteritems(self) -> Iterator[Tuple[basestring, basestring]]: ...
    def has_key(self, key: basestring) -> bool: ...
    def __contains__(self, key: basestring) -> bool: ...
    def __richcmp__(self, other: _Attrib, op: int) -> bool: ...

class _XSLTResultTree(_ElementTree, SupportsBytes):
    def __bytes__(self) -> bytes: ...

class _XSLTQuotedStringParam: ...

# https://lxml.de/parsing.html#the-target-parser-interface
class ParserTarget(Protocol):
    def comment(self, text: basestring) -> None: ...
    def close(self) -> Any: ...
    def data(self, data: basestring) -> None: ...
    def end(self, tag: basestring) -> None: ...
    def start(self, tag: basestring, attrib: Dict[basestring, basestring]) -> None: ...

class ElementClassLookup: ...

class FallbackElementClassLookup(ElementClassLookup):
    fallback: Optional[ElementClassLookup]
    def __init__(self, fallback: Optional[ElementClassLookup] = ...): ...
    def set_fallback(self, lookup: ElementClassLookup) -> None: ...

class CustomElementClassLookup(FallbackElementClassLookup):
    def lookup(
        self, type: str, doc: str, namespace: str, name: str
    ) -> Optional[Type[ElementBase]]: ...

class _BaseParser:
    def copy(self) -> _BaseParser: ...
    def makeelement(
        self,
        _tag: basestring,
        attrib: Optional[Union[_DictAnyStr, _Attrib]] = ...,
        nsmap: _NSMapArg = ...,
        **_extra: Any,
    ) -> _Element: ...
    def setElementClassLookup(
        self, lookup: Optional[ElementClassLookup] = ...
    ) -> None: ...
    def set_element_class_lookup(
        self, lookup: Optional[ElementClassLookup] = ...
    ) -> None: ...
    @property
    def error_log(self) -> _ErrorLog: ...

class _FeedParser(_BaseParser):
    def close(self) -> _Element: ...
    def feed(self, data: basestring) -> None: ...

class XMLParser(_FeedParser):
    def __init__(
        self,
        encoding: Optional[basestring] = ...,
        attribute_defaults: bool = ...,
        dtd_validation: bool = ...,
        load_dtd: bool = ...,
        no_network: bool = ...,
        ns_clean: bool = ...,
        recover: bool = ...,
        schema: Optional[XMLSchema] = ...,
        huge_tree: bool = ...,
        remove_blank_text: bool = ...,
        resolve_entities: bool = ...,
        remove_comments: bool = ...,
        remove_pis: bool = ...,
        strip_cdata: bool = ...,
        collect_ids: bool = ...,
        target: Optional[ParserTarget] = ...,
        compact: bool = ...,
    ) -> None: ...
    resolvers = ...  # type: _ResolverRegistry

class HTMLParser(_FeedParser):
    def __init__(
        self,
        encoding: Optional[basestring] = ...,
        collect_ids: bool = ...,
        compact: bool = ...,
        huge_tree: bool = ...,
        no_network: bool = ...,
        recover: bool = ...,
        remove_blank_text: bool = ...,
        remove_comments: bool = ...,
        remove_pis: bool = ...,
        schema: Optional[XMLSchema] = ...,
        strip_cdata: bool = ...,
        target: Optional[ParserTarget] = ...,
    ) -> None: ...

class _ResolverRegistry:
    def add(self, resolver: Resolver) -> None: ...
    def remove(self, resolver: Resolver) -> None: ...

class Resolver:
    def resolve(self, system_url: str, public_id: str): ...
    def resolve_file(
        self, f: IO[Any], context: Any, *, base_url: Optional[basestring], close: bool
    ): ...
    def resolve_string(
        self, string: basestring, context: Any, *, base_url: Optional[basestring]
    ): ...

class XMLSchema:
    def __init__(
        self,
        etree: Union[_Element, _ElementTree] = ...,
        file: Union[basestring, IO[Any]] = ...,
    ) -> None: ...
    def assertValid(self, etree: Union[_Element, _ElementTree]) -> None: ...

class XSLTAccessControl: ...

class XSLT:
    def __init__(
        self,
        xslt_input: Union[_Element, _ElementTree],
        extensions: _Dict_Tuple2AnyStr_Any = ...,
        regexp: bool = ...,
        access_control: XSLTAccessControl = ...,
    ) -> None: ...
    def __call__(
        self,
        _input: Union[_Element, _ElementTree],
        profile_run: bool = ...,
        **kwargs: Union[basestring, _XSLTQuotedStringParam],
    ) -> _XSLTResultTree: ...
    @staticmethod
    def strparam(s: basestring) -> _XSLTQuotedStringParam: ...
    @property
    def error_log(self) -> _ErrorLog: ...

def Comment(text: Optional[basestring] = ...) -> _Comment: ...
def Element(
    _tag: basestring,
    attrib: Optional[_DictAnyStr] = ...,
    nsmap: _NSMapArg = ...,
    **extra: basestring,
) -> _Element: ...
def SubElement(
    _parent: _Element,
    _tag: basestring,
    attrib: Optional[_DictAnyStr] = ...,
    nsmap: _NSMapArg = ...,
    **extra: basestring,
) -> _Element: ...
def ElementTree(
    element: _Element = ...,
    file: Union[basestring, IO[Any]] = ...,
    parser: XMLParser = ...,
) -> _ElementTree: ...
def ProcessingInstruction(
    target: basestring, text: basestring = ...
) -> _ProcessingInstruction: ...

PI = ProcessingInstruction

def HTML(
    text: basestring,
    parser: Optional[HTMLParser] = ...,
    base_url: Optional[basestring] = ...,
) -> _Element: ...
def XML(
    text: basestring,
    parser: Optional[XMLParser] = ...,
    base_url: Optional[basestring] = ...,
) -> _Element: ...
def cleanup_namespaces(
    tree_or_element: Union[_Element, _ElementTree],
    top_nsmap: _NSMapArg = ...,
    keep_ns_prefixes: Optional[Iterable[basestring]] = ...,
) -> None: ...
def parse(
    source: Union[basestring, IO[Any]],
    parser: XMLParser = ...,
    base_url: basestring = ...,
) -> _ElementTree: ...
def fromstring(
    text: basestring, parser: XMLParser = ..., *, base_url: basestring = ...
) -> _Element: ...
@overload
def tostring(
    element_or_tree: Union[_Element, _ElementTree],
    encoding: Union[Type[str], Literal["unicode"]],
    method: str = ...,
    xml_declaration: bool = ...,
    pretty_print: bool = ...,
    with_tail: bool = ...,
    standalone: bool = ...,
    doctype: str = ...,
    exclusive: bool = ...,
    with_comments: bool = ...,
    inclusive_ns_prefixes: Any = ...,
) -> str: ...
@overload
def tostring(
    element_or_tree: Union[_Element, _ElementTree],
    # Should be anything but "unicode", cannot be typed
    encoding: Optional[_KnownEncodings] = ...,
    method: str = ...,
    xml_declaration: bool = ...,
    pretty_print: bool = ...,
    with_tail: bool = ...,
    standalone: bool = ...,
    doctype: str = ...,
    exclusive: bool = ...,
    with_comments: bool = ...,
    inclusive_ns_prefixes: Any = ...,
) -> bytes: ...
@overload
def tostring(
    element_or_tree: Union[_Element, _ElementTree],
    encoding: Union[str, type] = ...,
    method: str = ...,
    xml_declaration: bool = ...,
    pretty_print: bool = ...,
    with_tail: bool = ...,
    standalone: bool = ...,
    doctype: str = ...,
    exclusive: bool = ...,
    with_comments: bool = ...,
    inclusive_ns_prefixes: Any = ...,
) -> basestring: ...

class Error(Exception): ...

class LxmlError(Error):
    def __init__(
        self, message: Any, error_log: Optional[_BaseErrorLog] = ...
    ) -> None: ...
    error_log: _BaseErrorLog = ...

class DocumentInvalid(LxmlError): ...
class LxmlSyntaxError(LxmlError, SyntaxError): ...
class ParseError(LxmlSyntaxError): ...
class XMLSyntaxError(ParseError): ...

class _Validator:
    @property
    def error_log(self) -> _ErrorLog: ...

class DTD(_Validator):
    def __init__(
        self, file: Union[basestring, IO[Any]] = ..., *, external_id: Any = ...
    ) -> None: ...
    def assertValid(self, etree: _Element) -> None: ...

_ElementFactory = Callable[[Any, Dict[basestring, basestring]], _Element]
_CommentFactory = Callable[[basestring], _Comment]
_ProcessingInstructionFactory = Callable[
    [basestring, basestring], _ProcessingInstruction
]

class TreeBuilder:
    def __init__(
        self,
        element_factory: Optional[_ElementFactory] = ...,
        parser: Optional[_BaseParser] = ...,
        comment_factory: Optional[_CommentFactory] = ...,
        pi_factory: Optional[_ProcessingInstructionFactory] = ...,
        insert_comments: bool = ...,
        insert_pis: bool = ...,
    ) -> None: ...
    def close(self) -> _Element: ...
    def comment(self, text: basestring) -> None: ...
    def data(self, data: basestring) -> None: ...
    def end(self, tag: basestring) -> None: ...
    def pi(self, target: basestring, data: Optional[basestring] = ...) -> Any: ...
    def start(self, tag: basestring, attrib: Dict[basestring, basestring]) -> None: ...

#
# Public members of xmlerror.pxi
#

def clear_error_log() -> None: ...

class PyErrorLog(_BaseErrorLog):
    @property
    def level_map(self) -> Dict[int, int]: ...
    def __init__(
        self, logger_name: Optional[str] = ..., logger: logging.Logger = ...
    ) -> None: ...
    # FIXME PyErrorLog.copy() is a dummy that doesn't really copy itself,
    # causing error on type checkers
    # def copy(self) -> _ListErrorLog: ...
    def log(self, log_entry: _LogEntry, message: str, *args: Any) -> None: ...

def use_global_python_log(log: PyErrorLog) -> None: ...

# Container for libxml2 constants
# TODO consider using enum.IntEnum?
class ErrorLevels:
    NONE: int = ...
    WARNING: int = ...
    ERROR: int = ...
    FATAL: int = ...

# It's overkill to include zillions of constants into type checker;
# and more no-no for updating constants along with each lxml releases
# unless these stubs are bundled with lxml together
class ErrorDomains:
    def __getattr__(self, name: str) -> int: ...

class ErrorTypes:
    def __getattr__(self, name: str) -> int: ...

class RelaxNGErrorTypes:
    def __getattr__(self, name: str) -> int: ...

#
# Public members of xpath.pxi
#

# TODO Belongs to extensions.pxi, to be moved
class XPathError(LxmlError): ...
class XPathSyntaxError(LxmlSyntaxError, XPathError): ...

class XPathElementEvaluator(_XPathEvaluatorBase):
    def __init__(
        self,
        element: _Element,
        *,
        namespaces: _NonDefaultNSMapArg = ...,
        extensions: _ExtensionArg = ...,
        regexp: bool = ...,
        smart_strings: bool = ...,
    ) -> None: ...
    def register_namespace(self, prefix: basestring, uri: basestring) -> None: ...
    def register_namespaces(self, prefix: basestring, uri: basestring) -> None: ...
    def __call__(
        self,
        path: basestring,
        **_variables: _XPathVarArg,
    ) -> _XPathObject[_Element]: ...

class XPathDocumentEvaluator(_XPathEvaluatorBase):
    def __init__(
        self,
        etree: _ElementTree,
        *,
        namespaces: _NonDefaultNSMapArg = ...,
        extensions: _ExtensionArg = ...,
        regexp: bool = ...,
        smart_strings: bool = ...,
    ) -> None: ...
    def __call__(
        self,
        path: basestring,
        **_variables: _XPathVarArg,
    ) -> _XPathObject[_Element]: ...

@overload
def XPathEvaluator(
    etree_or_element: _Element,
    *,
    namespaces: _NonDefaultNSMapArg = ...,
    extensions: _ExtensionArg = ...,
    regexp: bool = ...,
    smart_strings: bool = ...,
) -> XPathElementEvaluator: ...
@overload
def XPathEvaluator(
    etree_or_element: _ElementTree,
    *,
    namespaces: _NonDefaultNSMapArg = ...,
    extensions: _ExtensionArg = ...,
    regexp: bool = ...,
    smart_strings: bool = ...,
) -> XPathDocumentEvaluator: ...

class XPath(_XPathEvaluatorBase):
    def __init__(
        self,
        path: basestring,
        *,
        namespaces: _NonDefaultNSMapArg = ...,
        extensions: _ExtensionArg = ...,
        regexp: bool = ...,
        smart_strings: bool = ...,
    ) -> None: ...
    def __call__(
        self,
        _etree_or_element: Union[_Element, _ElementTree],
        **_variables: _XPathVarArg,
    ) -> _XPathObject[_Element]: ...
    @property
    def path(self) -> str: ...

class ETXPath(XPath):
    def __init__(
        self,
        path: basestring,
        *,
        extensions: _ExtensionArg = ...,
        regexp: bool = ...,
        smart_strings: bool = ...,
    ) -> None: ...
