from rouge_score import rouge_scorer
import numpy as np

def calculate_rouge_metrics(matching_values):
    """
    Calculate macro and micro ROUGE-L scores for a list of (reference, hypothesis) tuples.

    Args:
        matching_values (list of tuples): List where each tuple contains (reference, hypothesis) strings.

    Returns:
        dict: Dictionary containing the micro ROUGE-L scores for each pair, 
              the macro ROUGE-L score, and the micro-average ROUGE-L score.
    """
    # Initialize ROUGE scorer for LCS (Longest Common Subsequence)
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)

    # Lists to store individual micro scores
    micro_scores = []

    # Calculate micro ROUGE-L score (individual score for each pair)
    for ref, hyp in matching_values:
        scores = scorer.score(ref, hyp)
        rouge_l_fmeasure = scores['rougeL'].fmeasure
        micro_scores.append(rouge_l_fmeasure)

    # Micro-average ROUGE-L score (average of individual scores)
    micro_rouge_l = round(np.mean(micro_scores), 2)

    # Calculate macro ROUGE-L by concatenating all reference and hypothesis texts
    all_ref = " ".join([ref for ref, _ in matching_values])
    all_hyp = " ".join([hyp for _, hyp in matching_values])
    macro_scores = scorer.score(all_ref, all_hyp)
    macro_rouge_l = round(macro_scores['rougeL'].fmeasure, 2)

    # Return the results in a dictionary
    return {
        "micro_scores_per_pair": [round(score, 2) for score in micro_scores],
        "macro_rouge_l": macro_rouge_l,
        "micro_average_rouge_l": micro_rouge_l
    }



from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import numpy as np

def calculate_bleu_metrics(matching_values):
    """
    Calculate BLEU scores for each (reference, hypothesis) pair and the average BLEU score.

    Args:
        matching_values (list of tuples): List where each tuple contains (reference, hypothesis) strings.

    Returns:
        dict: Dictionary containing the BLEU scores for each pair and the average BLEU score.
    """
    # Initialize smoothing function
    smoothie = SmoothingFunction().method4

    # List to store individual BLEU scores
    bleu_scores = []

    # Calculate BLEU score for each pair
    for ref, hyp in matching_values:
        # Tokenize sentences
        reference = [ref.split()]  # reference must be a list of lists for sentence_bleu
        hypothesis = hyp.split()
        # Compute BLEU score
        bleu_score = sentence_bleu(reference, hypothesis, smoothing_function=smoothie)
        bleu_scores.append(bleu_score)

    # Calculate Averaged BLEU (average of individual BLEU scores)
    average_bleu = round(np.mean(bleu_scores), 4)

    # Return the results in a dictionary
    return {
        "bleu_scores_per_pair": [round(score, 4) for score in bleu_scores],
        "average_bleu": average_bleu
    }
