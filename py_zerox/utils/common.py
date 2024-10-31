
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



def remove_unnecessary_space_token(text):
    # Step 1: Remove SPACE_TOKEN in "text } SPACE_TOKEN & text"
    pattern1 = r"(\})\s*SPACE_TOKEN\s*&"
    replacement1 = r"\1 &"
    text = re.sub(pattern1, replacement1, text)

    # Step 2: Remove SPACE_TOKEN in "text & SPACE_TOKEN \ text"
    pattern2 = r"(&)\s*SPACE_TOKEN\s*\\"
    replacement2 = r"\1 \\"
    text = re.sub(pattern2, replacement2, text)

    return text