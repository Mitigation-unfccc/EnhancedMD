import logging
import re
from typing import List

import docx

from enhanced_md import enhanced_elements


class EnhancedMD:
	def __init__(self, docx_file_path: str, styles: dict):
		"""

		"""
		# TODO: Iterar para per para i construir el nostre propi Para.
		# TODO: Ens interesa molt el tipus de paragraph, i el item, aixi com els fills.

		#
		self.docx_file_path = docx_file_path
		logging.info(f"\t[{self.docx_file_path}]")
		self.docx = docx.Document(docx_file_path)
		self.docx_metadata = self._get_docx_metadata()
		logging.info(
			f"\t(metadata)"
			f"\n\t\t- title: {self.docx_metadata['title']}"
			f"\n\t\t- created: {self.docx_metadata['created_at']} ({self.docx_metadata['created_by']})"
			f"\n\t\t- last modified: {self.docx_metadata['modified_at']} ({self.docx_metadata['modified_by']})"
		)

		#
		self.heading_styles, self.paragraph_styles = self._check_and_unpack_styles(styles=styles)
		logging.info(
			f"\t(styles)"
			f"\n\t\t- heading styles: {self.heading_styles}"
			f"\n\t\t- paragraph styles: {self.paragraph_styles}"
		)

		#
		self.doc_graph = None
		self.build_doc_graph()

		#
		self.doc_flat = None

	def _get_docx_metadata(self):
		"""
		Obtains .docx document metadata dictionary from python-docx CoreProperties object
		:return:
		"""

		return {
			"title": self.docx.core_properties.title,
			"created_at": self.docx.core_properties.created,
			"created_by": self.docx.core_properties.author,
			"modified_at": self.docx.core_properties.modified,
			"modified_by": self.docx.core_properties.last_modified_by
		}

	def _check_and_unpack_styles(self, styles: dict) -> tuple:
		"""

		:param styles:
		:return:
		"""

		# Check heading styles
		try:
			heading_styles = styles["heading"]
			self._check_style_dict(style_dict=heading_styles, element_name="heading")
		except KeyError:
			raise KeyError("styles dictionary missing \'heading\'")

		# Check paragraph styles
		try:
			paragraph_styles = styles["paragraph"]
			self._check_style_dict(style_dict=paragraph_styles, element_name="paragraph")
		except KeyError:
			raise KeyError("styles dictionary missing \'paragraph\'")

		return heading_styles, paragraph_styles

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

	def _process_docx_paragraph(self, docx_paragraph: docx.text.paragraph.Paragraph):
		"""

		:param docx_paragraph:
		:return:
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

		print(paragraph_content)

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
	):
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

	def _process_docx_table(self, docx_table: docx.table):
		pass

	def __str__(self):
		# TODO
		return ""
