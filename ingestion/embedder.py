"""MedCPT Embedding Engine — asymmetric article/query encoders.

MedCPT uses SEPARATE encoders for documents vs queries, which is critical
for pharma retrieval where a short claim ("Drug X achieved 32% abstinence")
must match against long clinical paragraphs.

- Article Encoder: used during INGESTION to embed reference document chunks
- Query Encoder: used during RETRIEVAL to embed the user's claim

Both produce 768-dim vectors in the same latent space.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)


class MedCPTEmbedder:
    """Dual-encoder wrapper for MedCPT article and query models."""

    def __init__(
        self,
        article_model_name: str = "ncbi/MedCPT-Article-Encoder",
        query_model_name: str = "ncbi/MedCPT-Query-Encoder",
        device: str = "cpu",
        hf_token: Optional[str] = None,
    ):
        self.device = torch.device(device)

        logger.info(f"Loading MedCPT Article Encoder: {article_model_name}")
        self._article_tokenizer = AutoTokenizer.from_pretrained(
            article_model_name, token=hf_token
        )
        self._article_model = AutoModel.from_pretrained(
            article_model_name, token=hf_token
        ).to(self.device).eval()

        logger.info(f"Loading MedCPT Query Encoder: {query_model_name}")
        self._query_tokenizer = AutoTokenizer.from_pretrained(
            query_model_name, token=hf_token
        )
        self._query_model = AutoModel.from_pretrained(
            query_model_name, token=hf_token
        ).to(self.device).eval()

        self.embedding_dim = 768
        logger.info("MedCPT embedders loaded successfully")

    @torch.no_grad()
    def encode_article(self, text: str) -> np.ndarray:
        """Encode a single document/article chunk for INGESTION.

        Args:
            text: The reference document text chunk.

        Returns:
            768-dim numpy array.
        """
        encoded = self._article_tokenizer(
            text,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        ).to(self.device)

        output = self._article_model(**encoded)
        # MedCPT uses [CLS] token embedding
        embedding = output.last_hidden_state[:, 0, :]
        return embedding.cpu().numpy().flatten()

    @torch.no_grad()
    def encode_articles_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode multiple article chunks in batches.

        Args:
            texts: List of text chunks to encode.
            batch_size: Batch size for encoding.

        Returns:
            Array of shape (N, 768).
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = self._article_tokenizer(
                batch,
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(self.device)

            output = self._article_model(**encoded)
            embeddings = output.last_hidden_state[:, 0, :]
            all_embeddings.append(embeddings.cpu().numpy())

        return np.vstack(all_embeddings)

    @torch.no_grad()
    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single claim/query for RETRIEVAL.

        Uses the separate Query Encoder which is trained to project
        short queries into the same space as article embeddings.

        Args:
            query: The claim text to search for.

        Returns:
            768-dim numpy array.
        """
        encoded = self._query_tokenizer(
            query,
            max_length=256,
            padding=True,
            truncation=True,
            return_tensors="pt",
        ).to(self.device)

        output = self._query_model(**encoded)
        embedding = output.last_hidden_state[:, 0, :]
        return embedding.cpu().numpy().flatten()
