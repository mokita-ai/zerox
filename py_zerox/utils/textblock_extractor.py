from datetime import datetime


def extract_text(data, current_heading=None, result=None, log_path="logs.txt", log_text=None):
    """
    Recursively extracts text from a nested data structure, grouping text by headings, and logs all extractions in a single entry.

    Args:
        data (dict): The input data with nested elements.
        current_heading (str, optional): Tracks the current heading as we navigate through nested elements.
        result (dict, optional): Stores the extracted text grouped by headings.
        log_path (str, optional): The path to save the log file in text format (default is 'logs.txt').
        log_text (list, optional): Accumulates log entries for a single function run.

    Returns:
        dict: A dictionary with headings as keys and concatenated text as values.
    """
    # Initialize result and log_text if not already provided (only on the initial call)
    if result is None:
        result = {}
    if log_text is None:
        log_text = [
            f"Extract Text Log - Timestamp: {datetime.now().isoformat()}",
            "-" * 50
        ]

    # Check if the current node has children and iterate through them
    if "children" in data:
        for child in data["children"]:
            # If the child is a heading (e.g., section, subsection, etc.)
            if child["type"] in ["document", "section", "subsection", "subsubsection", "paragraph", "subparagraph", "itemize", "enumerate"]:
                # Update the current heading name
                new_heading = child["name"]
                log_text.append(f"Processing heading: {new_heading}")
                extract_text(child, new_heading, result, log_path, log_text)
                
            # If the child is of type "text," concatenate it to the current heading's text
            elif child["type"] == "text" and current_heading is not None:
                text = child["name"]
                if current_heading in result:
                    result[current_heading] += text
                else:
                    result[current_heading] = text
                log_text.append(f"Extracted text under heading '{current_heading}': {text}")
                    
            # Recursively process the remaining children
            else:
                extract_text(child, current_heading, result, log_path, log_text)
    
    # Only write to the log file on the initial call (when the function completes all recursive calls)
    if current_heading is None:
        log_text.append("-" * 50 + "\n\n")
        with open(log_path, "a") as log_file:
            log_file.write("\n".join(log_text))

    return result



def find_and_matching_values(dict1, dict2, log_path="logs.txt"):
    """
    Finds matching values between two dictionaries based on their keys and logs the results.

    Parameters:
    ----------
    dict1 : dict
        The first dictionary to compare.
    dict2 : dict
        The second dictionary to compare.
    log_path : str, optional
        The path to save the log file in text format (default is 'logs.txt').

    Returns:
    -------
    matching_values : list of tuples
        A list of tuples containing matching, missing, and unique values between the two dictionaries.
    
    Example Usage:
    --------------
    matching_values = find_and_log_matching_values(dict1, dict2, "path/to/logs.txt")
    """

    matching_values = []

    # Find common keys and add corresponding values from both dictionaries
    common_keys = dict1.keys() & dict2.keys()
    for key in common_keys:
        matching_values.append((dict1[key], dict2[key]))

    # Add values from dict1 with missing keys in dict2
    for key in (dict1.keys() - dict2.keys()):
        matching_values.append((dict1[key], ""))

    # Add values from dict2 with missing keys in dict1
    for key in (dict2.keys() - dict1.keys()):
        matching_values.append(("", dict2[key]))

    # Log matching values to file
    log_text = (
        "Matching Values Log\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        "-" * 50 + "\n"
        "Matching Values:\n"
    )
    for pair in matching_values:
        log_text += f"{pair}\n"
    log_text += "-" * 50 + "\n\n"

    # Append the log to the specified log file path
    with open(log_path, "a") as log_file:
        log_file.write(log_text)

    print(matching_values)
    return matching_values
