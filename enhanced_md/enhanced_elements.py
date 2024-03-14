from __future__ import annotations

import re
from abc import ABC
from enum import Enum, auto
from enhanced_md.exceptions import UndefinedTextFormatError

from docx.text.paragraph import Paragraph as DocxParagraph
from docx.text.hyperlink import Hyperlink as DocxHyperlink
from docx.table import Table as DocxTable

# Define general docx element type
DocxElement = DocxHyperlink | DocxParagraph | DocxTable

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
    ):
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
            # For underline, superscript and subscript, Markdown doesn't have a standard notation, so HTML tags are used
            "underline": ("<u>", "</u>"),
            "superscript": ("<sup>", "</sup>"),
            "subscript": ("<sub>", "</sub>"),
        }
        md_string = self.string
        for style, (start, end) in md_tags.items():
            if self.font_style[style]:
                md_string = f"{start}{md_string}{end}"
        return md_string


class BaseElement(ABC):
    __slots__ = ("content", "docx_element", "text_format", "text")

    def __init__(self, content: list[Content | BaseElement], docx_element: DocxElement,
                 text_format: TextFormat = TextFormat.HTML):
        self.content: list[Content | BaseElement] = content
        self.docx_element: DocxElement = docx_element
        self._check_text_format(text_format)
        self.text_format: TextFormat = text_format
        self.text: str = self._construct_text_from_content()

    @staticmethod
    def _check_text_format(text_format: TextFormat):
        if text_format not in TextFormat:
            raise UndefinedTextFormatError(
                f"Undefined text format found: {text_format}. Options are: [\"html\", \"md\", \"plain\"]")

    def _construct_text_from_content(self) -> str:
        construct_method = {
            "html": self._construct_html_text_from_content,
            "md": self._construct_md_text_from_content,
            "plain": self._construct_plain_text_from_content,
        }.get(str(self.text_format), self._construct_plain_text_from_content)
        return construct_method()

    @staticmethod
    def clean_html_tags(text: str) -> str:
        # Define tag pairs to be cleaned
        tag_pairs = {
            "italic": ("i", "i"),
            "bold": ("b", "b"),
            "underline": ("u", "u"),
            "strike": ("strike", "strike"),
            "superscript": ("sup", "sup"),
            "subscript": ("sub", "sub"),
        }

        # Iterate through tag pairs and replace consecutive tags
        for tag in tag_pairs.values():
            opening_tag, closing_tag = tag
            pattern = re.compile(f"</{closing_tag}>\\s*<{opening_tag}>")
            text = pattern.sub(" ", text)

        return text

    @staticmethod
    def clean_and_merge_markdown(text: str) -> str:
        # Patterns to identify Markdown syntax for bold, italic, strikethrough, superscript, and subscript
        markdown_patterns = {
            "bold": r"\*\*(.*?)\*\*",
            "italic": r"\*(.*?)\*",
            "strike": r"~~(.*?)~~",
            "superscript": r"<sup>(.*?)</sup>",
            "subscript": r"<sub>(.*?)</sub>",
        }

        # Pattern to find unnecessary repeated Markdown without content
        cleanup_patterns = {
            "bold": r"\*\*\s*\*\*",
            "italic": r"\*\s*\*",
            "strike": r"~~\s*~~",
            "superscript": r"<sup>\s*</sup>",
            "subscript": r"<sub>\s*</sub>",
        }

        # First, remove any unnecessary repeated Markdown syntax
        for pattern in cleanup_patterns.values():
            text = re.sub(pattern, " ", text)

        # Now, merge adjacent markdown patterns
        for key, pattern in markdown_patterns.items():
            # Create a regex to find adjacent patterns
            merge_regex = re.compile(f"({pattern})\s+({pattern})")
            while True:
                # Look for matches to merge
                match = merge_regex.search(text)
                if not match:
                    break  # Exit loop if no more matches
                # Extract matched texts without the Markdown syntax
                text1, text2 = match.group(1), match.group(3)
                # Determine the Markdown syntax based on the key
                if key in ["bold", "italic", "strike"]:
                    md_open, md_close = match.group(2)[0] * 2, match.group(2)[-1] * 2
                else:  # For superscript and subscript
                    md_open = f"<{key}>"
                    md_close = f"</{key}>"
                # Replace the matched text with merged version
                merged_text = f"{md_open}{text1} {text2}{md_close}"
                text = text[:match.start()] + merged_text + text[match.end():]

        return text

    def _construct_html_text_from_content(self) -> str:
        return self.clean_html_tags(
            ''.join([content.string_to_html() if isinstance(content, Content)
                     else content._construct_html_text_from_content() for content in self.content])
        )

    def _construct_md_text_from_content(self) -> str:
        return self.clean_and_merge_markdown(
            ''.join([content.string_to_md() if isinstance(content, Content)
                     else content._construct_md_text_from_content() for content in self.content])
        )

    def _construct_plain_text_from_content(self) -> str:
        return ''.join([content.string if isinstance(content, Content)
                        else content._construct_plain_text_from_content() for content in self.content])


