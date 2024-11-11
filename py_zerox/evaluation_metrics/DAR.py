import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import logging
from typing import Tuple, Dict, Set
import json

# Configure logging
logging.basicConfig(filename='./logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class RelationType:
    PARENT_CHILD = "parent_child"
    SIBLING = "sibling"
    COMBINED = "combined"


def truncate_text(text: str, max_chars: int = 100) -> str:
    """
    Truncate text to approximately first 15 words (or max_chars characters).
    If text is shorter than max_chars, return the original text.
    """
    if len(text) <= max_chars:
        return text
        
    # Find the last space within max_chars limit to avoid cutting words
    last_space = text[:max_chars].rfind(' ')
    if last_space == -1:  # No space found, just cut at max_chars
        return text[:max_chars] + '...'
    return text[:last_space] + '...'

def extract_relations(hierarchy: Dict) -> Dict[str, List[Tuple[str, str]]]:
    """
    Extract parent-child and unidirectional sibling relations from a heading hierarchy.
    Relations are stored using node names. Includes relations from the root document node.
    Skip processing children of table nodes.
    For text nodes, truncate value to approximately first 15 words.
    """
    parent_child_relations = []
    sibling_relations = []
    
    def get_node_value(node: Dict) -> str:
        """Get node value, truncating if it's a text node"""
        if node['type'] == 'text':
            return truncate_text(node['value'])
        return node['value']
    
    def process_siblings(siblings: List[Dict]):
        """Process sibling relationships among a list of nodes"""
        if not siblings:
            return
            
        try:
            sibling_names = [get_node_value(node) for node in siblings]
            for i in range(len(sibling_names)):
                for j in range(i + 1, len(sibling_names)):
                    sibling_relations.append((sibling_names[i], sibling_names[j]))
        except Exception as e:
            print(f"Error processing siblings: {siblings}")
            raise
    
    def process_node(node: Dict):
        """Process a single node and its children, skipping table children"""
        try:
            current_name = get_node_value(node)
            
            # Skip processing children if node is a table
            if node['type'] == 'table':
                return
            
            if 'children' in node and node['children']:
                children = node['children']
                # Process parent-child relations
                for child in children:
                    parent_child_relations.append((current_name, get_node_value(child)))
                    process_node(child)
                # Process sibling relations among children
                process_siblings(children)
        except Exception as e:
            print(f"Error processing node: {node}")
            raise
    
    # Start processing from root
    if not isinstance(hierarchy, dict):
        raise ValueError(f"Hierarchy must be a dictionary, got {type(hierarchy)}")
    
    # Validate root node
    if 'value' not in hierarchy or 'type' not in hierarchy:
        # If root doesn't have name/type, assume it's a document root
        hierarchy['value'] = 'document'
        hierarchy['type'] = 'root'
    
    if 'children' not in hierarchy:
        raise ValueError("Root node must have 'children' field")
        
    if not isinstance(hierarchy['children'], list):
        raise ValueError("Root 'children' must be a list")
    
    root_children = hierarchy['children']
    
    # Process root's relations with its immediate children
    for child in root_children:
        parent_child_relations.append((hierarchy['value'], get_node_value(child)))
    
    # Process siblings at root level
    process_siblings(root_children)
    
    # Process each child node and its descendants
    for node in root_children:
        process_node(node)
        
    return {
        RelationType.PARENT_CHILD: parent_child_relations,
        RelationType.SIBLING: sibling_relations
    }


def print_relation(relation: Tuple[int, int]):
    """Print a relation with both IDs and names."""
    try:
        source = relation[0]
        target = relation[1]
        print(f"  {source} → {target}")
    except KeyError as e:
        print(f"Error: Could not find node with ID {e} in node map")

def print_scores(metrics: Dict[str, Dict[str, float]]):
    """Print scores for all relation types."""
    print("\n=== EVALUATION SCORES ===\n")
    
    for relation_type in [RelationType.PARENT_CHILD, RelationType.SIBLING, RelationType.COMBINED]:
        print(f"\n{relation_type.upper()} SCORES:")
        print("-" * (len(relation_type) + 8))
        for metric, value in metrics[relation_type].items():
            if metric != 'details':
                print(f"{metric}: {value:.3f}")

def print_relation_analysis(gt_relations: Dict[str, Set[Tuple[int, int]]], 
                          pred_relations: Dict[str, Set[Tuple[int, int]]], 
                          metrics: Dict[str, Dict[str, float]],
                         ):
    """Print detailed analysis of relations and metrics."""
    print("\n=== DETAILED RELATION ANALYSIS ===\n")
    
    for relation_type in [RelationType.PARENT_CHILD, RelationType.SIBLING, RelationType.COMBINED]:
        print(f"\n{relation_type.upper()} RELATIONS:")
        print("=" * (len(relation_type) + 10))
        
        if relation_type != RelationType.COMBINED:
            print("\nGround Truth Relations:")
            print("-" * 20)
            for relation in gt_relations[relation_type]:
                print_relation(relation)
            
            print("\nPredicted Relations:")
            print("-" * 19)
            for relation in pred_relations[relation_type]:
                print_relation(relation )
        
        details = metrics[relation_type]['details']
        
        print("\nCorrect Predictions (True Positives):")
        print("-" * 35)
        for relation in details['true_positives']:
            print_relation(relation)
        
        print("\nMissed Relations (False Negatives):")
        print("-" * 33)
        for relation in details['false_negatives']:
            print_relation(relation)
        
        print("\nIncorrect Predictions (False Positives):")
        print("-" * 37)
        for relation in details['false_positives']:
            print_relation(relation )
        
        print("\n" + "="*50)

def calculate_metrics_by_type(gt_relations: List[Tuple[int, int]], 
                            pred_relations: List[Tuple[int, int]]) -> Dict[str, float]:
    """Calculate metrics for a specific relation type."""
    true_positives = [rel for rel in pred_relations if rel in gt_relations]
    false_positives = [rel for rel in pred_relations if rel not in gt_relations]
    false_negatives = [rel for rel in gt_relations if rel not in pred_relations]
    
    tp_count = len(true_positives)
    fp_count = len(false_positives)
    fn_count = len(false_negatives)
    
    precision = tp_count / len(pred_relations) if pred_relations else 0
    recall = tp_count / len(gt_relations) if gt_relations else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # More appropriate accuracy calculation
    total_decisions = tp_count + fp_count + fn_count
    accuracy = tp_count / total_decisions if total_decisions > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'accuracy': accuracy,
        'details': {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
    }

def evaluate_hierarchy(gt_json, pred_json , print_details = True) -> Dict[str, Dict[str, float]]:
    """
    Evaluate predicted heading hierarchy against ground truth using different relation types.
    Returns a dictionary with calculated metrics excluding detailed analysis.
    """
    try:
        # Validate root structure
        if not isinstance(gt_json, dict) or not isinstance(pred_json, dict):
            raise ValueError("Both ground truth and predicted JSON must be dictionaries")
        
        if 'children' not in gt_json or 'children' not in pred_json:
            raise ValueError("Both JSON structures must have a 'children' field at root level")
        
        # Extract relations
        gt_relations = extract_relations(gt_json)
        pred_relations = extract_relations(pred_json)
        
        # Calculate metrics for each case
        metrics = {}
        
        # Case 1: Parent-child relations only
        metrics[RelationType.PARENT_CHILD] = calculate_metrics_by_type(
            gt_relations[RelationType.PARENT_CHILD],
            pred_relations[RelationType.PARENT_CHILD]
        )
        
        # Case 2: Sibling relations only
        metrics[RelationType.SIBLING] = calculate_metrics_by_type(
            gt_relations[RelationType.SIBLING],
            pred_relations[RelationType.SIBLING]
        )
        
        # Case 3: Combined relations
        combined_gt = gt_relations[RelationType.PARENT_CHILD] + gt_relations[RelationType.SIBLING]
        combined_pred = pred_relations[RelationType.PARENT_CHILD] + pred_relations[RelationType.SIBLING]
        metrics[RelationType.COMBINED] = calculate_metrics_by_type(combined_gt, combined_pred)
        
        # Print scores and analysis
        if print_details:
            print_scores(metrics)
            print_relation_analysis(gt_relations, pred_relations, metrics)
        
        # Prepare return value with only main metrics, excluding 'details'
        summary_metrics = {
            relation_type: {metric: value for metric, value in metrics[relation_type].items() if metric != 'details'}
            for relation_type in metrics
        }
        
        return summary_metrics
    
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
        raise
    except ValueError as e:
        print(f"Validation error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise