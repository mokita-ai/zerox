from datetime import datetime

def extract_text(data, current_path=None, text_result=None, table_result=None):
    """
    Recursively extracts text and tables from a nested data structure, grouping them by their paths.
    Text nodes with the same path are concatenated, tables with the same path are concatenated.
    """
    if text_result is None:
        text_result = {}
    
    if table_result is None:
        table_result = {}
    
    if current_path is None:
        current_path = []
    
    # Get the current node's name if it exists and isn't a text/table
    if "value" in data and data["type"] not in ["text", "table"]:
        current_path = current_path + [data["value"]]
    
    # If we find a text or table node, add it to the result
    if data["type"] in ["text", "table"]:
        # Create path string
        path_key = " > ".join(current_path)
        
        if data["type"] == "text":
            # For text, concatenate strings
            if path_key in text_result:
                text_result[path_key] += data["value"]
            else:
                text_result[path_key] = data["value"]
        else:
            # For tables, accumulate the data
            if path_key in table_result:
                table_result[path_key].append(data)
            else:
                table_result[path_key] = [data]
        
        return text_result, table_result
    
    # Process children if they exist
    if "children" in data:
        for child in data["children"]:
            extract_text(child, current_path, text_result, table_result)
    
    return text_result, table_result


def find_and_matching_values(dict1, dict2 , text = True):
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
            matching_values.append((dict1[key], "" if text else [""]))  # Missing in dict2
    
    # Add values from dict2 with keys missing in dict1, preserving the original order of dict2 for these keys
    for key in dict2:
        if key not in dict1:
            matching_values.append(("" if text else [""], dict2[key]))  # Missing in dict1

    return matching_values


def create_table_pairs(tables_matching_values):
    """
    Convert grouped table matches into individual pairs, padding shorter lists with empty strings.
    
    Args:
        tables_matching_values: List of tuples, each containing two lists:
            - GT tables list
            - Predicted tables list
    
    Returns:
        List of tuples, each containing a (gt_table, pred_table) pair.
        If one list is longer, the shorter list is padded with empty strings.
    """
    all_pairs = []
    
    for gt_tables, pred_tables in tables_matching_values:
        # Get the lengths of both lists
        gt_len = len(gt_tables)
        pred_len = len(pred_tables)
        
        # Find the maximum length
        max_len = max(gt_len, pred_len)
        
        # Pad the shorter list with empty strings
        gt_tables_padded = gt_tables + [""] * (max_len - gt_len)
        pred_tables_padded = pred_tables + [""] * (max_len - pred_len)
        
        # Create pairs using the padded lists
        for gt, pred in zip(gt_tables_padded, pred_tables_padded):
            all_pairs.append((gt, pred))
    
    return all_pairs


def full_text_pair(GT_dict_text , pred_dict_text):
    # concatenate all values for all keys in pred_dict_text
    pred_full_text = ""
    for key in pred_dict_text.keys():
        pred_full_text += pred_dict_text[key]
    
    GT_full_text = ""
    for key in GT_dict_text.keys():
        GT_full_text += GT_dict_text[key]
    
    full_text_pair = (GT_full_text , pred_full_text)
    return full_text_pair