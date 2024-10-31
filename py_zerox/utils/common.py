
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
    return text

def restore_special_chars(text):
    for latex_char, token in SPECIAL_CHAR_TOKENS.items():
        text = re.sub(re.escape(token), latex_char, text)
    return text

