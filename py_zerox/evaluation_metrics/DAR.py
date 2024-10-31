import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import logging
from typing import Tuple, Dict, Set
import json

# Configure logging
logging.basicConfig(filename='logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RelationType:
    PARENT_CHILD = "parent_child"
    SIBLING = "sibling"
    COMBINED = "combined"

class NodeInfo:
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
    
    def __str__(self):
        return f"{self.name} (Type: {self.type})"

def validate_node(node: Dict) -> bool:
    """Validate that a node has all required fields and correct types"""
    required_fields = {'name': str, 'type': str}
    
    for field, expected_type in required_fields.items():
        if field not in node:
            raise ValueError(f"Missing required field '{field}' in node: {node}")
        if not isinstance(node[field], expected_type):
            raise ValueError(f"Field '{field}' in node has wrong type. Expected {expected_type}, got {type(node[field])}. Node: {node}")
    
    if 'children' in node and not isinstance(node['children'], list):
        raise ValueError(f"Field 'children' must be a list. Node: {node}")
    
    return True

def extract_relations(hierarchy: Dict) -> Dict[str, Set[Tuple[str, str]]]:
    """
    Extract parent-child and unidirectional sibling relations from a heading hierarchy.
    Relations are stored using node names. Includes relations from the root document node.
    """
    parent_child_relations = set()
    sibling_relations = set()
    
    def process_siblings(siblings: List[Dict]):
        """Process sibling relationships among a list of nodes"""
        if not siblings:
            return
            
        try:
            for node in siblings:
                validate_node(node)
            
            sibling_names = [node['name'] for node in siblings]
            for i in range(len(sibling_names)):
                for j in range(i + 1, len(sibling_names)):
                    sibling_relations.add((sibling_names[i], sibling_names[j]))
        except Exception as e:
            print(f"Error processing siblings: {siblings}")
            raise
    
    def process_node(node: Dict):
        """Process a single node and its children"""
        try:
            validate_node(node)
            current_name = node['name']
            
            if 'children' in node and node['children']:
                children = node['children']
                # Process parent-child relations
                for child in children:
                    validate_node(child)
                    parent_child_relations.add((current_name, child['name']))
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
    if 'name' not in hierarchy or 'type' not in hierarchy:
        # If root doesn't have name/type, assume it's a document root
        hierarchy['name'] = 'document'
        hierarchy['type'] = 'root'
    
    validate_node(hierarchy)
    
    if 'children' not in hierarchy:
        raise ValueError("Root node must have 'children' field")
        
    if not isinstance(hierarchy['children'], list):
        raise ValueError("Root 'children' must be a list")
    
    root_children = hierarchy['children']
    
    # Process root's relations with its immediate children
    for child in root_children:
        validate_node(child)
        parent_child_relations.add((hierarchy['name'], child['name']))
    
    # Process siblings at root level
    process_siblings(root_children)
    
    # Process each child node and its descendants
    for node in root_children:
        process_node(node)
    
    return {
        RelationType.PARENT_CHILD: parent_child_relations,
        RelationType.SIBLING: sibling_relations
    }

def build_node_info_map(hierarchy: Dict) -> Dict[str, NodeInfo]:
    """Build a mapping of node names to their information"""
    node_map = {}
    
    # Add root node to the map if it has name and type
    if 'name' in hierarchy and 'type' in hierarchy:
        node_map[hierarchy['name']] = NodeInfo(hierarchy['name'], hierarchy['type'])
    elif 'children' in hierarchy:  # Add default document root if not specified
        node_map['document'] = NodeInfo('document', 'root')
    
    def process_node(node: Dict):
        try:
            validate_node(node)
            node_map[node['name']] = NodeInfo(node['name'], node['type'])
            if 'children' in node and node['children']:
                for child in node['children']:
                    process_node(child)
        except Exception as e:
            print(f"Error processing node in build_node_info_map: {node}")
            raise
    
    if 'children' in hierarchy:
        for node in hierarchy['children']:
            process_node(node)
    
    return node_map






def calculate_metrics_by_type(gt_relations: Set[Tuple[int, int]], 
                            pred_relations: Set[Tuple[int, int]]) -> Dict[str, float]:
    """Calculate metrics for a specific relation type."""
    true_positives = gt_relations.intersection(pred_relations)
    false_positives = pred_relations - gt_relations
    false_negatives = gt_relations - pred_relations
    
    tp_count = len(true_positives)
    fp_count = len(false_positives)
    fn_count = len(false_negatives)
    
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    total_relations = len(gt_relations.union(pred_relations))
    accuracy = tp_count / total_relations if total_relations > 0 else 0
    
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


def log_relation(relation: Tuple[int, int], node_map: Dict[int, NodeInfo]):
    """Log a relation with both IDs and names."""
    try:
        source = node_map[relation[0]]
        target = node_map[relation[1]]
        logger.info(f"  {source} → {target}")
    except KeyError as e:
        logger.error(f"Error: Could not find node with ID {e} in node map")

def log_scores(metrics: Dict[str, Dict[str, float]]):
    """Log scores for all relation types."""
    logger.info("\n=== EVALUATION SCORES ===\n")
    
    for relation_type in [RelationType.PARENT_CHILD, RelationType.SIBLING, RelationType.COMBINED]:
        logger.info(f"\n{relation_type.upper()} SCORES:")
        logger.info("-" * (len(relation_type) + 8))
        for metric, value in metrics[relation_type].items():
            if metric != 'details':
                logger.info(f"{metric}: {value:.3f}")

def log_relation_analysis(gt_relations: Dict[str, Set[Tuple[int, int]]], 
                          pred_relations: Dict[str, Set[Tuple[int, int]]], 
                          metrics: Dict[str, Dict[str, float]],
                          gt_node_map: Dict[int, NodeInfo],
                          pred_node_map: Dict[int, NodeInfo]):
    """Log detailed analysis of relations and metrics."""
    logger.info("\n=== DETAILED RELATION ANALYSIS ===\n")
    
    for relation_type in [RelationType.PARENT_CHILD, RelationType.SIBLING, RelationType.COMBINED]:
        logger.info(f"\n{relation_type.upper()} RELATIONS:")
        logger.info("=" * (len(relation_type) + 10))
        
        if relation_type != RelationType.COMBINED:
            logger.info("\nGround Truth Relations:")
            logger.info("-" * 20)
            for relation in sorted(gt_relations[relation_type]):
                log_relation(relation, gt_node_map)
            
            logger.info("\nPredicted Relations:")
            logger.info("-" * 19)
            for relation in sorted(pred_relations[relation_type]):
                log_relation(relation, pred_node_map)
        
        details = metrics[relation_type]['details']
        
        logger.info("\nCorrect Predictions (True Positives):")
        logger.info("-" * 35)
        for relation in sorted(details['true_positives']):
            log_relation(relation, gt_node_map)
        
        logger.info("\nMissed Relations (False Negatives):")
        logger.info("-" * 33)
        for relation in sorted(details['false_negatives']):
            log_relation(relation, gt_node_map)
        
        logger.info("\nIncorrect Predictions (False Positives):")
        logger.info("-" * 37)
        for relation in sorted(details['false_positives']):
            log_relation(relation, pred_node_map)
        
        logger.info("\n" + "="*50)


def evaluate_hierarchy(gt_json, pred_json) -> Dict[str, Dict[str, float]]:
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
        
        # Build node info maps
        gt_node_map = build_node_info_map(gt_json)
        pred_node_map = build_node_info_map(pred_json)
        
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
        combined_gt = gt_relations[RelationType.PARENT_CHILD].union(gt_relations[RelationType.SIBLING])
        combined_pred = pred_relations[RelationType.PARENT_CHILD].union(pred_relations[RelationType.SIBLING])
        metrics[RelationType.COMBINED] = calculate_metrics_by_type(combined_gt, combined_pred)
        
        # Log scores
        log_scores(metrics)
        
        log_relation_analysis(gt_relations, pred_relations, metrics, gt_node_map, pred_node_map)
        
        # Prepare return value with only main metrics, excluding 'details'
        summary_metrics = {
            relation_type: {metric: value for metric, value in metrics[relation_type].items() if metric != 'details'}
            for relation_type in metrics
        }
        
        return summary_metrics
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
