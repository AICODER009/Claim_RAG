#!/usr/bin/env python3
"""BM25 sparse vector generator for Qdrant.

Implements a lightweight BM25 tokenizer that generates sparse vectors
compatible with Qdrant's sparse vector search. No external dependencies
beyond the Qdrant client.

This replaces fastembed's BM25 model when fastembed can't be loaded
(e.g., due to onnxruntime DLL issues on constrained systems).
"""

import hashlib
import math
import re
import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Snowball-style English stemmer (simplified but covers 90% of cases)
# Full Porter stemmer would be ~200 lines; this handles the common suffixes
# that matter for our pharma/medical corpus
STEM_RULES = [
    # Order matters: longest suffix first
    ("ational", "ate"), ("tional", "tion"), ("ization", "ize"),
    ("fulness", "ful"), ("ousness", "ous"), ("iveness", "ive"),
    ("ement", ""), ("ment", ""), ("ness", ""),
    ("ating", "ate"), ("izing", "ize"),
    ("ible", ""), ("able", ""),
    ("tion", ""), ("sion", ""),
    ("ling", "l"), ("ying", "y"),
    ("ing", ""), ("ied", "y"), ("ies", "y"),
    ("ed", ""), ("er", ""), ("ly", ""),
    ("es", ""), ("s", ""),
]


def stem_word(word: str) -> str:
    """Simple English stemmer for BM25 purposes.
    
    freeze → freez, frozen → frozen (special case), washing → wash, etc.
    """
    if len(word) <= 3:
        return word

    # Special irregular forms common in our corpus
    IRREGULARS = {
        "frozen": "freez", "freeze": "freez", "freezing": "freez",
        "warming": "warm", "warmed": "warm",
        "injecting": "inject", "injected": "inject", "injection": "inject",
        "expired": "expir", "expiring": "expir", "expiration": "expir",
        "discarding": "discard", "discarded": "discard",
        "washing": "wash", "washed": "wash",
        "unused": "unus",
    }
    if word in IRREGULARS:
        return IRREGULARS[word]

    for suffix, replacement in STEM_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            return word[:-len(suffix)] + replacement

    return word


# Standard English stopwords
STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "because",
    "but", "and", "or", "if", "while", "that", "this", "what",
    "which", "who", "whom", "these", "those", "it", "its",
    "i", "me", "my", "we", "our", "you", "your", "he", "she",
    "him", "her", "they", "them", "their", "up", "about",
})


def tokenize(text: str) -> List[str]:
    """Tokenize text into stemmed lowercase tokens, removing stopwords."""
    # Split on non-alphanumeric, keep numbers
    tokens = re.findall(r"[a-zA-Z0-9]+(?:\.[0-9]+)?%?", text.lower())
    # Filter stopwords, stem remaining
    return [stem_word(t) for t in tokens if t not in STOPWORDS and len(t) >= 2]


def token_to_index(token: str) -> int:
    """Map a token string to a stable integer index via hashing.
    
    Uses a 32-bit hash to create a sparse vector index.
    The same token always maps to the same index.
    """
    h = hashlib.md5(token.encode()).hexdigest()
    return int(h[:8], 16)  # 32-bit index space


