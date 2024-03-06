from abc import ABC, abstractmethod
from typing import List

from enhanced_md.exceptions import UndefinedTextFormatError


class Content:
	def __init__(
			self, string: str,
			italic: bool = False, bold: bool = False, underline: bool = False, strike: bool = False,
			superscript: bool = False, subscript: bool = False
	):
		#
		self.string: str = string

		# Font style properties
		self.font_style = {
			"italic": italic, "bold": bold, "underline": underline, "strike": strike,
			"superscript": superscript, "subscript": subscript
		}

	def __repr__(self):
		return f"string text: {repr(self.string)}\t(font style: {self.font_style})"

	def string_to_html(self) -> str:
		# TODO (en html \n -> <br>)
		return self.string

	def string_to_md(self) -> str:
		# TODO
		return self.string

class BaseElement(ABC):
	def __init__(
			self, content, text_format: str = "html"
	):
		#
		self.content = content

		#
		self.text_format: str = text_format
		self._check_text_format(text_format=self.text_format)
		self._construct_text_from_content()

	@staticmethod  # Not necessary to re-implement
	def _check_text_format(text_format: str):
		if text_format not in ["html", "md", "plain"]:
			raise UndefinedTextFormatError(f"Undefined text format found: {text_format}"
			                               f"\n Text format options = [\"html\", \"md\", \"plain\"")

	def _construct_text_from_content(self):
		if self.text_format == "html":
			self.text = self._construct_html_text_from_content()
		elif self.text_format == "md":
			self.text = self._construct_md_text_from_content()
		elif self.text_format == "plain":
			self.text = self._construct_plain_text_from_content()

	@abstractmethod
	def _construct_html_text_from_content(self) -> str:
		pass

	@abstractmethod
	def _construct_md_text_from_content(self) -> str:
		pass

	@abstractmethod
	def _construct_plain_text_from_content(self) -> str:
		pass


class Hyperlink(BaseElement):
	def __init__(
			self, content: List[Content], address: str, fragment: str, text_format: str = "html"
	):
		# BaseElement initialization
		super().__init__(content=content, text_format=text_format)

		#
		if len(address):
			self.link = address
			self.type = "url"
		elif len(fragment):
			self.link = fragment
			self.type = "jump"
		else:
			self.link = ""
			self.type = None

	def _construct_html_text_from_content(self) -> str:
		# TODO
		text = ""

		if self.type == "url":
			return f"<a href={self.link}>{self.text}</a>"
		elif self.type == "jump":
			return ""
		else:
			return ""

	def _construct_md_text_from_content(self) -> str:
		# TODO
		return ""

	def _construct_plain_text_from_content(self) -> str:
		# TODO
		return ""


class DirectedElement(BaseElement):
	def __init__(
			self, content: List[Content | BaseElement], item: List[int],
			style: str, text_format: str = "html",
			parent_element=None, children_elements=None, previous_element=None, next_element=None
	):
		# BaseElement initialization
		super().__init__(content=content, text_format=text_format)

		#
		self.item = item
		self.style = style

		# Graph relations
		self.parent: DirectedElement | None = parent_element
		self.children: List[DirectedElement] | None = children_elements
		self.previous: DirectedElement | None = previous_element
		self.next: DirectedElement | None = next_element

	@abstractmethod
	def _construct_html_text_from_content(self) -> str:
		pass

	@abstractmethod
	def _construct_md_text_from_content(self) -> str:
		pass

	@abstractmethod
	def _construct_plain_text_from_content(self) -> str:
		pass


class Heading(DirectedElement):
	def __init__(
			self,
			# DirectedElement attributes
			content: List[Content | BaseElement], item: List[int], style: str,
			# Heading specific attributes
			# DirectedElement attributes (with default)
			text_format: str = "html",
			parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
			previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None
			# Heading specific attributes (with default)
	):
		# DirectedElement initialization
		super().__init__(
			content=content, item=item, style=style, text_format=text_format,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)

	def _construct_html_text_from_content(self) -> str:
		# TODO
		return ""

	def _construct_md_text_from_content(self) -> str:
		# TODO
		return ""

	def _construct_plain_text_from_content(self) -> str:
		# TODO
		return ""


class Paragraph(DirectedElement):
	def __init__(
			self,
			# DirectedElement attributes
			content: List[Content | BaseElement], item: List[int], heading_item: List[int] | None, style: str,
			# Paragraph specific attributes
			# DirectedElement attributes (with default)
			text_format: str = "html",
			parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
			previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None
			# Paragraph specific attributes (with default)
	):
		# DirectedElement initialization
		super().__init__(
			content=content, item=item, style=style, text_format=text_format,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)

		self.heading_item = heading_item

	def _construct_html_text_from_content(self) -> str:
		# TODO
		return ""

	def _construct_md_text_from_content(self) -> str:
		# TODO
		return ""

	def _construct_plain_text_from_content(self) -> str:
		# TODO
		return ""


class Table(DirectedElement):
	def __init__(
			self,
			# DirectedElement attributes
			content: List[Content | BaseElement], item: List[int], style: str,
			# Table specific attributes
			# DirectedElement attributes (with default)
			text_format: str = "html",
			parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
			previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None
			# Table specific attributes (with default)
	):
		# DirectedElement initialization
		super().__init__(
			content=content, item=item, style=style, text_format=text_format,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)

	def _construct_html_text_from_content(self) -> str:
		return ""

	def _construct_md_text_from_content(self) -> str:
		return ""

	def _construct_plain_text_from_content(self) -> str:
		return ""
