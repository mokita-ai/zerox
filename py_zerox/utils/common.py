
import re

HIERARCHY = ['document', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
LEAF_NODES = ['itemize', 'table' , 'enumerate']
MAX_TEXT_LENGTH = 1500000

SPECIAL_CHAR_TOKENS = {
    r'\$': 'DOLLAR',
    r'\%': 'PERCENT',
    r'\&': 'AMPERSAND',
    r'\#': 'HASH',
}

def replace_special_chars(text):
    for latex_char, token in SPECIAL_CHAR_TOKENS.items():
        text = re.sub(re.escape(latex_char), token, text)

    
    
    ##todo
    text = re.sub(r'$', 'DOLLAR', text)
    text = re.sub(r'%', 'PERCENT', text)


    return text

def restore_special_chars(text):
    for latex_char, token in SPECIAL_CHAR_TOKENS.items():
        text = re.sub(re.escape(token), latex_char, text)
    return text


def make_sure_one_document(text):
    text = re.sub(r'\\begin{document}', '', text)
    text = re.sub(r'\\end{document}', '', text)

    return '\\begin{document}\n'  + text + '\n\\end{document}'
