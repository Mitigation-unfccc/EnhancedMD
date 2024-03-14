import logging
import re

import docx
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.text.run import Run as DocxRun
from docx.text.hyperlink import Hyperlink as DocxHyperlink
from docx.table import Table as DocxTable

import networkx as nx
import matplotlib.pyplot as plt

import enhanced_md.enhanced_elements as ee
from enhanced_md.exceptions import UndefinedStyleFoundError, EmptyDocxDocument


class EnhancedMD:

	def __init__(self, docx_file_path: str, styles: dict):
		"""

		"""

		# Docx data
		self.docx_file_path = docx_file_path
		logging.info(f"\t[{self.docx_file_path}]")
		self.docx = docx.Document(docx_file_path)
		self._get_docx_metadata()
		self._log_docx_metadata()

		# Styles data
		self._check_and_unpack_styles(styles=styles)
		self._log_styles()

		# Doc data
		self.doc_graph = None
		self.aux_doc_graph = None
		self.aux_doc_graph_index = 0
		self.doc_flat = None

		self.repr_array = None
		self.is_built = False

	def __call__(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		"""

		self.build_doc_graph()
		self.build_doc_flat()
		self.build_repr()

	def __repr__(self):
		if self.repr_array is None:
			raise RuntimeError("Graph and flat document has not been built, invoke .__call__() first")

		return f"~{repr(self.docx_metadata['title'])}\n"+"\n".join(map(str, self.repr_array))

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
		Checks the style dictionary correctness
		and unpacks into separated style dictionaries for each type of directed element
		:param styles: Input style dictionary
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
		Checks the correctness of the directed element specific style dictionary:
		- Integers keys representing the hierarchy level (including 0 which represents undefined)
		- The hierarchy levels cannot be empty except the undefined one
		:param style_dict: Directed element specific style dictionary
		"""

		hierarchy_levels = style_dict.keys()

		# Check style dictionary hierarchy levels consist only of integers
		if not all(isinstance(key, int) for key in hierarchy_levels):
			raise KeyError(f"{element_name} style dictionary hierarchy levels keys must consist only of integers")

		# Check style dictionary hierarchy levels range from 0 to the maximum level without any gaps
		# and that no hierarchy level is empty except for hierarchy level 0
		for key in range(max(hierarchy_levels) + 1):
			try:
				# Checks first for KeyError and only can raise ValueError for hierarchy levels higher than 0
				if not style_dict[key] and key:
					raise ValueError(f"{element_name} style dictionary, {key} hierarchy level cannot be empty")
				if any([type(style) is not str for style in style_dict[key]]):
					raise ValueError(f"{element_name} style dictionary, {key} hierarchy level "
					                 f"must be an array containing strings")
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
		Iterates over the docx document processing the contents into the enhanced_elements defined classes,
		once the whole document has been processed, recursively builds the doc graph structure
		"""

		# Process the docx document
		self.aux_doc_graph = []
		self._process_docx_document()

		# Build the doc graph structure
		self.doc_graph = []
		self._build_doc_graph()

	def _process_docx_document(self):
		"""
		Iterates over the docx document processing the contents into the enhanced_elements defined classes,
		storing the processed contents into the auxiliary doc graph structure
		"""

		for docx_content in self.docx.iter_inner_content():
			# Detect whether document content is paragraph or table and process accordingly
			if isinstance(docx_content, DocxParagraph):
				# Only process paragraphs which are not empty or only consist of space, tabular or newline characters
				if len(docx_content.text) and not all(c in " \t\n" for c in docx_content.text):
					self._process_docx_paragraph(docx_paragraph=docx_content)

			if isinstance(docx_content, DocxTable):
				# Only process tables which are not empty
				if len(docx_content.rows) and len(docx_content.columns):
					self._process_docx_table(docx_table=docx_content)

	def _process_docx_paragraph(self, docx_paragraph: DocxParagraph):
		"""
		Process a docx paragraph into the enhanced_elements Heading or Paragraph structure,
		appending them into the auxiliary doc graph structure
		:param docx_paragraph: Docx paragraph class
		"""

		# Process paragraph content
		paragraph_content = self._process_docx_paragraph_content(docx_paragraph=docx_paragraph)

		# Detect whether the docx paragraph is a Heading or Paragraph based on the style name and the hierarchy level
		directed_element_type, hierarchy_level = self._detect_directed_element_type_and_hierarchy_level(
			docx_paragraph=docx_paragraph
		)

		# Build into the corresponding directed element structure
		if directed_element_type == "heading":
			self.aux_doc_graph.append(ee.Heading(
				content=paragraph_content, docx_element=docx_paragraph,
				style=docx_paragraph.style.name, hierarchy_level=hierarchy_level
			))
		else:
			# directed_element_type == "paragraph":
			self.aux_doc_graph.append(ee.Paragraph(
				content=paragraph_content, docx_element=docx_paragraph,
				style=docx_paragraph.style.name, hierarchy_level=hierarchy_level
			))

	def _process_docx_paragraph_content(self, docx_paragraph: DocxParagraph) -> list[ee.Content | ee.Hyperlink]:
		"""

		:param docx_paragraph: Docx paragraph class
		:return paragraph_content:
		"""

		paragraph_content = []
		for docx_paragraph_content in docx_paragraph.iter_inner_content():
			# Only process paragraph contents which are not empty
			if len(docx_paragraph_content.text):
				# Detect whether paragraph content is run or hyperlink and process accordingly
				if isinstance(docx_paragraph_content, DocxRun):
					run_content = self._process_docx_run(docx_run=docx_paragraph_content)

					# Apply (if needed) special paragraph_content concat
					paragraph_content = self._concat_run_content_to_content_list(
						content_list=paragraph_content, run_content=run_content
					)

				elif isinstance(docx_paragraph_content, DocxHyperlink):
					paragraph_content.append(self._process_docx_hyperlink(docx_hyperlink=docx_paragraph_content))

		return paragraph_content

	@staticmethod
	def _process_docx_run(docx_run: DocxRun) -> list[ee.Content]:
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
				ee.Content(
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

	def _process_docx_hyperlink(self, docx_hyperlink: DocxHyperlink) -> ee.Hyperlink:
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

		return ee.Hyperlink(
			content=hyperlink_content, docx_element=docx_hyperlink,
			address=docx_hyperlink.address, fragment=docx_hyperlink.fragment
		)

	def _concat_run_content_to_content_list(self, content_list: list[ee.Content | ee.Hyperlink],
	                                        run_content: list[ee.Content]) -> list[ee.Content | ee.Hyperlink]:
		"""

		:param content_list:
		:param run_content:
		:return content_list:
		"""

		# Only if content_list is not empty and previous content is content class
		if len(content_list) and isinstance(content_list[-1], ee.Content):
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
	def _detect_special_content_concat(content_a: ee.Content, content_b: ee.Content) -> bool:
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

	def _detect_directed_element_type_and_hierarchy_level(self, docx_paragraph: DocxParagraph) -> tuple[str, int]:
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
				return "paragraph", 1
		else:
			if paragraph_hl is None:
				return "heading", 1
			else:
				# If both heading hierarchy level are 0 print correspondent warning and solve conflict
				logging.info(f"\tUndefined directed element type conflict for: {docx_paragraph.style.name}"
				                f"\n\t(text):\n\t\t{repr(docx_paragraph.text)}")
				return self._conflict_undefined_directed_element_type()

	@staticmethod
	def _detect_hierarchy_level(docx_paragraph: DocxParagraph, styles_dict: dict) -> int | None:
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
		return "paragraph", 1

	def _process_docx_table(self, docx_table: docx.table):
		pass

	def _build_doc_graph(self):
		"""
		Recursively build the doc graph structure by iterating over the processed docx document contents,
		storing the subtrees into the doc graph structure
		"""

		if len(self.aux_doc_graph) > 0:  # Check the document is not empty
			first_directed_element = self._get_aux_doc_graph_element_and_increment()

			# Avoid starting with directed element with undefined hierarchy level
			while first_directed_element.hierarchy_level == 0:  # will have to delete this later
				first_directed_element = self._get_aux_doc_graph_element_and_increment()

			first_directed_element.item = [0]
			if first_directed_element.has_num_id:
				first_directed_element.num_id = 1

			self._build_doc_subgraph(curr_directed_element=first_directed_element)
		else:
			raise EmptyDocxDocument(f"{self.docx_file_path} is an empty document")

	def _build_doc_subgraph(self, curr_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:return need_backtrack:
		"""

		# If no parent has been assigned to the current directed element, means that it is child of doc graph root
		if curr_directed_element.parent is None:
			self.doc_graph.append(curr_directed_element)

		# End of graph condition
		if self.aux_doc_graph_index == len(self.aux_doc_graph):
			return False

		next_directed_element = self._get_aux_doc_graph_element_and_increment()

		# Forward recursive graph exploration
		need_backtrack = self._build_doc_subgraph_forward(
			curr_directed_element=curr_directed_element, next_directed_element=next_directed_element
		)

		# Backtracking
		if need_backtrack:
			return self._build_doc_sub_graph_backtrack(curr_directed_element=curr_directed_element)
		else:
			return False

	def _build_doc_subgraph_forward(self, curr_directed_element: ee.DirectedElement,
	                                next_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:param next_directed_element:
		:return need_backtrack:
		"""

		# Skip directed elements with undefined hierarchy level (at least for now)
		if next_directed_element.hierarchy_level == 0:
			return self._build_doc_subgraph(curr_directed_element=curr_directed_element)
		else:
			curr_directed_element.add_next(next_directed_element)

			if isinstance(curr_directed_element, ee.Heading) and (not isinstance(next_directed_element, ee.Heading)):
				return self._build_doc_subgraph_forward_heading_and_non_heading_type(
					curr_directed_element=curr_directed_element, next_directed_element=next_directed_element
				)
			elif (not isinstance(curr_directed_element, ee.Heading)) and isinstance(next_directed_element, ee.Heading):
				return self._build_doc_subgraph_backtrack_and_root_edge_case(
					curr_directed_element=curr_directed_element, other_directed_element=next_directed_element
				)
			else:
				return self._build_doc_subgraph_forward_same_directed_element_type(
					curr_directed_element=curr_directed_element, next_directed_element=next_directed_element
				)

	def _build_doc_subgraph_forward_heading_and_non_heading_type(self, curr_directed_element: ee.Heading,
	                                                             next_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:param next_directed_element:
		:return need_backtrack:
		"""

		# Set non heading directed element heading item
		next_directed_element.heading_item = curr_directed_element.item

		# Add as heading child
		curr_directed_element.add_child(next_directed_element)
		# Reset non heading directed element item and num id
		next_directed_element.item = [0]
		self._reset_num_id(directed_element=next_directed_element)

		# Continue recursive doc graph exploration
		return self._build_doc_subgraph(curr_directed_element=next_directed_element)

	def _build_doc_subgraph_forward_same_directed_element_type(self, curr_directed_element: ee.DirectedElement,
	                                                   next_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:return need_backtrack:
		"""

		# If next directed element has higher hierarchy level, backtrack
		if curr_directed_element.hierarchy_level > next_directed_element.hierarchy_level:
			return True
		else:
			# Depending on difference of hierarchy levels add as child or next
			if curr_directed_element.hierarchy_level < next_directed_element.hierarchy_level:
				curr_directed_element.add_child(next_directed_element)
				next_directed_element.item = self._get_item_child_hierarchy_level(prev_item=curr_directed_element.item)
				# Reset num id
				if next_directed_element.has_num_id:
					next_directed_element.num_id = 1

			elif curr_directed_element.hierarchy_level == next_directed_element.hierarchy_level:

				if curr_directed_element.parent is not None:
					curr_directed_element.parent.add_child(next_directed_element)

				next_directed_element.item = self._get_item_same_hierarchy_level(prev_item=curr_directed_element.item)
				self._set_num_id(directed_element=next_directed_element, other_directed_element=curr_directed_element)

			# Continue recursive graph exploration
			return self._build_doc_subgraph(curr_directed_element=next_directed_element)

	def _build_doc_sub_graph_backtrack(self, curr_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:return need_backtrack:
		"""

		back_directed_element = self.aux_doc_graph[self.aux_doc_graph_index - 1]

		if isinstance(curr_directed_element, ee.Heading) and (not isinstance(back_directed_element, ee.Heading)):
			return self._build_doc_subgraph_backtrack_heading_and_non_heading_type(
				curr_directed_element=curr_directed_element, back_directed_element=back_directed_element
			)
		elif (not isinstance(curr_directed_element, ee.Heading)) and isinstance(back_directed_element, ee.Heading):
			return self._build_doc_subgraph_backtrack_and_root_edge_case(
				curr_directed_element=curr_directed_element, other_directed_element=back_directed_element
			)
		else:
			return self._build_doc_subgraph_backtrack_same_directed_element_type(
				curr_directed_element=curr_directed_element, back_directed_element=back_directed_element
			)

	def _build_doc_subgraph_backtrack_heading_and_non_heading_type(self, curr_directed_element: ee.Heading,
	                                                               back_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:param back_directed_element:
		:return:
		"""

		if curr_directed_element.parent is not None:
			curr_directed_element.parent.add_child(back_directed_element)

		back_directed_element.item = self._get_item_same_hierarchy_level(prev_item=curr_directed_element.item)
		self._set_num_id(directed_element=back_directed_element, other_directed_element=curr_directed_element)

		# Continue recursive doc graph exploration
		return self._build_doc_subgraph(curr_directed_element=back_directed_element)

	def _build_doc_subgraph_backtrack_same_directed_element_type(self, curr_directed_element: ee.DirectedElement,
	                                                             back_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:param back_directed_element:
		:return:
		"""

		# If next directed element has higher hierarchy level, continue backtracking
		if curr_directed_element.hierarchy_level > back_directed_element.hierarchy_level:
			return self._build_doc_subgraph_backtrack_and_root_edge_case(
				curr_directed_element=curr_directed_element, other_directed_element=back_directed_element
			)
		else:
			if curr_directed_element.parent is not None:
				curr_directed_element.parent.add_child(back_directed_element)

			back_directed_element.item = self._get_item_same_hierarchy_level(prev_item=curr_directed_element.item)
			self._set_num_id(directed_element=back_directed_element, other_directed_element=curr_directed_element)

			# Continue recursive doc graph exploration
			return self._build_doc_subgraph(curr_directed_element=back_directed_element)

	def _build_doc_subgraph_backtrack_and_root_edge_case(self, curr_directed_element: ee.DirectedElement,
	                                                     other_directed_element: ee.DirectedElement) -> bool:
		"""

		:param curr_directed_element:
		:param other_directed_element:
		:return need_backtrack:
		"""

		if curr_directed_element.parent is not None:  # Continue backtracking
			return True
		else:
			last_root_directed_element = self.doc_graph[-1]  # Previous directed element from the doc graph root

			# Append other directed element to doc graph root
			# (will actually be appended in next _build_doc_subgraph call)
			other_directed_element.item = self._get_item_same_hierarchy_level(prev_item=last_root_directed_element.item)
			self._set_num_id(directed_element=other_directed_element, other_directed_element=last_root_directed_element)

			# Continue recursive doc graph exploration from the root
			return self._build_doc_subgraph(curr_directed_element=other_directed_element)

	def _get_aux_doc_graph_element_and_increment(self) -> ee.DirectedElement:
		"""

		:return aux_doc_graph_element:
		"""

		aux_doc_graph_element = self.aux_doc_graph[self.aux_doc_graph_index]
		self.aux_doc_graph_index += 1

		return aux_doc_graph_element

	@staticmethod
	def _get_item_same_hierarchy_level(prev_item: list[int]) -> list[int]:
		"""

		:param prev_item:
		:return new_item:
		"""

		return prev_item[:-1] + [prev_item[-1] + 1]

	@staticmethod
	def _get_item_child_hierarchy_level(prev_item: list[int]) -> list[int]:
		"""

		:param prev_item:
		:return new_item:
		"""

		return prev_item.copy() + [0]  # Make a copy to avoid pass by reference errors

	@staticmethod
	def _reset_num_id(directed_element: ee.DirectedElement):
		"""

		:param directed_element:
		"""

		if directed_element.has_num_id:
			directed_element.num_id = 1

	@staticmethod
	def _set_num_id(directed_element: ee.DirectedElement, other_directed_element: ee.DirectedElement):
		"""

		:param directed_element:
		:param other_directed_element:
		"""

		if directed_element.has_num_id:
			directed_element.num_id = (1 if not other_directed_element.has_num_id
			                           else other_directed_element.num_id + 1)

	def build_doc_flat(self):
		"""

		"""

		self.doc_flat = []
		self._build_doc_flat(curr_directed_element=self.doc_graph[0])

	def _build_doc_flat(self, curr_directed_element: ee.DirectedElement):
		"""

		:param curr_directed_element:
		"""

		self.doc_flat.append(curr_directed_element)
		if curr_directed_element.next is not None:
			self._build_doc_flat(curr_directed_element=curr_directed_element.next)

	def build_repr(self):
		"""

		"""

		directed_element_types_dict = {
			"Heading": "H",
			"Paragraph": "P"
		}

		self.repr_array = []
		for directed_element in self.doc_flat:

			directed_element_type = directed_element_types_dict[type(directed_element).__name__]
			heading_item_len = (0 if isinstance(directed_element, ee.Heading) or directed_element.heading_item is None
			                    else len(directed_element.heading_item))
			space = "·"*5*(len(directed_element.item) + heading_item_len - 1)
			marker = "" if heading_item_len == 0 and len(directed_element.item) == 1 else "+----"
			numbering = "" if directed_element.num_id is None else f"({directed_element.num_id})"
			self.repr_array.append(f"{directed_element_type}|{space}{marker}"
			                       f"{directed_element.item}${directed_element.style}$"
			                       f"{numbering}->{repr(directed_element.text)}")

	def visualize_doc_graph(self):
		"""

		"""

		G = nx.DiGraph()

		i = 0
		for node in self.doc_graph:
			i = self._visualization_add_nodes_and_edges(G, node, i)

		plt.figure(figsize=(10, 8))
		nx.draw(
			G,
			node_size=250, node_color=[G.nodes[node]['color'] for node in G.nodes()],
			pos=nx.get_node_attributes(G, "pos"),
			edge_color=[G[u][v]["color"] for u, v in G.edges()], arrows=True,
			with_labels=True , font_size=7,
		)
		plt.show()

	def _visualization_add_nodes_and_edges(self, G, node, i):
		i += 1
		node_x_position = (0 if isinstance(node, ee.Heading) else len(self.heading_styles.keys())-1) + len(node.item)
		node_color = (0 if isinstance(node, ee.Heading) else 2)
		node_color = (node_color+1 if node.has_num_id else node_color)
		color_map = {0: "skyblue", 1: "blue", 2: "lightgray", 3: "gray"}
		node_color = color_map[node_color]
		G.add_node(
			node.construct_identifier_string(), pos=(node_x_position, len(self.aux_doc_graph) - i), color=node_color
		)
		if node.parent is not None:
			G.add_edge(node.parent.construct_identifier_string(),
			           node.construct_identifier_string(), color="black")
		if node.next is not None:
			G.add_edge(node.construct_identifier_string(),
			           node.next.construct_identifier_string(), color="b")
		if node.children is not None:
			for child in node.children:
				i = self._visualization_add_nodes_and_edges(G, child, i)
		return i

	def conditional_num_id_reindex_on_heading_regex(self, conditional_heading_regex: list):
		"""

		:param conditional_heading_regex:
		"""

		# TODO: Generalize the concept

		reset_num_id = False
		incr_num_id = 1
		for directed_element in self.doc_flat:
			if isinstance(directed_element, ee.Heading):
				for pattern in conditional_heading_regex:
					if re.search(pattern, directed_element.text):
						reset_num_id = True

			elif (isinstance(directed_element, ee.Paragraph)
			      and len(directed_element.item) == 1 and directed_element.has_num_id):
				if reset_num_id:
					incr_num_id = 1
					reset_num_id = False

				directed_element.num_id = incr_num_id
				incr_num_id += 1
 