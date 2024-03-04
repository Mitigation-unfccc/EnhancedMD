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

		paragraph = []
		#
		for docx_paragraph_content in docx_paragraph.iter_inner_content():
			# Only process paragraph contents which are not empty
			if len(docx_paragraph_content.text):
				# Detect whether paragraph content is run or hyperlink and process accordingly
				if isinstance(docx_paragraph_content, docx.text.run.Run):
					run = self._process_docx_run(docx_run=docx_paragraph_content)

				elif isinstance(docx_paragraph_content, docx.text.hyperlink.Hyperlink):
					print(repr(docx_paragraph_content.text))

	def _process_docx_run(self, docx_run: docx.text.run.Run) -> List[enhanced_elements.Content]:
		"""

		:param docx_run:
		:return processed_run:
		"""

		# Split run text by spaces, sequences of word characters, and individual punctuation characters
		pattern = r'(\s|[\w]+|\W)'
		content_split = re.findall(pattern, docx_run.text)

		processed_run = []
		#
		for content in content_split:
			processed_run.append(
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

		return processed_run

	def _process_docx_table(self, docx_table: docx.table):
		pass

	def __str__(self):
		# TODO
		return ""
