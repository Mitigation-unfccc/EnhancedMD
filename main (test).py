from enhanced_md import EnhancedMD
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    styles = {
        "heading": {
            0: ["Normal"],
            1: ["Reg_H__Ch_G", "_ H _Ch_G"],
            2: ["Reg_H_1_G"],
            3: ["Reg_H_2/3_G"]
        },
        "paragraph": {
            0: ["Normal", "Default"],
            1: ["Reg_Single Txt_G", "_ Single Txt_G"],
            2: ["Reg_Single Txt_G2"],
            3: ["Reg_Single Txt_G3"]
        }
    }

    file_path = "cma2021.docx"
    emd = EnhancedMD(docx_file_path=file_path, styles=styles)
