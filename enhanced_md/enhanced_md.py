from abc import ABC
from typing import List

import docx


class EnhancedMD:
    def __init__(self, doc_path: str, styles: dict):
        """

        :param doc_path: Path to word document
        :param styles: a dictionary with the configuration of the styles
        """
        # TODO: Iterar para per para i construir el nostre propi Para.
        # TODO: Ens interesa molt el tipus de paragraph, i el item, aixi com els fills.
        self.doc_path = doc_path
        self.doc = docx.Document(doc_path)
        self.styles = self._check_style(styles)

    def _check_style(self, style: dict) -> dict:
        """
        Check that the styles dict is correct
        :param style:
        :return:
        """
        pass


class BaseElement(ABC):
    def __init__(self):
        self.text = None


class Heading(BaseElement):
    def __init__(self):
        super().__init__()
        self.elements = []  # git pullList of elements that are inside the heading


class Paragraph(BaseElement):
    def __init__(self, text: str, parent=None, children=None, para_type=None, item=None):
        super().__init__()
        self.text = text

        # For lists and sublist
        self.parent: Paragraph = parent
        self.children: List[Paragraph] = children
        self.type = para_type  # Heading, Paragraph
        self.heading_level = None  # If it is a heading, this is the level
        self.item = item  # If it is a list, this is the item. e.g. 1, 2, 3, a, b, c
