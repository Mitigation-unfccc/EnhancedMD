from enhanced_md import EnhancedMD
import logging
import enhanced_md.enhanced_elements as ee

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    styles = {
        "heading": {
            0: ["Normal"],
            1: ["_ H _Ch_G"],
            2: ["Reg_H__Ch_G"],
            3: ["Reg_H_1_G", "_ H_1_G"],
            4: ["Reg_H_2/3_G"]
        },
        "paragraph": {
            0: ["Normal", "Default"],
            1: ["Reg_Single Txt_G", "_ Single Txt_G", "Anno_ Single Txt_G"],
            2: ["Reg_Single Txt_G2"],
            3: ["Reg_Single Txt_G3"],
            4: ["List Paragraph", "toc 1"]
        }
    }

    file_path = "cmp2022_09_a01.docx"
    emd = EnhancedMD(docx_file_path=file_path, styles=styles)
    emd()
    emd.visualize_doc_graph()