class BM25SparseEncoder:
    """Generates BM25 sparse vectors for Qdrant.
    
    Two-phase usage:
    1. fit(corpus_texts) — compute IDF from the document collection
    2. encode(text) — generate sparse vector for a single text
    
    Or use encode_query(text) for query-time encoding (TF only, no IDF needed
    since Qdrant applies IDF via Modifier.IDF).
    
    BM25 parameters:
    - k1: Term frequency saturation. Higher = more weight to repeated terms.
    - b: Length normalization. 0 = no normalization, 1 = full normalization.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.avg_doc_len: float = 0.0
        self.doc_count: int = 0
        self.doc_freq: Dict[str, int] = {}  # token -> number of documents containing it
        self._fitted = False

    def fit(self, texts: List[str]):
        """Compute corpus statistics (IDF, avg doc length) from all documents."""
        self.doc_count = len(texts)
        total_tokens = 0
        self.doc_freq = {}

        for text in texts:
            tokens = tokenize(text)
            total_tokens += len(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1

        self.avg_doc_len = total_tokens / max(self.doc_count, 1)
        self._fitted = True
        logger.info(
            f"BM25 fitted: {self.doc_count} docs, "
            f"avg_len={self.avg_doc_len:.1f}, "
            f"vocab={len(self.doc_freq)} terms"
        )

    def _idf(self, token: str) -> float:
        """Compute IDF for a token. Higher for rare terms."""
        df = self.doc_freq.get(token, 0)
        if df == 0:
            return 0.0
        # Standard BM25 IDF formula
        return math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)

    def encode_document(self, text: str) -> Tuple[List[int], List[float]]:
        """Generate sparse vector for a document (includes TF + length norm).
        
        When using Qdrant's Modifier.IDF, we only encode TF here
        and let Qdrant handle IDF at search time.
        
        Returns (indices, values) for Qdrant SparseVector.
        """
        tokens = tokenize(text)
        if not tokens:
            return [], []

        doc_len = len(tokens)
        tf_counts = Counter(tokens)

        indices = []
        values = []

        for token, count in tf_counts.items():
            idx = token_to_index(token)
            # BM25 TF component with length normalization
            tf = (count * (self.k1 + 1)) / (
                count + self.k1 * (1 - self.b + self.b * doc_len / max(self.avg_doc_len, 1))
            )
            indices.append(idx)
            values.append(round(tf, 4))

        return indices, values

    def encode_query(self, text: str) -> Tuple[List[int], List[float]]:
        """Generate sparse vector for a query.
        
        For queries, we use simple term presence (weight=1.0) since
        Qdrant's IDF modifier will handle the scoring at search time.
        
        Returns (indices, values) for Qdrant SparseVector.
        """
        tokens = tokenize(text)
        if not tokens:
            return [], []

        # Deduplicate tokens, weight = 1.0 for each unique term
        unique_tokens = set(tokens)
        indices = [token_to_index(t) for t in unique_tokens]
        values = [1.0] * len(indices)

        return indices, values

    def encode_query_with_idf(self, text: str) -> Tuple[List[int], List[float]]:
        """Generate sparse vector with IDF weights baked in.
        
        Use this if NOT using Qdrant's Modifier.IDF.
        Requires fit() to have been called first.
        """
        if not self._fitted:
            raise RuntimeError("Call fit() before encode_query_with_idf()")

        tokens = tokenize(text)
        if not tokens:
            return [], []

        unique_tokens = set(tokens)
        indices = []
        values = []
        for token in unique_tokens:
            idf = self._idf(token)
            if idf > 0:
                indices.append(token_to_index(token))
                values.append(round(idf, 4))

        return indices, values


if __name__ == "__main__":
    # Quick test
    encoder = BM25SparseEncoder()

    # Simulate corpus
    corpus = [
        "Do not freeze VYVGART HYTRULO. Store in refrigerator.",
        "Wash your hands with soap and water before injecting.",
        "Discard any unused portion of the prefilled syringe.",
        "The efficacy of efgartigimod was demonstrated in a pivotal trial.",
    ]
    encoder.fit(corpus)

    # Test query
    query = "Do not freeze VYVGART HYTRULO"
    tokens = tokenize(query)
    print(f"Query: {query}")
    print(f"Tokens: {tokens}")

    indices, values = encoder.encode_query(query)
    print(f"Sparse vector: {len(indices)} non-zero terms")

    indices2, values2 = encoder.encode_query_with_idf(query)
    print(f"With IDF: {list(zip(indices2, values2))}")

    # Show stemming works
    for word in ["freeze", "frozen", "freezing", "warm", "warmed", "warming",
                 "inject", "injected", "injecting", "expired", "expiration"]:
        print(f"  {word:15s} → {stem_word(word)}")
