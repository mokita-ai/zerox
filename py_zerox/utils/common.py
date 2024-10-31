
import re

HIERARCHY = ['document', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
LEAF_NODES = ['itemize', 'table' , 'enumerate']
MAX_TEXT_LENGTH = 15

SPECIAL_CHAR_TOKENS = {
    r'\$': 'DOLLAR_TOKEN',
    r'\%': 'PERCENT_TOKEN',
    r'\&': 'AMPERSAND_TOKEN',
    r'\#': 'HASH_TOKEN',
}

def replace_special_chars(text):
    for latex_char, token in SPECIAL_CHAR_TOKENS.items():
        text = re.sub(re.escape(latex_char), token, text)
    return text

def restore_special_chars(text):
    for latex_char, token in SPECIAL_CHAR_TOKENS.items():
        plain_char = latex_char[1:] if latex_char.startswith(r'\\') else latex_char.replace('\\', '')
        text = re.sub(re.escape(token), plain_char, text)
        text =  re.sub(re.escape("SPACE_TOKEN"), "", text)
    return text

