import logging
import re
from typing import List

import docx

from enhanced_md import enhanced_elements
from enhanced_md.exceptions import UndefinedStyleFoundError


class EnhancedMD:
	def __init__(self, docx_file_path: str, styles: dict):
		"""

		"""

		#
		self.docx_file_path = docx_file_path
		logging.info(f"\t[{self.docx_file_path}]")
		self.docx = docx.Document(docx_file_path)
		self._get_docx_metadata()
		self._log_docx_metadata()

		#
		self._check_and_unpack_styles(styles=styles)
		self._log_styles()

		#
		self.doc_graph = None
		self.doc_flat = None

	def __call__(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		"""

		self.build_doc_graph()

	def __repr__(self):
		# TODO
		return print(self.doc_graph)

	def _get_docx_metadata(self):
		"""
		Obtains .docx document metadata dictionary from python-docx CoreProperties object
		:return:
		"""

		self.docx_metadata = {
			"title": self.docx.core_properties.title,
			"created_at": self.docx.core_properties.created,
			"created_by": self.docx.core_properties.author,
			"modified_at": self.docx.core_properties.modified,
			"modified_by": self.docx.core_properties.last_modified_by
		}

	def _log_docx_metadata(self):
		logging.info(
			f"\t(metadata)"
			f"\n\t\t- title: {self.docx_metadata['title']}"
			f"\n\t\t- created: {self.docx_metadata['created_at']} ({self.docx_metadata['created_by']})"
			f"\n\t\t- last modified: {self.docx_metadata['modified_at']} ({self.docx_metadata['modified_by']})"
		)

	def _check_and_unpack_styles(self, styles: dict):
		"""

		:param styles:
		:return:
		"""

		# Check heading styles
		try:
			self.heading_styles = styles["heading"]
			self._check_style_dict(style_dict=self.heading_styles, element_name="heading")
		except KeyError:
			raise KeyError("styles dictionary missing \"heading\"")

		# Check paragraph styles
		try:
			self.paragraph_styles = styles["paragraph"]
			self._check_style_dict(style_dict=self.paragraph_styles, element_name="paragraph")
		except KeyError:
			raise KeyError("styles dictionary missing \"paragraph\"")

		# TODO: Check that styles for different elements are not the same (except level 0)

	@staticmethod
	def _check_style_dict(style_dict: dict, element_name: str):
		"""

		:param style_dict:
		:return:
		"""

		hierarchy_levels = style_dict.keys()

		# Check style dictionary hierarchy levels consist only of integers
		if not all(isinstance(key, int) for key in hierarchy_levels):
			raise KeyError(f"{element_name} style dictionary hierarchy levels keys must consist only of integers")

		# Check style dictionary hierarchy levels range from 0 to the maximum level without any gaps
		# and that no hierarchy level is empty except for hierarchy level 0
		for key in range(max(hierarchy_levels)+1):
			try:
				# Checks first for KeyError and only can raise ValueError for hierarchy levels higher than 0
				if not style_dict[key] and key:
					raise ValueError(f"{element_name} style dictionary, {key} hierarchy level cannot be empty")
			except KeyError:
				raise KeyError(f"{element_name} style dictionary, {key} hierarchy level must be defined")

	def _log_styles(self):
		logging.info(
			f"\t(styles)"
			f"\n\t\t- heading styles: {self.heading_styles}"
			f"\n\t\t- paragraph styles: {self.paragraph_styles}"
		)

	def build_doc_graph(self):
		"""

		:return:
		"""

		self.doc_graph = []

		for docx_content in self.docx.iter_inner_content():
			# Detect whether document content is paragraph or table and process accordingly
			if isinstance(docx_content, docx.text.paragraph.Paragraph):
				# Only process paragraphs which are not empty or only consist of space, tabular or newline characters
				if len(docx_content.text) and not all(c in " \t\n" for c in docx_content.text):
					self._process_docx_paragraph(docx_paragraph=docx_content)

			if isinstance(docx_content, docx.table.Table):
				# Only process tables which are not empty
				if len(docx_content.rows) and len(docx_content.columns):
					self._process_docx_table(docx_table=docx_content)

			print(self.doc_graph)


	def _process_docx_paragraph(self, docx_paragraph: docx.text.paragraph.Paragraph):
		"""

		:param docx_paragraph:
		"""

		#
		paragraph_content = self._process_docx_paragraph_content(docx_paragraph=docx_paragraph)

		#
		directed_element_type, hierarchy_level = self._detect_directed_element_type_and_hierarchy_level(
			docx_paragraph=docx_paragraph
		)

		print(f"{'#' * hierarchy_level}{directed_element_type}")

		if directed_element_type == "heading":
			self._build_heading_subtree(
				heading={"content": paragraph_content, "style":docx_paragraph.style.name},
				hierarchy_level=hierarchy_level
			)

		else:
			# directed_element_type == "paragraph":
			pass

	def _build_heading_subtree(self, heading: dict, hierarchy_level: int):
		"""

		:param heading:
		:param hierarchy_level:
		:return:
		"""

		#
		if not len(self.doc_graph):
			self.doc_graph.append({
				"directed_element": enhanced_elements.Heading(
					content=heading["content"],
					style=heading["style"],
					item=[0]
				),
				"hierarchy_level": hierarchy_level
			})
		elif hierarchy_level:
			prev_directed_element = self.doc_graph[-1]
			#
			if isinstance(prev_directed_element["directed_element"], enhanced_elements.Heading):
				#
				if prev_directed_element["hierarchy_level"] == hierarchy_level:
					self._append_heading_into_doc_graph(
						heading=heading, hierarchy_level=hierarchy_level,
						item=self._get_new_item_same_level(prev_item=prev_directed_element["directed_element"].item)
					)
				elif prev_directed_element["hierarchy_level"] < hierarchy_level:
					self._append_heading_into_doc_graph(
						heading=heading, hierarchy_level=hierarchy_level,
						item=self._get_new_item_lower_level(prev_item=prev_directed_element["directed_element"].item)
					)
				else:
					# prev_directed_element["hierarchy_level"] > hierarchy_level
					#
					self._merge_heading_into_heading_subtree(hierarchy_level=hierarchy_level)

					prev_directed_element = self.doc_graph[-1]  # Refresh previous directed element
					self._append_heading_into_doc_graph(
						heading=heading, hierarchy_level=hierarchy_level,
						item=self._get_new_item_same_level(prev_item=prev_directed_element["directed_element"].item)
					)
			else:
				# Previous directed element is Paragraph or Table
				self._merge_non_heading_into_heading_subtree()

				prev_directed_element = self.doc_graph[-1]  # Refresh previous directed element
				self._append_heading_into_doc_graph(
					heading=heading, hierarchy_level=hierarchy_level,
					item=self._get_new_item_same_level(prev_item=prev_directed_element["directed_element"].item)
				)

		else:
			pass

	def _append_heading_into_doc_graph(self, heading: dict, hierarchy_level: int, item: List[int]):
		"""

		:param heading:
		:param hierarchy_level:
		:param item:
		:return:
		"""

		self.doc_graph.append({
			"directed_element": enhanced_elements.Heading(
				content=heading["content"],
				style=heading["style"],
				item=item
			),
			"hierarchy_level": hierarchy_level
		})

	def _merge_heading_into_heading_subtree(self, hierarchy_level: int):
		"""

		:param hierarchy_level:
		:return:
		"""

		curr_heading = self.doc_graph.pop()
		curr_children = [curr_heading["directed_element"]]
		while curr_heading["hierarchy_level"] > hierarchy_level:
			prev_heading = self.doc_graph[-1]

			if prev_heading["hierarchy_level"] == curr_heading["hierarchy_level"]:  # Vertical merge
				prev_heading["directed_element"].next = curr_heading["directed_element"]
				curr_heading["directed_element"].previous = prev_heading["directed_element"]
			else:  # Horizontal merge
				prev_heading["directed_element"].children = curr_children
				for children in curr_children:
					children.parent = prev_heading["directed_element"]
				curr_children = []

			curr_heading = self.doc_graph.pop()
			curr_children.append(curr_heading["directed_element"])

	def _merge_non_heading_into_heading_subtree(self):
		pass

	def _build_paragraph_subtree(self, paragraph: enhanced_elements.Heading, hierarchy_level: int):
		"""

		:param paragraph:
		:param hierarchy_level:
		"""

		pass

	def _merge_paragraph_into_paragraph_subtree(self):
		pass

	@staticmethod
	def _get_new_item_same_level(prev_item):
		"""

		:param prev_item:
		"""

		new_item = prev_item.copy()  # Make a copy to avoid pass by reference errors
		new_item[-1] += 1

		return  new_item

	@staticmethod
	def _get_new_item_lower_level(prev_item):
		"""

		:param prev_item:
		"""

		new_item = prev_item.copy()  # Make a copy to avoid pass by reference errors
		new_item += [0]

		return new_item

	def _process_docx_paragraph_content(
			self, docx_paragraph: docx.text.paragraph.Paragraph
	) -> List[enhanced_elements.Content | enhanced_elements.Hyperlink]:
		"""

		:param docx_paragraph:
		:return paragraph_content:
		"""

		paragraph_content = []
		#
		for docx_paragraph_content in docx_paragraph.iter_inner_content():
			# Only process paragraph contents which are not empty
			if len(docx_paragraph_content.text):
				# Detect whether paragraph content is run or hyperlink and process accordingly
				if isinstance(docx_paragraph_content, docx.text.run.Run):
					run_content = self._process_docx_run(docx_run=docx_paragraph_content)

					# Apply special paragraph_content concat
					paragraph_content = self._concat_run_content_to_content_list(
						content_list=paragraph_content,
						run_content=run_content
					)

				elif isinstance(docx_paragraph_content, docx.text.hyperlink.Hyperlink):
					paragraph_content.append(self._process_docx_hyperlink(docx_hyperlink=docx_paragraph_content))

		return paragraph_content

	@staticmethod
	def _process_docx_run(docx_run: docx.text.run.Run) -> List[enhanced_elements.Content]:
		"""

		:param docx_run:
		:return run_content:
		"""

		# Split run text by spaces, sequences of word characters ('-' included), and punctuation characters
		pattern = r"(\s|[\w-]+|\W)"
		content_split = re.findall(pattern, docx_run.text)

		run_content = []
		#
		for content in content_split:
			run_content.append(
				enhanced_elements.Content(
					string=content,
					# Font style attributes return either True or None
					italic=(True if docx_run.font.italic is not None else False),
					bold=(True if docx_run.font.bold is not None else False),
					underline=(True if docx_run.font.underline is not None else False),
					strike=(True if docx_run.font.strike is not None else False),
					superscript=(True if docx_run.font.superscript is not None else False),
					subscript=(True if docx_run.font.subscript is not None else False)
				)
			)

		return run_content

	def _process_docx_hyperlink(self, docx_hyperlink: docx.text.hyperlink.Hyperlink) -> enhanced_elements.Hyperlink:
		"""

		:param docx_hyperlink:
		:return hyperlink:
		"""

		hyperlink_content = []
		#
		for docx_hyperlink_content in docx_hyperlink.runs:
			run_content = self._process_docx_run(docx_run=docx_hyperlink_content)

			# Apply special hyperlink_content concat
			hyperlink_content = self._concat_run_content_to_content_list(
				# Even though content_list can contain other hyperlinks, it will always consist of runs in this case
				content_list=hyperlink_content,
				run_content=run_content
			)

		return enhanced_elements.Hyperlink(
			content=hyperlink_content, address=docx_hyperlink.address, fragment=docx_hyperlink.fragment
		)

	def _concat_run_content_to_content_list(
			self,
	        content_list: List[enhanced_elements.Content | enhanced_elements.Hyperlink],
			run_content: List[enhanced_elements.Content]
	) -> List[enhanced_elements.Content | enhanced_elements.Hyperlink]:
		"""

		:param content_list:
		:param run_content:
		:return content_list:
		"""

		# Only if content_list is not empty and previous content is content class
		if len(content_list) and isinstance(content_list[-1], enhanced_elements.Content):
			# Detect whether the special concat is needed
			is_special_concat = self._detect_special_content_concat(
				content_a=content_list[-1], content_b=run_content[0]
			)
		else:
			is_special_concat = False

		# Apply special concat if detected else normal concat
		if is_special_concat:
			# Join junction last content_list and first run_content strings
			# (does not matter which content is chosen to define font style since they must be the same)
			content_list[-1].string += run_content[0].string
			content_list += run_content[1:]
		else:
			content_list += run_content

		return content_list

	@staticmethod
	def _detect_special_content_concat(
			content_a: enhanced_elements.Content, content_b: enhanced_elements.Content
	) -> bool:
		"""

		:param content_a:
		:param content_b:
		:return is_special_concat:
		"""

		return (
			# Content A string ends with word character ('-' included)
			bool(re.search(r"[\w-]$", content_a.string))
			# Content B string begins with word character ('-' included)
			and bool(re.search(r"^[\w-]", content_b.string))
			# Last paragraph_content and first run_content have the same font style attributes
			and content_a.font_style == content_b.font_style
		)

	def _detect_directed_element_type_and_hierarchy_level(
			self, docx_paragraph: docx.text.paragraph.Paragraph
	) -> (str, int):
		"""

		:param docx_paragraph:
		:return directed_element_type, hierarchy_level:
		"""

		#
		heading_hl = self._detect_hierarchy_level(docx_paragraph=docx_paragraph, styles_dict=self.heading_styles)
		if heading_hl is not None and heading_hl:
			return "heading", heading_hl

		#
		paragraph_hl = self._detect_hierarchy_level(docx_paragraph=docx_paragraph, styles_dict=self.paragraph_styles)
		if paragraph_hl is not None and paragraph_hl:
			return "paragraph", paragraph_hl

		#
		if heading_hl is None:
			if paragraph_hl is None:
				# If both heading hierarchy level are None raise correspondent error
				raise UndefinedStyleFoundError(f"Undefined style found: {docx_paragraph.style.name}"
				                               f"\n(text)\n\t{repr(docx_paragraph.text)}")
			else:
				return "paragraph", 0
		else:
			if paragraph_hl is None:
				return "heading", 0
			else:
				logging.warning(f"\tUndefined directed element type conflict for: {docx_paragraph.style.name}"
				                f"\n\t(text):\n\t\t{repr(docx_paragraph.text)}")
				return self._conflict_undefined_directed_element_type()

	@staticmethod
	def _detect_hierarchy_level(docx_paragraph: docx.text.paragraph.Paragraph, styles_dict: dict) -> int | None:
		"""

		:param docx_paragraph:
		:param styles_dict
		:return hierarchy_level:
		"""

		for hierarchy_level in styles_dict:
			if docx_paragraph.style.name in styles_dict[hierarchy_level]:
				return hierarchy_level

		return None

	@staticmethod
	def _conflict_undefined_directed_element_type():
		"""

		:return directed_element_type, hierarchy_level:
		"""
		# TODO: Implement this function correctly (logic to be discussed)
		# Right now it will always assume that:
		return "paragraph", 0

	def _process_docx_table(self, docx_table: docx.table):
		pass


