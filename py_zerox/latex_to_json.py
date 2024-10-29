HIERARCHY = ['document', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
LEAF_NODES = ['itemize', 'table', 'enumerate']
MAX_TEXT_LENGTH = 1500000

from TexSoup import TexSoup as TS

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
            text_length = len(element)
            truncated_text = element[:min(MAX_TEXT_LENGTH, text_length)]
            node_stack[-1]['children'].append(truncated_text)

        elif element.name in HIERARCHY:
            element_depth = HIERARCHY.index(element.name)
            
            while element_depth <= HIERARCHY.index(node_stack[-1]['type']) and len(node_stack) > 1:
                node_stack.pop()

            if element_depth - 1 == HIERARCHY.index(node_stack[-1]['type']):
                new_node = {
                    'id': node_id,
                    'name': element.contents[0],
                    'type': element.name,
                    'children': [],
                    'level': node_stack[-1]['level'] + 1
                }
                node_stack[-1]['children'].append(new_node)
                node_stack.append(new_node)
                node_id += 1
            elif len(node_stack) > 1:
                raise Exception("Document is not structured with proper hierarchy")
        
        elif element.name in LEAF_NODES:

            children = []
            if element.name != 'table':
                children = [item.contents[0] for item in element.contents]


            leaf_node = {
                'id': node_id,
                'name': element.name,
                'level': node_stack[-1]['level'] + 1,
                'type': 'leaf',
                'children': children
            }
            node_stack[-1]['children'].append(leaf_node)
            node_id += 1


    return node_stack[0]

def tex_file_to_json(file_path = None, tex_data = None):
    if tex_data == None:
        with open(file_path) as file:
            tex_data = file.read()
    tex_soup = TS(tex_data)

    return tex_soup_to_json(tex_soup)