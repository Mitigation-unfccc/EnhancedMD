from abc import ABC, abstractmethod
from typing import List
import re


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


class BaseElement(ABC):
	def __init__(
			self, content: List[Content]
	):
		#
		self.content: List[Content] = content
		self.text: str = self._construct_text_from_content()

	@abstractmethod
	def _construct_text_from_content(self):
		pass


class Hyperlink(BaseElement):
	def __init__(
			self, content: List[Content], address: str, fragment: str
	):
		# BaseElement initialization
		super().__init__(content=content)

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

	def _construct_text_from_content(self):
		return ""


class DirectedElement(BaseElement):
	def __init__(
			self, content: List[Content], style: str,
			parent_element=None, children_elements=None, previous_element=None, next_element=None
	):
		# BaseElement initialization
		super().__init__(content=content)

		#
		self.style: str = style

		# Graph relations
		self.parent: DirectedElement | None = parent_element
		self.children: List[DirectedElement] | None = children_elements
		self.previous: DirectedElement | None = previous_element
		self.next: DirectedElement | None = next_element

	@abstractmethod
	def _construct_text_from_content(self):
		return ""


class Heading(DirectedElement):
	def __init__(
			self,
			# DirectedElement attributes
			content: List[Content], style: str,
			# Heading specific attributes
			# DirectedElement attributes (with default)
			parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
			previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None
			# Heading specific attributes (with default)
	):
		# DirectedElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)

	def _construct_text_from_content(self):
		return ""


class Paragraph(DirectedElement):
	def __init__(
			self,
			# DirectedElement attributes
			content: List[Content], style: str,
			# Paragraph specific attributes
			# DirectedElement attributes (with default)
			parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
			previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None
			# Paragraph specific attributes (with default)
	):
		# DirectedElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)

	def _construct_text_from_content(self):
		return ""


class Table(DirectedElement):
	def __init__(
			self,
			# DirectedElement attributes
			content: List[Content], style: str,
			# Table specific attributes
			# DirectedElement attributes (with default)
			parent_element: DirectedElement | None = None, children_elements: List[DirectedElement] | None = None,
			previous_element: DirectedElement | None = None, next_element: DirectedElement | None = None
			# Table specific attributes (with default)
	):
		# DirectedElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)

	def _construct_text_from_content(self):
		return ""
