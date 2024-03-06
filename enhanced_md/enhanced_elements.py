from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from enum import Enum, auto
from enhanced_md.exceptions import UndefinedTextFormatError


class TextFormat(Enum):
    HTML = auto()
    MD = auto()
    PLAIN = auto()


class LinkType(Enum):
    URL = auto()
    JUMP = auto()
    NONE = auto()


class Content:
    __slots__ = ("string", "font_style")

    def __init__(
            self, string: str,
            italic: bool = False, bold: bool = False, underline: bool = False, strike: bool = False,
            superscript: bool = False, subscript: bool = False
    ) -> None:
        self.string: str = string
        self.font_style: dict[str, bool] = {
            "italic": italic, "bold": bold, "underline": underline, "strike": strike,
            "superscript": superscript, "subscript": subscript
        }

    def __repr__(self) -> str:
        return f"string text: {repr(self.string)}\t(font style: {self.font_style})"

    def string_to_html(self) -> str:
        html_tags = {
            "italic": ("i", "i"),
            "bold": ("b", "b"),
            "underline": ("u", "u"),
            "strike": ("strike", "strike"),
            "superscript": ("sup", "sup"),
            "subscript": ("sub", "sub"),
        }
        html_string = self.string.replace('\n', '<br>')
        for style, (start_tag, end_tag) in html_tags.items():
            if self.font_style[style]:
                html_string = f"<{start_tag}>{html_string}</{end_tag}>"
        return html_string

    def string_to_md(self) -> str:
        md_tags = {
            "italic": ("*", "*"),
            "bold": ("**", "**"),
            "strike": ("~~", "~~"),
            # For superscript and subscript, Markdown doesn't have a standard notation, so HTML tags are used.
            "superscript": ("<sup>", "</sup>"),
            "subscript": ("<sub>", "</sub>"),
        }
        md_string = self.string
        for style, (start, end) in md_tags.items():
            if self.font_style[style]:
                md_string = f"{start}{md_string}{end}"
        return md_string


class BaseElement(ABC):
    __slots__ = ("content", "text_format", "text")

    def __init__(self, content: List[Content], text_format: str = TextFormat.HTML) -> None:
        self.content: List[Content] = content
        self._check_text_format(text_format)
        self.text_format: str = text_format
        self.text: str = self._construct_text_from_content()

    @staticmethod
    def _check_text_format(text_format: str) -> None:
        if text_format not in TextFormat:
            raise UndefinedTextFormatError(
                f"Undefined text format found: {text_format}. Options are: [\"html\", \"md\", \"plain\"]")

    def _construct_text_from_content(self) -> str:
        construct_method = {
            "html": self._construct_html_text_from_content,
            "md": self._construct_md_text_from_content,
            "plain": self._construct_plain_text_from_content,
        }.get(self.text_format, self._construct_plain_text_from_content)
        return construct_method()

    def _construct_html_text_from_content(self) -> str:
        return ''.join([content.string_to_html() for content in self.content])

    def _construct_md_text_from_content(self) -> str:
        return ''.join([content.string_to_md() for content in self.content])

    def _construct_plain_text_from_content(self) -> str:
        return ''.join([content.string for content in self.content])


class Hyperlink(BaseElement):

    __slots__ = ("link", "type")

    def __init__(self, content: List[Content], address: str = "", fragment: str = "",
                 text_format: str = TextFormat.HTML) -> None:
        super().__init__(content=content, text_format=text_format)
        if address and fragment:
            raise ValueError("Hyperlink cannot have both an address and a fragment. Choose one.")
        self.link = address or f"#{fragment}" if fragment else "#"
        self.type = LinkType.URL if address else LinkType.JUMP if fragment else LinkType.NONE

    def _construct_html_text_from_content(self) -> str:
        full_content = super()._construct_html_text_from_content()
        if self.type in [LinkType.URL, LinkType.JUMP]:
            return f'<a href="{self.link}">{full_content}</a>'
        return full_content

    def _construct_md_text_from_content(self) -> str:
        full_content = super()._construct_md_text_from_content()
        if self.type in [LinkType.URL, LinkType.JUMP]:
            return f'[{full_content}]({self.link})'
        return full_content

    def _construct_plain_text_from_content(self) -> str:
        full_content = super()._construct_plain_text_from_content()
        if self.type == LinkType.URL:
            return f'{full_content} ({self.link})'
        return full_content


class DirectedElement(BaseElement):

    __slots__ = ("style", "parent", "children", "previous", "next")

    def __init__(
            self, content: List[Content], style: str, text_format: str = "html",
            parent_element: DirectedElement | None = None,
            children_elements: List[DirectedElement | None] = None,
            previous_element: DirectedElement | None = None,
            next_element: DirectedElement | None = None
    ) -> None:
        super().__init__(content=content, text_format=text_format)
        self.style = style
        self.parent = parent_element
        self.children = children_elements if children_elements is not None else []
        self.previous = previous_element
        self.next = next_element

    def add_child(self, child: DirectedElement) -> None:
        self.children.append(child)
        child.parent = self


class Heading(DirectedElement):

    __slots__ = "level"

    def __init__(
            self, content: List[Content], style: str, text_format: str = "html",
            parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
            previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None):
        super().__init__(content=content, style=style, text_format=text_format,
                         parent_element=parent_element, children_elements=children_elements,
                         previous_element=previous_element, next_element=next_element)


class Paragraph(DirectedElement):

    __slots__ = "level"

    def __init__(
            self, content: List[Content], style: str, text_format: str = "html",
            parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
            previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None):
        super().__init__(
            content=content, style=style, text_format=text_format,
            parent_element=parent_element, children_elements=children_elements,
            previous_element=previous_element, next_element=next_element
        )


class Table(DirectedElement):

    __slots__ = "level"

    def __init__(self, content: List[Content], style: str, text_format: str = "html",
                 parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
                 previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None):
        super().__init__(content=content, style=style, text_format=text_format,
                         parent_element=parent_element, children_elements=children_elements,
                         previous_element=previous_element, next_element=next_element)

    def _construct_html_text_from_content(self) -> str:
        return ""

    def _construct_md_text_from_content(self) -> str:
        return ""

    def _construct_plain_text_from_content(self) -> str:
        return ""
