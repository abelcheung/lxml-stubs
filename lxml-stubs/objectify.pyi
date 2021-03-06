from typing import Any, Union

from lxml.etree import ElementBase, XMLParser

class ObjectifiedElement(ElementBase):
    pass

def fromstring(
    text: Union[bytes, str],
    parser: XMLParser = ...,
    *,
    base_url: Union[bytes, str] = ...
) -> ObjectifiedElement: ...
