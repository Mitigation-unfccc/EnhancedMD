from abc import ABC
from typing import List


class Content:
	def __init__(
			self, string: str,
			italic: bool = False, bold: bool = False, underline: bool = False, strike: bool = False,
			superscript: bool = False, subscript: bool = False
	):
		#
		self.string: str = string

		# Font style properties
		self.italic: bool = italic
		self.bold: bool = bold
		self.underline: bool = underline
		self.strike: bool = strike
		self.superscript: bool = superscript
		self.subscript: bool = subscript

	def __repr__(self):
		return (f"string text: {repr(self.string)}"
		        f"\t(italic: {self.italic}, bold: {self.bold}, underline: {self.underline}, strike: {self.strike}, "
		        f"superscript: {self.superscript}, subscript: {self.subscript})")


class BaseElement(ABC):
	def __init__(
			self, content: List[Content], style: str,
			parent_element=None, children_elements=None, previous_element=None, next_element=None
	):
		#
		self.content: List[Content] = content
		self.style: str = style

		# Graph relations
		self.parent: BaseElement | None = parent_element
		self.children: List[BaseElement] | None = children_elements
		self.previous: BaseElement | None = previous_element
		self.next: BaseElement | None = next_element

		#
		self.text: str = ""


class Heading(BaseElement):
	def __init__(
			self,
			# BaseElement attributes
			content: List[Content], style: str,
			# Heading specific attributes
			# BaseElement attributes (with default)
			parent_element: BaseElement | None = None, children_elements: List[BaseElement] | None = None,
			previous_element: BaseElement | None = None, next_element: BaseElement | None = None
			# Heading specific attributes (with default)
	):
		# BaseElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)


class Paragraph(BaseElement):
	def __init__(
			self,
			# BaseElement attributes
			content: List[Content], style: str,
			# Paragraph specific attributes
			# BaseElement attributes (with default)
			parent_element: BaseElement | None = None, children_elements: List[BaseElement] | None = None,
			previous_element: BaseElement | None = None, next_element: BaseElement | None = None
			# Paragraph specific attributes (with default)
	):
		# BaseElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)


class Table(BaseElement):
	def __init__(
			self,
			# BaseElement attributes
			content: List[Content], style: str,
			# Table specific attributes
			# BaseElement attributes (with default)
			parent_element: BaseElement | None = None, children_elements: List[BaseElement] | None = None,
			previous_element: BaseElement | None = None, next_element: BaseElement | None = None
			# Table specific attributes (with default)
	):
		# BaseElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)


class Hyperlink(BaseElement):
	def __init__(
			self,
			# BaseElement attributes
			content: List[Content], style: str,
			# Hyperlink specific attributes
			# BaseElement attributes (with default)
			parent_element: BaseElement | None = None, children_elements: List[BaseElement] | None = None,
			previous_element: BaseElement | None = None, next_element: BaseElement | None = None
			# Hyperlink specific attributes (with default)
	):
		# BaseElement initialization
		super().__init__(
			content=content, style=style,
			parent_element=parent_element, children_elements=children_elements,
			previous_element=previous_element, next_element=next_element
		)
