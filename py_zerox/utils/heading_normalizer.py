import re
from difflib import SequenceMatcher
import copy
import json


import json

def load_and_validate_json(file_path):
    """
    Load a JSON file and validate that it contains the expected structure
    with a 'children' field at the root level.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.

    Raises:
        ValueError: If the JSON does not have the expected structure.
    """
    # Load JSON file
    with open(file_path, 'r') as f:
        json_data = json.load(f)
        print(f"JSON file '{file_path}' loaded successfully")

    # Validate JSON structure
    if not isinstance(json_data, dict):
        raise ValueError(f"The JSON file '{file_path}' must be a dictionary at the root level.")
    
    if 'children' not in json_data:
        raise ValueError(f"The JSON file '{file_path}' must contain a 'children' field at the root level.")
    
    return json_data

# Example usage:
# gt_json = load_and_validate_json('ground_truth.json')
# pred_json = load_and_validate_json('prediction.json')




def normalize_text(text):
    """Normalize text for comparison by removing special characters and standardizing spacing."""
    # Convert to lowercase
    text = text.lower()
    # Replace special characters with spaces
    text = re.sub(r'[.,(){}[\]\'\"#]', ' ', text)
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()

def calculate_similarity(text1, text2):
    """Calculate similarity ratio between two texts after normalization."""
    norm_text1 = normalize_text(text1)
    norm_text2 = normalize_text(text2)
    return SequenceMatcher(None, norm_text1, norm_text2).ratio()

def find_matching_headings(pred_json, gt_json, similarity_threshold=0.75):
    """Find matching headings between predicted and ground truth JSONs."""
    HEADING_TYPES = ['document', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
    matches = []
    changes = []
    
    def collect_headings(node, headings):
        if isinstance(node, dict) and node.get('type') in HEADING_TYPES:
            headings.append(node)
        if isinstance(node, dict) and 'children' in node:
            for child in node['children']:
                collect_headings(child, headings)
    
    pred_headings = []
    gt_headings = []
    collect_headings(pred_json, pred_headings)
    collect_headings(gt_json, gt_headings)
    
    # Find matches without type constraint
    for pred_heading in pred_headings:
        best_match = None
        best_similarity = similarity_threshold
        
        for gt_heading in gt_headings:
            similarity = calculate_similarity(pred_heading['name'], gt_heading['name'])
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = gt_heading
        
        if best_match:
            matches.append((pred_heading, best_match))
            if pred_heading['name'] != best_match['name']:
                changes.append({
                    'original': pred_heading['name'],
                    'replaced_with': best_match['name'],
                    'similarity': best_similarity,
                    'original_type': pred_heading['type'],
                    'matched_type': best_match['type']
                })
    
    return matches, changes

def update_json_headings(json_data, matches):
    """Update the predicted JSON with matching heading names from ground truth."""
    updated_json = copy.deepcopy(json_data)
    
    def update_node(node):
        for match_pred, match_gt in matches:
            if isinstance(node, dict) and node.get('id') == match_pred['id']:
                node['name'] = match_gt['name']
        
        if isinstance(node, dict) and 'children' in node:
            for child in node['children']:
                update_node(child)
    
    update_node(updated_json)
    return updated_json

def normalize_headings(pred_json, gt_json):
    """Main function to normalize headings in predicted JSON based on ground truth."""
    matches, changes = find_matching_headings(pred_json, gt_json)
    updated_json = update_json_headings(pred_json, matches)
    
    return updated_json, changes