class Hyperlink(BaseElement):

    __slots__ = ("link", "type")

    def __init__(self, content: list[Content], docx_element: DocxElement, address: str = "", fragment: str = "",
                 text_format: TextFormat = TextFormat.HTML):
        if address and fragment:
            raise ValueError("Hyperlink cannot have both an address and a fragment")
        self.link = address or f"#{fragment}" if fragment else "#"
        self.type = LinkType.URL if address else LinkType.JUMP if fragment else LinkType.NONE
        super().__init__(content=content, docx_element=docx_element, text_format=text_format)

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

    __slots__ = ("style", "hierarchy_level", "parent", "children", "previous", "next", "item",
                 "has_numbering", "numbering_xml_info", "numbering_index", "numbering")

    def __init__(
            self, content: list[Content], docx_element: DocxElement, style: str, hierarchy_level: int,
            text_format: TextFormat = TextFormat.HTML,
            parent_element: DirectedElement | None = None,
            children_elements: list[DirectedElement | None] = None,
            previous_element: DirectedElement | None = None,
            next_element: DirectedElement | None = None
    ):
        super().__init__(content=content, docx_element=docx_element, text_format=text_format)
        self.style: str = style
        self.hierarchy_level: int = hierarchy_level
        self.parent: DirectedElement = parent_element
        self.children: list[DirectedElement] = children_elements if children_elements is not None else []
        self.previous: DirectedElement = previous_element
        self.next: DirectedElement = next_element
        self.item: list[int] | None = None
        self._has_numbering()  # Initializes has_numbering and numbering_xml_info
        self.numbering_index: int | None = None
        self.numbering: str | None = None

    def add_child(self, child: DirectedElement):
        self.children.append(child)
        child.parent = self

    def add_next(self, next_element: DirectedElement):
        self.next = next_element
        next_element.previous = self

    def construct_identifier_string(self) -> str:
        return ".".join(map(str, self.item))

    def _has_numbering(self):
        num_id, ilvl = self._obtain_num_id_and_ilvl()
        if num_id is None:  # If no numPr has been found inside pPr or style then it has no numbering
            return

        # Detect whether there exists a num with given numId
        if len(self.docx_element._element.xpath(f".//w:num[@w:numId={num_id}]")) != 0:
            self.has_numbering = True
            self._obtain_numbering_xml_info(num_id=num_id, ilvl=ilvl)
        else:
            pass

    def _obtain_num_id_and_ilvl(self) -> tuple[str | None, str | None]:

        # Detect whether style numPr has been overridden in pPr and Obtain numId and ilvl inside numPr
        if len(self.docx_element._element.xpath(".//w:numPr")) != 0:
            num_id = self.docx_element._element.xpath(".//w:numPr/w:numId/@w:val")[0]
            i_lvl = self.docx_element._element.xpath(".//w:numPr/w:ilvl/@w:val")[0]
        else:
            # Detect whether numPr exists inside style
            if len(self.docx_element.style._element.xpath(".//w:numPr")) == 0:
                self.has_numbering = False
                return None, None  # Return None to signal has_numbering already assigned and stop procedure

            num_id = self.docx_element.style._element.xpath(".//w:numPr/w:numId/@w:val")[0]
            i_lvl = self.docx_element.style._element.xpath(".//w:numPr/w:ilvl/@w:val")[0]

        return num_id, i_lvl

    def _obtain_numbering_xml_info(self, num_id: str, ilvl: str):
        abstract_num_id = self.docx_element._element.xpath(f".//w:num[@w:numId={num_id}/w:abstractNumId/@w:val]")
        self.numbering_xml_info = {
            "type": self.docx_element._element.xpath(
                f".//w:abstractNum[@w:abstractNumId={abstract_num_id}]/w:lvl[@w:ilvl={ilvl}]/w:numFmt/@w:val")[0],
            "format": self.docx_element._element.xpath(
                f".//w:abstractNum[@w:abstractNumId={abstract_num_id}]/w:lvl[@w:ilvl={ilvl}]/w:lvlText/@w:val")[0],
            "start": int(self.docx_element._element.xpath(
                f".//w:abstractNum[@w:abstractNumId={abstract_num_id}]/w:lvl[@w:ilvl={ilvl}]/w:start/@w:val")[0])
        }



