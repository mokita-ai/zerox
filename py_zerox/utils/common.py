
import re

HIERARCHY = ['document', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
LEAF_NODES = ['itemize', 'table' , 'enumerate']
MAX_TEXT_LENGTH = 1500000


def remove_unnecessary_space_token(text):
    # Step 1: Remove SPACE_TOKEN in "text } SPACE_TOKEN & text"
    pattern1 = r"(\})\s*SPACE_TOKEN\s*&"
    replacement1 = r"\1 &"
    text = re.sub(pattern1, replacement1, text)

    # Step 2: Remove SPACE_TOKEN in "text & SPACE_TOKEN \ text" only if not followed by another \
    pattern2 = r"(&)\s*SPACE_TOKEN\s*\\(?!\\)"
    replacement2 = r"\1 \\"
    text = re.sub(pattern2, replacement2, text)

    return text


def replace_special_chars(text):
    text = re.sub(r'\\$', 'DOLLAR', text)
    text = re.sub(r'\$', 'DOLLAR', text)
    text = re.sub(r'\\%', 'PERCENT', text)
    text = re.sub(r'\%', 'PERCENT', text)
    text = re.sub(r'\\&', 'AMPERSAND', text)
    text = re.sub(r'\&', 'AMPERSAND', text)
    text = re.sub(r'\\#', 'HASH', text)
    text = re.sub(r'\#', 'HASH', text)





    return text

def restore_special_chars(text):
    text = re.sub(r'DOLLAR', '$', text)
    text = re.sub(r'PERCENT', '%', text)
    text = re.sub(r'AMPERSAND', '&', text)
    text = re.sub(r'HASH', '#', text)
    text = re.sub(r'SPACE_TOKEN', '', text)   
    return text


def make_sure_one_document(text):
    text = re.sub(r'\\begin{document}', '', text)
    text = re.sub(r'\\end{document}', '', text)
    text = re.sub(r'\\usepackage{.*}', '', text)
    text = re.sub(r'\\documentclass{.*}', '', text)
    text = re.sub(r'\\title{.*}', '', text)
    text = re.sub(r'\\author{.*}', '', text)
    text = re.sub(r'\\date{.*}', '', text)
    text = re.sub(r'\\pagestyle{.*}', '', text)
    text = re.sub(r'\\bibliographystyle{.*}', '', text)
    

    

    return '\\begin{document}\n'  + text + '\n\\end{document}'
