from collections import deque
from typing import List, Optional, Tuple

from apted import APTED, Config
from apted.helpers import Tree
from Levenshtein import distance

from typing import Optional, List, Tuple, Dict
from collections import deque

class TableTree(Tree):
    def __init__(
        self,
        tag: str,
        colspan: Optional[int] = None,
        rowspan: Optional[int] = None,
        content: Optional[List[str]] = None,
        *children: Tuple['TableTree'],
    ):
        self.tag = tag
        self.colspan = colspan
        self.rowspan = rowspan
        self.content = content
        self.children = list(children)

class CustomConfigJson(Config):
    @staticmethod
    def maximum(*sequences):
        """Get maximum possible value"""
        return max(map(len, sequences))

    def normalized_distance(self, *sequences):
        """Get distance from 0 to 1"""
        return float(distance(*sequences)) / self.maximum(*sequences)

    def rename(self, node1: TableTree, node2: TableTree) -> float:
        """Compares attributes of trees"""
        if (
            (node1.tag != node2.tag)
            or (node1.colspan != node2.colspan)
            or (node1.rowspan != node2.rowspan)
        ):
            return 1.0

        if node1.tag == "cell":
            if node1.content or node2.content:
                return self.normalized_distance(node1.content, node2.content)

        return 0.0



class TEDS_JSON:
    """Tree Edit Distance based Similarity"""

    def __init__(
        self, structure_only: bool = False, ignore_nodes: Optional[List[str]] = None
    ):
        self.structure_only = structure_only
        self.ignore_nodes = ignore_nodes
        self.__tokens__: List[str] = []

    # print tokens
    def __str__(self):
        return str(self.__tokens__)

    def __call__(self, pred: Dict, gt: Dict) -> float:
        """Computes TEDS score between the prediction and the ground truth of a
        given sample

        Args:
            pred (Dict): The predicted JSON representation of the table.
            gt (Dict): The ground truth JSON representation of the table.

        Returns:
            float: TEDS score
        """
        if not pred or not gt:
            return 0.0

        tree_pred = self.load_json_tree(pred)

        tree_true = self.load_json_tree(gt)
        distance = APTED(tree_pred, tree_true, CustomConfigJson()).compute_edit_distance()
        n_nodes_pred = self.count_nodes(tree_pred) - 1 # -1 to exclude the root node
        n_nodes_true = self.count_nodes(tree_true) - 1 
        n_nodes = max(n_nodes_pred, n_nodes_true)
        return 1.0 - (float(distance) / n_nodes)

    def tokenize(self, node: Dict):
        """Tokenizes table cells"""
        self.__tokens__.append(f"<{node['type']}>")

        if 'value' in node and node['value']:
            self.__tokens__ += list(node['value'])

        if 'children' in node:
            for child in node['children']:
                self.tokenize(child)

        if node['type'] != "unk":
            self.__tokens__.append(f"</{node['type']}>")

    def load_json_tree(
        self, node: Dict, parent: Optional[TableTree] = None
    ) -> Optional[TableTree]:
        """Converts JSON tree to the format required by APTED"""
        if node['type'] == 'cell':
            if self.structure_only:
                cell_content = []
            else:
                self.__tokens__ = []
                self.tokenize(node)
                cell_content = self.__tokens__[1:-1].copy()

            new_node = TableTree(
                'cell',
                int(node.get('colspan', 1)),
                int(node.get('rowspan', 1)),
                cell_content,
                *deque(),
            )
        else: # table or row
            new_node = TableTree(
                node['type'],
                None,
                None,
                None,
                *deque(),
            )

        if parent is not None:
            parent.children.append(new_node)

        if 'children' in node: 
            for child in node['children']:
                self.load_json_tree(child, new_node)
        if parent is None:
            return new_node
        return None

    def count_nodes(self, tree: TableTree) -> int:
        """Counts the number of nodes in a tree"""
        count = 1  # Count the current node
        for child in tree.children:
            count += self.count_nodes(child)
        return count
    


    
def evaluate_teds(tables_pairs):
    structure_only_scores = []
    scores = []
    for gt , pred in tables_pairs:
        structure_only_score = TEDS_JSON(structure_only=True)(pred, gt)
        score = TEDS_JSON(structure_only=False)(pred, gt)
        scores.append(score)
        structure_only_scores.append(structure_only_score)

    if len(scores) == 0:
        return {"scores":scores , "structure_only_scores": structure_only_scores , "structure_only_scores_avg": 0 , "scores_avg": 0}

    avg_scores = sum(scores) / len(scores)
    avg_structure_only_scores = sum(structure_only_scores) / len(structure_only_scores)
    return {"scores":scores , "structure_only_scores": structure_only_scores , "structure_only_scores_avg": avg_structure_only_scores , "scores_avg": avg_scores}