class Heading(DirectedElement):

    def __init__(
            self, content: list[Content], docx_element: DocxElement, style: str, hierarchy_level: int,
            text_format: TextFormat = TextFormat.HTML,
            parent_element: DirectedElement | None = None, children_elements: list[DirectedElement] | None = None,
            previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None):
        super().__init__(
            content=content, docx_element=docx_element,
            style=style, hierarchy_level=hierarchy_level, text_format=text_format,
            parent_element=parent_element, children_elements=children_elements,
            previous_element=previous_element, next_element=next_element
        )


class Paragraph(DirectedElement):

    __slots__ = "heading_item"

    def __init__(
            self, content: list[Content], docx_element: DocxElement, style: str, hierarchy_level: int,
            text_format: TextFormat = TextFormat.HTML,
            parent_element: DirectedElement | None = None, children_elements: list[DirectedElement] | None = None,
            previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None):
        super().__init__(
            content=content, docx_element=docx_element,
            style=style, hierarchy_level=hierarchy_level, text_format=text_format,
            parent_element=parent_element, children_elements=children_elements,
            previous_element=previous_element, next_element=next_element
        )
        self.heading_item = None

    def add_child(self, child: DirectedElement):
        super().add_child(child=child)
        child.heading_item = self.heading_item

    def add_next(self, next_element: DirectedElement):
        super().add_next(next_element=next_element)
        if not isinstance(next_element, Heading):
            next_element.heading_item = self.heading_item

    def construct_identifier_string(self) -> str:
        return (f"({'.'.join(map(str, self.heading_item)) if self.heading_item is not None else 'NONE'})"
                f"\nP_{super().construct_identifier_string()}")


class Table(DirectedElement):

    __slots__ = "heading_item"

    def __init__(self, content: list[Content], docx_element: DocxElement, style: str, hierarchy_level: int,
                 text_format: TextFormat = TextFormat.HTML,
                 parent_element: DirectedElement | None = None, children_elements: list[DirectedElement] | None = None,
                 previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None):
        super().__init__(
            content=content, docx_element=docx_element,
            style=style, hierarchy_level=hierarchy_level, text_format=text_format,
            parent_element=parent_element, children_elements=children_elements,
            previous_element=previous_element, next_element=next_element
        )
        self.heading_item = None

    def _construct_html_text_from_content(self) -> str:
        return ""

    def _construct_md_text_from_content(self) -> str:
        return ""

    def _construct_plain_text_from_content(self) -> str:
        return ""

    def add_child(self, child: DirectedElement):
        super().add_child(child=child)
        child.heading_item = self.heading_item

    def add_next(self, next_element: DirectedElement):
        super().add_next(next_element=next_element)
        if not isinstance(next_element, Heading):
            next_element.heading_item = self.heading_item

    def construct_identifier_string(self) -> str:
        return f"({'.'.join(map(str, self.heading_item))})\nT_{super().construct_identifier_string()}"
