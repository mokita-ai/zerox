from difflib import SequenceMatcher
import copy
import json
from datetime import datetime
import re
import os


def normalize_text(text):
    """Normalize text for comparison by removing special characters and standardizing spacing."""
    text = text.lower()
    text = re.sub(r'[.,(){}[\]\'\"#]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
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

import re
from difflib import SequenceMatcher
import copy
from datetime import datetime
import os

def normalize_headings(pred_json, gt_json, log_path="logs.txt"):
    """
    Normalize headings in predicted JSON based on ground truth, logging changes to a text file.

    Parameters:
    ----------
    pred_json : dict
        The predicted JSON structure with headings to normalize.
    gt_json : dict
        The ground truth JSON structure for reference.
    log_path : str, optional
        Path to the log file (default is 'logs.txt').

    Returns:
    -------
    updated_json : dict
        The updated JSON structure with normalized headings.
    changes : list
        A list of changes made during normalization.

    Workflow:
    --------
    1. Finds matching headings in predicted and ground truth JSON based on similarity.
    2. Updates predicted JSON with matched headings from ground truth.
    3. Logs a formatted report of changes along with metadata for traceability.
    """
    matches, changes = find_matching_headings(pred_json, gt_json)
    updated_json = update_json_headings(pred_json, matches)

    # Create the change report as a formatted string
    report_lines = [
        "Heading Normalization Report:",
        "-" * 50,
        f"Timestamp: {datetime.now().isoformat()}",
        f"File: {log_path}",
        "-" * 50
    ]
    for change in changes:
        report_lines.append(f"Original: {change['original']} ({change['original_type']})")
        report_lines.append(f"Replaced with: {change['replaced_with']} ({change['matched_type']})")
        report_lines.append(f"Similarity score: {change['similarity']:.2f}")
        report_lines.append("-" * 50)

    report_text = "\n".join(report_lines)

    # Append the report to the log file
    with open(log_path, "a") as log_file:
        log_file.write(report_text + "\n\n")

    return updated_json, changes
