

from TexSoup import TexSoup as TS
from utils.common import *

def table_signiture(soup):
    tabular_index = -1 ## the index of the tag tabular
    content_count = len(soup.contents)

    for i in range(content_count):
        if not isinstance(soup.contents[i], str) and soup.contents[i].name == 'tabular':
            tabular_index = i
            break

    if tabular_index == -1:
        raise Exception("not a valid table")
    
    tabular_text = str(soup.contents[tabular_index])

    tabular_text =  re.sub(re.escape("&"), "SPACE_TOKEN&SPACE_TOKEN", tabular_text)
    tabular_text = remove_unnecessary_space_token(tabular_text)


    # ##save tex_data and latex .tex in a file
    # with open("testing/o.tex", 'w') as f:
    #     f.write(tabular_text)




    soup = TS(tabular_text)

    cells = []
    

    column_string = soup.contents[0].contents[0] ## for example "|c|c|c|" or "ccc"
    stripped_string = column_string.replace('|', '').replace(' ', '')

    # Count the remaining characters
    n_columns = len(stripped_string)

    i, j =  0, 0
    vis = {}
    for element in soup.contents[0].contents:
        span = None

        if not isinstance(element, str) and  isinstance(element.contents, list) and len(element.contents):
            if element.name in ['multirow', 'multicolumn']:
                span = element.name, int(element.contents[0])
                if(len(element.contents) < 3):
                    element = ""
                else:
                    element = element.contents[2]

                if not isinstance(element, str):
                    element = element.contents[0]

            else:
                if element.name != 'textbf':
                    continue

                element = element.contents[0]
        else:    
            if '&' not in element:
                continue
        
        for cell in str(element).split('&'):
            striped = cell.strip()
            if (len(striped.replace('\\', ""))):


                while (i, j) in vis:
                    j+=1

                    if(j == n_columns):
                        j = 0
                        i+=1 

                vis[(i, j)] = striped

                if(span != None):
                    typee, num = span

                    if typee == 'multirow':
                        for x in range(i + 1, i + num):
                            vis[(x, j)] = ''
                    else:
                        for y in range(j + 1, j + num):
                            vis[(i, y)] = ''
                cells.append(striped)

    n_rows = i + 1
    

    cells_grid = [['' for _ in range(n_columns+1)] for _ in range(n_rows+1)]

    for (row, col), value in vis.items():
        cells_grid[row][col] =  restore_special_chars(value)
        
    return cells_grid

def tex_soup_to_json(tex_content):
    doc_index = 0
    content_count = len(tex_content.contents)
    
    for i in range(content_count):
        if not isinstance(tex_content.contents[i], str) and tex_content.contents[i].name == 'document':
            doc_index = i
            break

    document_content = tex_content.contents[doc_index]
    node_id = 0
    node_stack = [{'id': node_id, 'name': 'document', 'level': 0, 'type': 'document', 'children': []}]
    node_id += 1

    for element in document_content:
        if isinstance(element, str):
            # Truncate text to fit within MAX_TEXT_LENGTH
            text_length = len(element)
            truncated_text = element[:min(MAX_TEXT_LENGTH, text_length)]
            
            # Create a new node with the text as a hierarchy element
            text_node = {
                'id': node_id,
                'level': node_stack[-1]['level'] + 1,
                'name': restore_special_chars (truncated_text),
                'type': 'text',
                'children': []
            }
            node_stack[-1]['children'].append(text_node)
            node_id += 1

        elif element.name in HIERARCHY:
            element_depth = HIERARCHY.index(element.name)

            while element_depth <= HIERARCHY.index(node_stack[-1]['type']) and len(node_stack) > 1:
                node_stack.pop()

            if element_depth - 1 == HIERARCHY.index(node_stack[-1]['type']):
                new_node = {
                    'id': node_id,
                    'level': node_stack[-1]['level'] + 1,
                    'name': element.contents[0] if element.contents else '',
                    'type': element.name,
                    'children': []
                }
                node_stack[-1]['children'].append(new_node)
                node_stack.append(new_node)
                node_id += 1
            elif len(node_stack) > 1:
                raise Exception("Document is not structured with proper hierarchy")
        
        elif element.name in LEAF_NODES:
            
            children = []
            if element.name != 'table':
                # edit the count of the children and their level
                for item in element.contents:
                    text_node = {
                        'id': node_id,
                        'level': node_stack[-1]['level'] + 2, ##
                        'name': restore_special_chars(item.contents[0]) ,
                        'type': 'text',
                        'children': []
                                }
                    children.append(text_node)                    
                    node_id+=1##  

                name = element.name                  
            else: 
                children = table_signiture(element) 
                name = [' '.join(row) for row in children]
                name = ' '.join(name)
                ## to avoid the children of the table to be added to the children of the leaf node
                children = [] 

                


            leaf_node = {
                'id': node_id,
                'level': node_stack[-1]['level'] + 1,
                'name': name,
                'type': element.name,
                'children': children
            }
        
        
            node_stack[-1]['children'].append(leaf_node)
            node_id += 1

    return node_stack[0]


def tex_file_to_json(file_path = None, tex_data = None, log_path="logs.txt"):
    if tex_data is None:
        with open(file_path) as file:
            tex_data = file.read()

    tex_data = replace_special_chars(tex_data)
    tex_data = make_sure_one_document(tex_data)




    tex_soup = TS(tex_data)
    json_data = tex_soup_to_json(tex_soup)
    

    # # Prepare log entry as text
    # log_text = (
    #     "TeX File to JSON Conversion Log\n"
    #     f"Timestamp: {datetime.now().isoformat()}\n"
    #     "-" * 50 + "\n "
    #      "converted json: "
    #     + str(json_data)
    # )

    # # Append the log entry to the specified log file path
    # with open(log_path, "a") as log_file:
    #     log_file.write(log_text + "\n")


    return json_data

# Example usage
# tex_file_to_json('t.tex')