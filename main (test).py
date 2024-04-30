import logging
import re

from enhanced_md import EnhancedMD
import enhanced_md.enhanced_elements as ee

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    codoc_styles = {
        "heading": {
            0: ["Normal"],
            1: ["_ H _Ch_G"],
            2: ["Reg_H__Ch_G"],
            3: ["Reg_H_1_G", "_ H_1_G"],
            4: ["Reg_H_2/3_G"],
            5: ["Reg_H_4_G"],
            6: ["Reg_H_5_G"]
        },
        "paragraph": {
            0: ["Normal", "Default"],
            1: ["Reg_Single Txt_G", "_ Single Txt_G", "Anno_ Single Txt_G"],
            2: ["Reg_Single Txt_G2"],
            3: ["Reg_Single Txt_G3"],
            4: ["List Paragraph", "toc 1", "FC1"],
            5: ["toc 2", "Footnote Table"]
        }
    }

    styles = {
        "heading": {
            0: [],
            1: ["SDMTitle1", "SDMTOCHeading"],
            2: ["SDMTitle2", "SDMDocInfoTitle"],
            3: ["MRHead1"],
            4: ["MRHead2", "Caption"]
        },
        "paragraph": {
            0: ["Normal"],
            1: ["SDMTiInfo", "SDMPara", "MRAnnexNumbering"],
            2: ["SDMSubPara1", "toc 1"],
            3: ["SDMSubPara2", "toc 2", "SDMTableBoxFigureFootnote"]
        }
    }

    file_path = "cp2022_10a03.docx"
    emd = EnhancedMD(docx_file_path=file_path, styles=codoc_styles)
    emd()
    print(emd)