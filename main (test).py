import logging
import re

from enhanced_md import EnhancedMD
import enhanced_md.enhanced_elements as ee

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)

	codoc_styles = {
		"heading": {
			0: ["Normal"],
			1: ["_ H _Ch_G", "MainTitle"],
			2: ["Reg_H__Ch_G", "Anno _ H_CH_G"],
			3: ["Reg_H_1_G", "_ H_1_G"],
			4: ["Reg_H_2/3_G"],
			5: ["Reg_H_4_G"],
			6: ["Reg_H_5_G"]
		},
		"paragraph": {
			0: ["Normal", "Default"],
			1: ["Reg_Single Txt_G", "_ Single Txt_G", "Anno_ Single Txt_G", "Style Reg_Single Txt_G + Italic"],
			2: ["Reg_Single Txt_G2"],
			3: ["Reg_Single Txt_G3"],
			4: ["List Paragraph", "toc 1", "endnote text"]
		}
	}

	styles = {
		"heading": {
			0: [],
			1: ["SDMTitle1", "SDMTOCHeading"],
			2: ["SDMTitle2", "SDMDocInfoTitle"],
			3: ["MRHead1", "MRAnnTitle"],
			4: ["MRHead2", "Caption"]
		},
		"paragraph": {
			0: ["Normal"],
			1: ["SDMTiInfo", "SDMPara", "MRAnnexNumbering"],
			2: ["SDMSubPara1", "toc 1"],
			3: ["SDMSubPara2", "toc 2", "SDMTableBoxFigureFootnote"]
		}
	}

	S_EB_SB = {
		"heading": {
			0: ["Normal"],
			1: ["_ H _Ch_G", "Heading 1", "SDMTitle1", "MRAnnTitle", "PAAnnTitle"],
			2: ["Reg_H__Ch_G", "Heading 2", "SDMTitle2", "SDMDocInfoTitle", "PAHead1"],
			3: ["Reg_H_1_G", "_ H_1_G", "MRHead1", "PAHead2", "ProposedAgendaHeading"],
			4: ["Reg_H_2/3_G", "MRHead2"]
		},
		"paragraph": {
			0: ["Normal", "Default"],
			1: ["Reg_Single Txt_G", "_ Single Txt_G",
				"Anno_ Single Txt_G", "RegPara", "SDMTiInfo", "SDMPara", "MRAnnexNumbering", "PAAnnexNumbering"],
			2: ["Reg_Single Txt_G2", "List2", "SDMSubPara1"],
			3: ["Reg_Single Txt_G3"],
			4: ["List Paragraph", "SDMSubPara2", "SDMTableBoxFigureFootnote", "Footnote Table",
				"FC1", "Reg_H_5_G", "Reg_H_4_G", "Caption", "No Spacing"]
		},
		"ignore": ["SDMTOCHeading", "toc 1", "toc 2"]
	}

	STYLES = {
		"heading": {
			0: ["Normal"],  # keep as-is, per instructions
			1: ["Title", "MainTitle", "MRAnnTitle", "PAAnnTitle", "SDMDocInfoTitle"], # 1: Document-Level Titles
			2: ["Heading 1", "SDMHead1", "SDMTitle1", "SDMTOCHeading", "_ H _Ch_G"], # 2: Heading 1 Equivalents
			3: ["Heading 2", "Reg_H__Ch_G", "SDMTitle2", "PAHead1", "SDMHead2", "MainSubTitle"], # 3: Heading 2 Equivalents
			4: ["Heading 3", "Reg_H_1_G", "_ H_1_G", "MRHead1", "PAHead2", "ProposedAgendaHeading", "SDMHead3"], # 4: Heading 3 Equivalents
			5: ["Heading 4", "Reg_H_2/3_G", "MRHead2", "_ H_2/3_G", "SDMHead4"], # 5: Heading 4 Equivalents
			6: ["Caption", "SDMDocRef", "FC2", "endnote text", "Anno _ H_CH_G"] # 6: Captions / Misc. / Specialized
		},
		"paragraph": {
			0: ["Normal", "Default"],
			1: ["Reg_Single Txt_G", "_ Single Txt_G", "Anno_ Single Txt_G", "RegPara", "SDMTiInfo", "SDMPara", "MRAnnexNumbering", "PAAnnexNumbering", "Body Text", "SDMAppTitle", "SDMCovNoteHead1", "CaptionFullPage"],
			2: ["Reg_Single Txt_G2", "List2", "SDMSubPara1"],
			3: ["Reg_Single Txt_G3", "1 paragraph", "Corps A", "Anno_ H_1_G", "CaptionLandscape", "SDMSubPara2"],
			4: ["List Paragraph", "toc 1", "SDMSubPara3", "toc 2", "SDMTableBoxFigureFootnote", "Footnote Table", "FC1", "Reg_H_5_G", "Reg_H_4_G", "Anno_ H_2/3_G", "Style Reg_Single Txt_G + Italic", "footnote text", "No Spacing", "toc 3", "toc 6", "_ H_4_G", "Corner notation", "SDMApp1", "SDMSubPara4"]
		},
		"ignore": []
	}
	file_path = "A6.4-PROC-METH-001.docx"
	emd = EnhancedMD(docx_file_path=file_path, styles=STYLES)
	emd()
	print(emd)