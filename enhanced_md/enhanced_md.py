import logging
import re
from typing import List, Tuple

import docx
from docx.text.paragraph import Paragraph as DocxParagraph

import enhanced_md.enhanced_elements as ee
from enhanced_md.exceptions import UndefinedStyleFoundError


class EnhancedMD:
    def __init__(self, docx_file_path: str, styles: dict):
        """

		"""
        # TODO: Iterar para per para i construir el nostre propi Para.
        # TODO: Ens interessa molt el tipus de paragraph, i el item, aixi com els fills.

        logging.info(f"Processing file: {docx_file_path}")
        self.docx_file_path = docx_file_path
        self.docx = docx.Document(docx_file_path)

        self._get_docx_metadata()
        self.log_docx_metadata()

        self.heading_styles, self.paragraph_styles = self._check_and_unpack_styles(styles=styles)
        self.log_styles_info()

        self.doc_graph = None
        self.doc_flat = None

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

    def log_docx_metadata(self):
        meta = self.docx_metadata

        logging.info(f"Metadata: title: {meta['title']}, created: {meta['created_at']} by {meta['created_by']}, "
                     f"last modified: {meta['modified_at']} by {meta['modified_by']}")

    def log_styles_info(self):
        logging.info(f"Styles: heading styles: {self.heading_styles}, paragraph styles: {self.paragraph_styles}")

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

        # TODO: Check that styles for different elements are not the same (except level 0)

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
        for key in range(max(hierarchy_levels) + 1):
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

    def _process_docx_paragraph(self, docx_paragraph: DocxParagraph) -> ee.Heading | ee.Paragraph:
        """

		:param docx_paragraph:
		:return directed_element:
		"""
        #
        self.paragraphs = []
        paragraph_content = self._process_docx_paragraph_content(docx_paragraph=docx_paragraph)

        #
        directed_element_type, hierarchy_level = self._detect_directed_element_type_and_hierarchy_level(
            docx_paragraph=docx_paragraph
        )

        self.paragraphs.append(paragraph_content)

    def _process_docx_paragraph_content(
            self, docx_paragraph: docx.text.paragraph.Paragraph
    ) -> List[ee.Content | ee.Hyperlink]:
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
    def _process_docx_run(docx_run: docx.text.run.Run) -> List[ee.Content]:
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

    def _process_docx_hyperlink(self, docx_hyperlink: docx.text.hyperlink.Hyperlink) -> ee.Hyperlink:
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
            content=hyperlink_content, address=docx_hyperlink.address, fragment=docx_hyperlink.fragment
        )

    def _concat_run_content_to_content_list(self, content_list: List[ee.Content | ee.Hyperlink],
                                            run_content: List[ee.Content]) -> List[ee.Content | ee.Hyperlink]:
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

    def _detect_directed_element_type_and_hierarchy_level(self, docx_paragraph: DocxParagraph) -> Tuple[str, int]:
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

    def __repr__(self):
        # TODO
        return print(self.doc_graph)

    def __call__(self, *args, **kwargs):
        self.build_doc_graph()
