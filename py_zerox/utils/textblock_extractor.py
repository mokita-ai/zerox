from datetime import datetime


def extract_text(data, current_path=None, result=None):
    """
    Recursively extracts text and tables from a nested data structure, grouping them by their paths.
    Text nodes with the same path are concatenated, tables with the same path are concatenated.
    Text and tables are kept separate even if they share the same path.
    
    Args:
        data (dict): The nested data structure to process
        current_path (list): The current path in the tree (list of section names)
        result (dict): Dictionary to store results with paths as keys
    
    Returns:
        dict: Dictionary with paths as keys and text/tables as values. 
              Text paths end with ":text" and table paths end with ":table"
    """
    if result is None:
        result = {}
    
    if current_path is None:
        current_path = []
    
    # Get the current node's name if it exists and isn't a text/table
    if "value" in data and data["type"] not in ["text", "table"]:
        current_path = current_path + [data["value"]]
    
    # If we find a text or table node, add it to the result
    if data["type"] in ["text"]:
        # Create path string with type indicator
        path_key = " > ".join(current_path) + f":{data['type']}"
        
        # Add or concatenate the content based on type
        if path_key in result:
            # For text, concatenate strings
            if data["type"] == "text":
                result[path_key] = result[path_key] + "\n" + data["value"]
            # For tables, concatenate with a separator
            else:  # table type
                result[path_key] = result[path_key] + "\n=====\n" + data["value"]
        else:
            result[path_key] = data["value"]
            
        return result
    
    # Process children if they exist
    if "children" in data:
        for child in data["children"]:
            extract_text(child, current_path, result)
    
    return result

def find_and_matching_values(dict1, dict2):
    """
    Finds matching values between two dictionaries based on their keys, using the order of keys from dict1.
    
    Parameters:
    ----------
    dict1 : dict
        The ground truth dictionary to compare.
    dict2 : dict
        The second dictionary to compare.
    
    Returns:
    -------
    matching_values : list of tuples
        A list of tuples containing matching, missing, and unique values between the two dictionaries,
        ordered according to the keys in dict1.
    """
    matching_values = []

    # Process each key in dict1 and gather matching or missing values from dict2
    for key in dict1:
        if key in dict2:
            matching_values.append((dict1[key], dict2[key]))  # Matching values
        else:
            matching_values.append((dict1[key], ""))  # Missing in dict2
    
    # Add values from dict2 with keys missing in dict1, preserving the original order of dict2 for these keys
    for key in dict2:
        if key not in dict1:
            matching_values.append(("", dict2[key]))

    return matching_values
