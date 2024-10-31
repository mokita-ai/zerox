def extract_text(data, current_heading=None, result=None):
    """
    Recursively extracts text from a nested data structure, grouping text by headings.

    Args:
        data (dict): The input data with nested elements.
        current_heading (str, optional): Tracks the current heading as we navigate through nested elements.
        result (dict, optional): Stores the extracted text grouped by headings.

    Returns:
        dict: A dictionary with headings as keys and concatenated text as values.
    """
    if result is None:
        result = {}

    # Check if the current node has children and iterate through them
    if "children" in data:
        for child in data["children"]:
            # If the child is a heading (e.g., section, subsection, etc.)
            if child["type"] in ["document", "section", "subsection", "subsubsection", "paragraph", "subparagraph", "itemize", "enumerate"]:
                # Update the current heading name
                new_heading = child["name"]
                extract_text(child, new_heading, result)
                
            # If the child is of type "text," concatenate it to the current heading's text
            elif child["type"] == "text" and current_heading is not None:
                if current_heading in result:
                    result[current_heading] += child["name"]
                else:
                    result[current_heading] = child["name"]
                    
            # Recursively process the remaining children
            else:
                extract_text(child, current_heading, result)
    
    return result
