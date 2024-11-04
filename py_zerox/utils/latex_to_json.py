
from TexSoup.data import TexNode
from TexSoup import TexSoup as TS
from utils.common import *
import uuid

def table_signiture(soup):
    tabular_index = -1 ## the index of the tag tabular the we huant for
    content_count = len(soup.contents)

    for i in range(content_count):
        if not isinstance(soup.contents[i], str) and soup.contents[i].name == 'tabular':
            tabular_index = i ## we found the tabular tag
            break

    if tabular_index == -1:
        raise Exception("not a valid table")
    
    tabular_content_text = str(soup.contents[tabular_index])
    tabular_content_text =  re.sub(re.escape("&"), "SPACE_TOKEN&SPACE_TOKEN", tabular_content_text) ## to handle empty table cells

    
    tabular_content_text = re.sub(r'\{\}', r'{SPACE_TOKEN}', tabular_content_text)  ##to handle empty {}
    # tabular_content_text = remove_latex_drawing_commands(tabular_content_text)
    tabular_content_text = remove_unnecessary_space_token(tabular_content_text) 

    # print(tabular_content_text)
    soup = TS(tabular_content_text)


    column_string = soup.contents[0].contents[0] ## for example "|c|c|c|" or "ccc"
    stripped_string = column_string.replace('|', '').replace(' ', '')

    # Count the remaining characters
    n_columns = len(stripped_string) ## is 3 in the example

    i, j =  0, 0
    vis = {}
    for element in soup.contents[0].contents:
        span = None
        isHeader = False

        if isinstance(element, TexNode) and len(element.contents):
            if element.name in SPANING_CELLS: 
                span = element.name, int(element.contents[0])
                element = element.contents[2]

                if not isinstance(element, str):
                   element = element.contents[0]
            else:
                if element.name not in TEXT_TAGS:
                    continue

                if element.name == 'thead':
                    isHeader = True
        
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
                        i += 1  

                vis[(i, j)] = {"type" : "cell", "value": text_end_point(striped)}

                if isHeader:
                    vis[(i, j)]["isHeader"] = True

                if(span != None):
                    typee, num = span

                    if typee == 'multirow':
                        vis[(i, j)]['rowspan'] = num
                        for x in range(i + 1, i + num):
                            vis[(x, j)] = ''
                    else:
                        vis[(i, j)]['colspan'] = num
                        for y in range(j + 1, j + num):
                            vis[(i, y)] = ''
                # cells.append(striped)

    n_rows = i + 1
    

    table_rows = [ {"type": "row", "value":"", "children": []} for _ in range(n_rows)]

    for (row, col), value in vis.items():
        if not (row < n_rows and col < n_columns):
            raise Exception("Table is not well formed")
        
        if value != '':
            table_rows[row]["children"].append(value)
        
    return table_rows

def tex_soup_to_json(tex_content = None, document_content = None, custom_value = 'document', custom_type = 'document', level = 0, page = 0):
    if document_content  == None:
        doc_index = 0
        content_count = len(tex_content.contents)
        
        for i in range(content_count):
            if not isinstance(tex_content.contents[i], str) and tex_content.contents[i].name == 'document':
                doc_index = i
                break

        document_content = tex_content.contents[doc_index]


 
    node_stack = [{
            'id': str(uuid.uuid4()), 
            'type': custom_type, 
            'value': custom_value , 
            'level': level, 
            'bbox':  [], 
            'page': page, 
            'children': []
        }
    ]


    for element in document_content:
        if isinstance(element, TexNode) and element.name in TEXT_TAGS:
            element = element.contents[0]
            
        if isinstance(element, str) :
            text_length = len(element)
            truncated_text = element[:min(MAX_TEXT_LENGTH, text_length)]# Truncate text to fit within MAX_TEXT_LENGTH
            
            # Create a new node with the text as a hierarchy element
            text_node = {
                'id': str(uuid.uuid4()),
                'type': 'text',
                'value': text_end_point (truncated_text),
                'level': node_stack[-1]['level'] + 1,
                'bbox':  [],
                'page': page,
                'children': []
            }
            node_stack[-1]['children'].append(text_node)
  

        elif element.name in HIERARCHY:
            element_depth = HIERARCHY.index(element.name)

            while element_depth <= HIERARCHY.index(node_stack[-1]['type']) and len(node_stack) > 1:
                node_stack.pop()

            # if element_depth - 1 == HIERARCHY.index(node_stack[-1]['type']):
            new_node = {
                'id': str(uuid.uuid4()),
                'type': element.name,
                'value':  text_end_point(element.contents[0]) if element.contents else '',
                'level': node_stack[-1]['level'] + 1,
                'bbox':  [],
                'page': page,
                'children': []
            }
            node_stack[-1]['children'].append(new_node)
            node_stack.append(new_node)

            # elif len(node_stack) > 1:
            #     print("Document have orphane text")
            #     ##TODO: handle the orphane text
            #     continue
            #     # raise Exception("Document is not structured with proper hierarchy")
        
        elif element.name in LEAF_NODES:
            children = []
            if element.name != 'table': ##itimize and enumerate
                for item in element.contents:                    
                    if len(item.contents) == 1:
                        value = text_end_point(item.contents[0])

                        text_node = {
                            'id': str(uuid.uuid4()),
                            'type': 'text',
                            'value': value,
                            'level': node_stack[-1]['level'] + 2, ##
                            'bbox':  [],
                            'page': page,
                            'children': []
                        }
                        children.append(text_node)                    
        

                    else:
                        document_content = item.contents
                        custom_value = 'item'
                        custom_type = 'item'
                        level = node_stack[-1]['level'] + 2 

                        if isinstance(document_content[0], TexNode) and document_content[0].name in TEXT_TAGS:
                            custom_value = text_end_point(document_content[0])
                            document_content = document_content[1:]



                        item_node = tex_soup_to_json(document_content = document_content, custom_value = custom_value, custom_type =  custom_type, level = level)

                        ##TODO
                        children.append(item_node)

                        # print("Document have itimize complex")
                        # name = 'CANNOT_PARSE'


                    

                value = element.name                  
            else: 
                children = table_signiture(element) 
                value = ""
                for row in children:
                    for cell in row['children']:
                        value += cell['value'] + ' '

                ##TODO
                # name = [' '.join(row) for row in children]
                # name = ' '.join(name)
                ## to avoid the children of the table to be added to the children of the leaf node
                # children = [] 

                


            leaf_node = {
                'id': str(uuid.uuid4()),
                'type': element.name,
                'value': value,
                'level': node_stack[-1]['level'] + 1,
                'bbox':  [],
                'page': page,
                'children': children
            }
        
        
            node_stack[-1]['children'].append(leaf_node)
       

    return node_stack[0]


def tex_file_to_json(file_path = None, tex_data = None, log_path="logs.txt"):
    if tex_data is None:
        with open(file_path) as file:
            tex_data = file.read()

    tex_data = replace_special_chars(tex_data)
    tex_data = make_sure_one_document(tex_data)

    tex_data = re.sub(r'\\(section|subsection|subsubsection|paragraph|subparagraph)\*', r'\\\1', tex_data)

    # tex_data = re.sub(r'\[a-zA-Z]+\*\{.*?\}', '', tex_data)


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