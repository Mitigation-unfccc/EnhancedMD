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
            1: ["Reg_Single Txt_G", "_ Single Txt_G"],
            2: ["Reg_Single Txt_G2"],
            3: ["Reg_Single Txt_G3"],
            4: ["List Paragraph"]
        }
    }

    file_path = "cma2021.docx"
    emd = EnhancedMD(docx_file_path=file_path, styles=styles)
    emd()
    emd.visualize_doc_graph()

    def explore_num_id(x):
        if isinstance(x, ee.Heading):
            print(x.num_id, "@", x.item, "@", x.style, "@", repr(x.text))
        if x.next is not None:
            explore_num_id(x.next)

    explore_num_id(emd.doc_graph[0])