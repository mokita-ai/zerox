
import re
from pathlib import Path

HIERARCHY = ['document', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
LEAF_NODES = ['itemize', 'enumerate', 'table', 'tabular']
TEXT_TAGS =  ['textbf', 'textit', 'texttt', 'textsc', 'textsf', 'underline', 'emph', 'thead']
SPANING_CELLS =   ['multirow', 'multicolumn']
TABLE_DRAWING_TAGS = ['hline', 'cline', 'cmidrule', 'toprule', 'midrule', 'bottomrule']



def remove_unnecessary_space_token(text):
    # Join TEXT_TAGS and SPANING_CELLS for regex patterns
    text_tags_pattern = '|'.join(TEXT_TAGS)
    spaning_cells_pattern = '|'.join(SPANING_CELLS)
    
    # Patterns for TEXT_TAGS
    # Pattern 1: \textbf{...} SPACE_TOKEN &
    pattern1 = re.compile(
        rf'(\\(?:{text_tags_pattern})\{{.*?\}})\s*SPACE_TOKEN\s*&'
    )
    replacement1 = r'\1 &'
    text = re.sub(pattern1, replacement1, text)
    
    # # # Pattern 2: \textbf{...} & SPACE_TOKEN \\
    # # pattern2 = re.compile(
    # #     rf'(\\(?:{text_tags_pattern})\{{.*?\}})\s*&\s*SPACE_TOKEN\s*\\'
    # # )
    # replacement2 = r'\1 & \\'
    # text = re.sub(pattern2, replacement2, text)
    
    # Pattern 3: & SPACE_TOKEN \textbf{...}
    pattern3 = re.compile(
        rf'&\s*SPACE_TOKEN\s*(\\(?:{text_tags_pattern})\{{.*?\}})'
    )
    replacement3 = r'& \1'
    text = re.sub(pattern3, replacement3, text)
    
    # Updated patterns for SPANING_CELLS
    # Pattern 4: \multirow{...}{...}{...} SPACE_TOKEN &
    pattern4 = re.compile(
        rf'(\\(?:{spaning_cells_pattern})\{{.*?\}}\{{.*?\}}\{{.*?\}})\s*SPACE_TOKEN\s*&'
    )
    replacement4 = r'\1 &'
    text = re.sub(pattern4, replacement4, text)
    
    # # Pattern 5: \multirow{...}{...}{...} & SPACE_TOKEN \\
    # pattern5 = re.compile(
    #     rf'(\\(?:{spaning_cells_pattern})\{{.*?\}}\{{.*?\}}\{{.*?\}})\s*&\s*SPACE_TOKEN\s*\\'
    # )
    # replacement5 = r'\1 & \\'
    # text = re.sub(pattern5, replacement5, text)
    
    # Pattern 6: & SPACE_TOKEN \multirow{...}{...}{...}
    pattern6 = re.compile(
        rf'&\s*SPACE_TOKEN\s*(\\(?:{spaning_cells_pattern})\{{.*?\}}\{{.*?\}}\{{.*?\}})'
    )
    replacement6 = r'& \1'
    text = re.sub(pattern6, replacement6, text)
    
    return text

def remove_latex_drawing_commands(latex_string):
    latex_drawing_commands = [
        r'\\hline',
        r'\\cline\{[0-9]+-[0-9]+\}',
        r'\\cmidrule\(lr\)\{[0-9]+-[0-9]+\}',
        r'\\toprule',
        r'\\midrule',
        r'\\bottomrule',
    ]

    for command in latex_drawing_commands:
        pattern = re.compile(command)
        latex_string = re.sub(pattern, '', latex_string)
    return latex_string

def replace_special_chars(text):
    # text = re.sub(r'\$', 'DOLLAR', text)
    # text = re.sub(r'\$', 'DOLLAR', text)
    # Replace all occurrences of \$ and $ with DOLLAR_TOKEN

    text = re.sub(r'\\\$', 'DOLLAR_TOKEN', text)
    text = re.sub(r'\$', 'DOLLAR_TOKEN', text)

    text = re.sub(r'\\\%', 'PERCENT', text)
    text = re.sub(r'\%', 'PERCENT', text)





    # text = re.sub(r'\%', 'PERCENT', text)
    # text = re.sub(r'\\&', 'AMPERSAND', text)
    # text = re.sub(r'\&', 'AMPERSAND', text)
    # text = re.sub(r'\#', 'HASH', text)
    # text = re.sub(r'\\#', 'HASH', text)





    return text

def custom_strip(text):
    # Remove trailing spaces
    text = re.sub(r"[ ]+$", "", text)


    # Remove leading spaces and newlines
    text = text.lstrip(" ") 
    text = text.lstrip("\n")

    # Reduce multiple trailing newlines to a single newline
    text = re.sub(r"\n\s*$", "\n", text)

    return text 


def text_end_point(text):
    if not isinstance(text, str):
        if text.name not in TEXT_TAGS or len(text.contents) != 1:
            raise Exception('text_end_point: text is not a string')
        
        text = text.contents[0]

    text = re.sub(r'DOLLAR_TOKEN', '$', text)
    text = re.sub(r'PERCENT', '%', text)
    # text = re.sub(r'AMPERSAND', '&', text)
    # text = re.sub(r'HASH', '#', text)
    text = re.sub(r'SPACE_TOKEN', '', text)   
    ##strip the text
    text = custom_strip(text)


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

def prepare_fs_examples_pathes():
    fs_examples = []
    
    ##list all folders in data/fewshot_examples folder
    fewshot_examples_folder = Path("data/fewshot_examples")

    ##if the path does not exist return empty list
    if not fewshot_examples_folder.exists():
        return fs_examples

    for folder in fewshot_examples_folder.iterdir():
        #assert there is only one .png and one .tex file in the folder
        png_files = list(folder.glob("*.png"))
        tex_files = list(folder.glob("*.tex"))


        assert (len(png_files) == 1 and len(tex_files) == 1)


        fs_examples.append((png_files[0].as_posix(), tex_files[0].as_posix()))
    return fs_examples